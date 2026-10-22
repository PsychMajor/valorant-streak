"""Exercise actual Anki 26.8.1 hooks and bundled Qt without opening any collection."""
import sys, time
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import aqt
from aqt import gui_hooks
from aqt.qt import QApplication, QMainWindow, QMenu, QLabel, QCheckBox, QComboBox, QSpinBox, QDialogButtonBox, QUrl, QPixmap

app=QApplication([])
class Manager:
    def __init__(self):self.saved=None
    def getConfig(self, module):return {'volume':0}
    def setConfigAction(self,module,action):self.action=action
    def writeConfig(self,module,config):self.saved=config

window=QMainWindow();window.resize(1000,760);window.state='review'
window.form=SimpleNamespace(menuTools=QMenu('Tools',window))
window.addonManager=Manager()
window.setCentralWidget(QLabel('Anki review preview — test window, no collection loaded'))
aqt.mw=window
import addon
window.show();addon.initialize();app.processEvents()
c=addon.controller
assert len(c.packs)==6
for pack in c.packs:
    assert len(pack['sounds'])==5
    assert not QPixmap(str(addon.ROOT/pack['banner'])).isNull(), pack['name']
for i in range(6):gui_hooks.reviewer_did_answer_card(None,None,3)
app.processEvents()
assert c.streak.count==6 and c.overlay.title.text()=='FIVE ALIVE'
assert abs(c.streak.active_window-30*.8**5)<.0001
assert c.overlay.isVisible()
window.resize(1100,800);app.processEvents()
assert c.overlay.x()==(window.width()-c.overlay.width())//2
c.popup_until=0;c.tick()
assert not c.overlay.banner.isVisible() and c.overlay.height()==58
assert c.overlay.progress.value()>950
assert 'repeat stage 5' in c.overlay.detail.text()
gui_hooks.reviewer_did_answer_card(None,None,1)
assert c.streak.count==0 and not c.overlay.isVisible()
gui_hooks.reviewer_did_answer_card(None,None,4)
c.streak.deadline=time.monotonic()-1;c.tick()
assert c.streak.count==0 and not c.timer.isActive()
gui_hooks.reviewer_did_answer_card(None,None,3)
gui_hooks.state_did_undo(None)
assert c.streak.count==0
gui_hooks.reviewer_did_answer_card(None,None,3)
gui_hooks.reviewer_will_end()
assert c.streak.count==0
c.config['enabled']=False;c.answered(None,None,3)
assert c.streak.count==0
c.config['enabled']=True
c.open_settings();app.processEvents()
dialog=c.dialog
assert dialog and dialog.isVisible()
collection=dialog.findChildren(QComboBox)[0]
assert collection.count()==6
collection.setCurrentIndex(collection.findData("bloom"))
dialog.findChildren(QSpinBox)[0].setValue(45)
assert '45.0s → 36.0s → 28.8s → 23.0s' in dialog.findChild(QLabel,'timing_schedule').text()
mode=dialog.findChild(QComboBox,'timing_mode')
mode.setCurrentIndex(mode.findData('fixed'))
assert not dialog.findChild(QSpinBox,'shrink_percent').isEnabled()
assert '45.0s → 45.0s → 45.0s → 45.0s' in dialog.findChild(QLabel,'timing_schedule').text()
buttons=dialog.findChild(QDialogButtonBox)
buttons.button(QDialogButtonBox.StandardButton.Save).click();app.processEvents()
assert c.config['collection']=="bloom" and c.config['window_seconds']==45
assert window.addonManager.saved['collection']=="bloom"
assert c.config['timing_mode']=='fixed'
assert c.dialog is None
for i in range(9):c.answered(None,None,3)
assert c.streak.active_window==45
c.reset()
# Decode every bundled sound using the actual Anki Qt multimedia backend.
c.ensure_audio();c.audio_output.setVolume(0)
for pack in c.packs:
    for sound in pack['sounds']:
        c.player.setSource(QUrl.fromLocalFile(str(addon.ROOT/sound['file'])))
        c.player.play()
        until=time.monotonic()+2
        while time.monotonic()<until and c.player.duration()==0:
            app.processEvents();time.sleep(.01)
        assert c.player.duration()>0, (sound['file'], c.player.errorString())
        assert not c.audio_warned, c.player.errorString()
        c.player.stop()
print('PASS: Anki hooks, accelerating ace repeats, active-window progress, fixed-mode toggle/save, resize, countdown, Again, expiry, undo, review exit, disabling, WAV decoding.')
c.config=addon.settings()
c.open_settings();app.processEvents()
c.dialog.grab().save(str(Path(__file__).resolve().parents[2] / 'streak-lab-settings.png'))
c.dialog.close();c.reset();window.close();app.processEvents()
