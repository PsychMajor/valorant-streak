"""Valorant Streak: local, configurable reward overlay for Anki desktop (Qt 6)."""
from __future__ import annotations

import json
from pathlib import Path
from time import monotonic

from aqt import gui_hooks, mw
from aqt.qt import (
    QAction, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QEvent, QFormLayout, QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel,
    QProgressBar, QPropertyAnimation, QPushButton, QSlider, QSpinBox, Qt,
    QTimer, QUrl, QVBoxLayout, QPixmap,
)
from aqt.utils import tooltip

from .core import Streak, settings, window_for_count

ROOT = Path(__file__).resolve().parent
TITLES = ('FIRST BLOOD', 'DOUBLE KILL', 'TRIPLE KILL', 'QUADRA KILL', 'ACE')
MODULE = __name__


class RewardOverlay(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName('valorantReward')
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(4)
        self.banner = QLabel(self)
        self.banner.setFixedHeight(82)
        self.banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title = QLabel(self)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet('font-size: 21px; font-weight: 800; color: #eef3f6;')
        self.detail = QLabel(self)
        self.detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail.setStyleSheet('font-size: 11px; color: #c2cdd5;')
        self.progress = QProgressBar(self)
        self.progress.setRange(0, 1000)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(4)
        for widget in (self.banner, self.title, self.detail, self.progress):
            layout.addWidget(widget)
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.animation = QPropertyAnimation(self.effect, b'opacity', self)
        self.animation.setDuration(180)
        self.hide()

    def theme(self, pack):
        color = pack['color']
        self.setStyleSheet(
            'QFrame#valorantReward {background: #111c25; border: 1px solid '+color+'; border-radius: 10px;}'
            'QLabel {background: transparent; border: none;}'
            'QProgressBar {background: #34434e; border: none; border-radius: 2px;}'
            'QProgressBar::chunk {background: '+color+'; border-radius: 2px;}'
        )
        pixmap = QPixmap(str(ROOT / pack['banner']))
        self.banner.setPixmap(pixmap.scaled(140, 82, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def place(self, config):
        self.placement_config = config
        parent = self.parentWidget()
        width = min(280, max(150, parent.width() - 24))
        self.setFixedWidth(width)
        height = 180 if self.banner.isVisible() else 58
        self.setFixedHeight(height)
        if config['position'] == 'top_right':
            x, y = parent.width() - width - 20, 85
        else:
            x, y = (parent.width() - width) // 2, parent.height() - height - 105
        self.move(max(8, x), max(35, y))
        self.raise_()

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.Resize, QEvent.Type.Show) and self.isVisible():
            self.place(self.placement_config)
        return False

    def reward(self, pack, count, config):
        self.theme(pack)
        self.banner.show()
        self.title.show()
        self.title.setText(TITLES[min(count, 5) - 1])
        self.progress.setValue(1000)
        self.detail.setText(f'{count} correct in a row · {pack["name"]}')
        self.show()
        self.place(config)
        self.animation.stop()
        self.animation.setStartValue(.2)
        self.animation.setEndValue(1.)
        self.animation.start()

    def compact(self, config):
        self.banner.hide()
        self.title.hide()
        self.place(config)


class Controller:
    def __init__(self, window):
        self.mw = window
        self.config = settings(window.addonManager.getConfig(MODULE))
        self.packs = json.loads((ROOT / 'catalog.json').read_text())['packs']
        self.streak = Streak()
        self.overlay = RewardOverlay(window)
        self.timer = QTimer(window)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.tick)
        self.popup_until = 0.
        self.dialog = None
        self.player = self.audio_output = None
        self.audio_warned = False
        window.installEventFilter(self.overlay)
        self.action = QAction('Valorant Streak…', window)
        self.action.triggered.connect(self.open_settings)
        window.form.menuTools.addAction(self.action)
        window.addonManager.setConfigAction(MODULE, self.open_settings)
        gui_hooks.reviewer_did_answer_card.append(self.answered)
        gui_hooks.reviewer_will_end.append(self.reset)
        gui_hooks.profile_will_close.append(self.profile_close)
        gui_hooks.state_did_undo.append(self.undo)

    def pack(self, pack_id=None):
        wanted = pack_id or self.config['collection']
        return next((p for p in self.packs if p['id'] == wanted), self.packs[0])

    def ensure_audio(self):
        if self.player is None:
            from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
            self.player = QMediaPlayer(self.mw)
            self.audio_output = QAudioOutput(self.mw)
            self.player.setAudioOutput(self.audio_output)
            self.player.errorOccurred.connect(self.audio_error)

    def audio_error(self, *_):
        if not self.audio_warned:
            self.audio_warned = True
            tooltip('Valorant Streak: sound could not play. Try another collection in Tools → Valorant Streak.', parent=self.mw)

    def play(self, pack, kill, volume=None):
        level = self.config['volume'] if volume is None else volume
        if level <= 0:
            if self.player:
                self.player.stop()
            return
        try:
            self.ensure_audio()
            self.player.stop()
            self.audio_output.setVolume(level / 100.)
            self.player.setSource(QUrl.fromLocalFile(str(ROOT / pack['sounds'][kill-1]['file'])))
            self.player.play()
        except (ImportError, RuntimeError):
            self.audio_error()

    def answered(self, reviewer, card, ease):
        if not self.config['enabled']:
            return
        now = monotonic()
        shrink = self.config['shrink_percent'] if self.config['timing_mode'] == 'accelerating' else 0
        kill = self.streak.answer(ease, now, self.config['window_seconds'], self.config['count_hard'], shrink, self.config['minimum_window_percent'])
        if not kill:
            self.reset()
            return
        self.popup_until = now + self.config['popup_seconds']
        self.overlay.reward(self.pack(), self.streak.count, self.config)
        self.play(self.pack(), kill)
        self.timer.start()

    def tick(self):
        now = monotonic()
        if self.mw.state != 'review' or not self.streak.count or self.streak.expire(now):
            self.reset()
            return
        remaining = self.streak.remaining(now)
        self.overlay.progress.setValue(round(remaining / self.streak.active_window * 1000))
        if now >= self.popup_until:
            if self.config['show_countdown']:
                self.overlay.compact(self.config)
                target = 'repeat ACE' if self.streak.count >= 5 else f'reach kill {self.streak.count + 1}'
                self.overlay.detail.setText(f'{self.streak.count} streak · {remaining:.1f}s to {target}')
            else:
                self.overlay.hide()

    def reset(self):
        self.streak.reset()
        self.timer.stop()
        self.overlay.animation.stop()
        self.overlay.hide()
        if self.player:
            self.player.stop()

    def undo(self, changes):
        self.reset()

    def profile_close(self):
        self.reset()
        if self.dialog:
            self.dialog.close()

    def open_settings(self):
        if self.dialog:
            self.dialog.raise_()
            self.dialog.activateWindow()
            return
        self.reset()
        dialog = QDialog(self.mw)
        self.dialog = dialog
        dialog.setWindowTitle('Valorant Streak')
        dialog.setMinimumWidth(440)
        layout = QVBoxLayout(dialog)
        title = QLabel('Make every right answer count.', dialog)
        title.setStyleSheet('font-size: 20px; font-weight: 700; margin-bottom: 8px;')
        layout.addWidget(title)
        description = QLabel('Keep answering before the timer expires to build your streak.\nAccelerating mode tightens the window, even after an ace.', dialog)
        layout.addWidget(description)
        form = QFormLayout()
        enabled = QCheckBox('Enable sounds and streak banners', dialog)
        enabled.setChecked(self.config['enabled'])
        form.addRow(enabled)
        collection = QComboBox(dialog)
        for pack in self.packs:
            collection.addItem(pack['name'], pack['id'])
        collection.setCurrentIndex(max(0, collection.findData(self.pack()['id'])))
        form.addRow('Sound collection', collection)
        mode = QComboBox(dialog)
        mode.setObjectName('timing_mode')
        mode.addItem('Accelerating — custom study pacing', 'accelerating')
        mode.addItem('Fixed window — original behavior', 'fixed')
        mode.setCurrentIndex(max(0, mode.findData(self.config['timing_mode'])))
        form.addRow('Timing', mode)
        seconds = QSpinBox(dialog)
        seconds.setRange(1, 600)
        seconds.setValue(round(self.config['window_seconds']))
        seconds.setSuffix(' seconds')
        form.addRow('Starting time window', seconds)
        shrink = QSpinBox(dialog)
        shrink.setObjectName('shrink_percent')
        shrink.setRange(1, 75)
        shrink.setValue(round(self.config['shrink_percent']))
        shrink.setSuffix('% shorter')
        form.addRow('After each correct answer', shrink)
        minimum = QSpinBox(dialog)
        minimum.setObjectName('minimum_window_percent')
        minimum.setRange(5, 100)
        minimum.setValue(round(self.config['minimum_window_percent']))
        minimum.setSuffix('% of starting time')
        form.addRow('Shortest allowed window', minimum)
        schedule = QLabel(dialog)
        schedule.setObjectName('timing_schedule')
        schedule.setWordWrap(True)
        schedule.setStyleSheet('font-size: 11px; color: #87939c;')
        form.addRow(schedule)

        def update_schedule():
            accelerating = mode.currentData() == 'accelerating'
            shrink.setEnabled(accelerating)
            minimum.setEnabled(accelerating)
            rate = shrink.value() if accelerating else 0
            windows = [window_for_count(i, seconds.value(), rate, minimum.value()) for i in range(1, 8)]
            before = ' → '.join(f'{value:.1f}s' for value in windows[:4])
            after = ' → '.join(f'{value:.1f}s' for value in windows[4:])
            floor = seconds.value() * minimum.value() / 100 if accelerating else seconds.value()
            schedule.setText(f'To kills 2 / 3 / 4 / 5: {before}\nAfter ace, for repeats: {after}… (floor {floor:.1f}s)')

        mode.currentIndexChanged.connect(update_schedule)
        for control in (seconds, shrink, minimum):
            control.valueChanged.connect(update_schedule)
        update_schedule()
        hard = QCheckBox('Hard also counts as correct', dialog)
        hard.setChecked(self.config['count_hard'])
        form.addRow(hard)
        volume = QSlider(Qt.Orientation.Horizontal, dialog)
        volume.setRange(0, 100)
        volume.setValue(round(self.config['volume']))
        volume_label = QLabel(f'{volume.value()}%', dialog)
        volume.valueChanged.connect(lambda value: volume_label.setText(f'{value}%'))
        volume_row = QHBoxLayout()
        volume_row.addWidget(volume)
        volume_row.addWidget(volume_label)
        form.addRow('Effect volume', volume_row)
        popup = QDoubleSpinBox(dialog)
        popup.setRange(.5, 8.)
        popup.setSingleStep(.1)
        popup.setValue(self.config['popup_seconds'])
        popup.setSuffix(' seconds')
        form.addRow('Banner duration', popup)
        countdown = QCheckBox('Show a small countdown between answers', dialog)
        countdown.setChecked(self.config['show_countdown'])
        form.addRow(countdown)
        position = QComboBox(dialog)
        position.addItem('Bottom center', 'bottom_center')
        position.addItem('Top right', 'top_right')
        position.setCurrentIndex(max(0, position.findData(self.config['position'])))
        form.addRow('Banner position', position)
        layout.addLayout(form)
        preview = QLabel(dialog)
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview.setFixedHeight(90)
        preview_title = QLabel('Preview a kill sound', dialog)
        preview_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(preview)
        layout.addWidget(preview_title)

        def update_preview():
            pack = self.pack(collection.currentData())
            preview.setPixmap(QPixmap(str(ROOT / pack['banner'])).scaled(145, 86, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            preview_title.setText(pack['name'] + ' · preview a kill sound')
            if self.player:
                self.player.stop()

        def audition(kill):
            pack = self.pack(collection.currentData())
            preview_title.setText(f'{TITLES[kill-1]} · {pack["name"]}')
            self.play(pack, kill, volume.value())

        collection.currentIndexChanged.connect(update_preview)
        update_preview()
        row = QHBoxLayout()
        for kill in range(1, 6):
            button = QPushButton(f'▶ {kill}', dialog)
            button.setAutoDefault(False)
            button.clicked.connect(lambda checked=False, k=kill: audition(k))
            row.addWidget(button)
        layout.addLayout(row)
        note = QLabel('The fifth sound repeats at 5+. Expiry or Again resets to kill 1.\nAccelerating timing is a study adaptation, not verified game timing.\nAudio & artwork © Riot Games · unofficial personal add-on.', dialog)
        note.setStyleSheet('font-size: 11px; color: #87939c; margin-top: 8px;')
        layout.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel, parent=dialog)
        layout.addWidget(buttons)

        def save():
            self.config = settings({
                'enabled': enabled.isChecked(), 'collection': collection.currentData(),
                'window_seconds': seconds.value(), 'count_hard': hard.isChecked(),
                'volume': volume.value(), 'popup_seconds': popup.value(),
                'show_countdown': countdown.isChecked(), 'position': position.currentData(),
                'timing_mode': mode.currentData(), 'shrink_percent': shrink.value(),
                'minimum_window_percent': minimum.value(),
            })
            self.mw.addonManager.writeConfig(MODULE, self.config)
            dialog.accept()

        def closed(result):
            self.reset()
            self.dialog = None
            dialog.deleteLater()

        buttons.accepted.connect(save)
        buttons.rejected.connect(dialog.reject)
        dialog.finished.connect(closed)
        dialog.setWindowModality(Qt.WindowModality.WindowModal)
        dialog.show()


controller = None


def initialize():
    global controller
    if controller is None:
        controller = Controller(mw)


gui_hooks.main_window_did_init.append(initialize)
