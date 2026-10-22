"""Pure streak rules. Does not access cards, scheduling, or Anki's database."""
import math

DEFAULTS = {
    'enabled': True, 'collection': 'pulse', 'window_seconds': 30,
    'count_hard': True, 'volume': 50, 'popup_seconds': 1.8,
    'show_countdown': True, 'position': 'bottom_center',
    'timing_mode': 'accelerating', 'shrink_percent': 20,
    'minimum_window_percent': 25,
}


def settings(raw=None):
    raw = raw if isinstance(raw, dict) else {}
    result = DEFAULTS.copy()
    for key in ('enabled', 'count_hard', 'show_countdown'):
        if isinstance(raw.get(key), bool):
            result[key] = raw[key]
    for key, lower, upper in (('window_seconds', 1, 600), ('volume', 0, 100), ('popup_seconds', .5, 8), ('shrink_percent', 1, 75), ('minimum_window_percent', 5, 100)):
        try:
            value = float(raw.get(key, result[key]))
            if math.isfinite(value):
                result[key] = max(lower, min(upper, value))
        except (ValueError, TypeError):
            pass
    if isinstance(raw.get('collection'), str):
        result['collection'] = raw['collection']
    if raw.get('position') in ('bottom_center', 'top_right'):
        result['position'] = raw['position']
    if raw.get('timing_mode') in ('fixed', 'accelerating'):
        result['timing_mode'] = raw['timing_mode']
    return result


def window_for_count(count, base, shrink_percent=0, minimum_percent=25):
    """Configurable rolling deadlines for successive review ratings.

    Count 1 creates the full window for answer 2. Count 5 creates the
    window for the first fifth-stage repeat. Later repeats keep shrinking to a floor.
    """
    floor = base * minimum_percent / 100.
    return max(floor, base * (1 - shrink_percent / 100.) ** max(0, min(count - 1, 10000)))


class Streak:
    def __init__(self):
        self.reset()

    def reset(self):
        self.count = 0
        self.deadline = None
        self.active_window = 0.

    def expire(self, now):
        if self.deadline is not None and now >= self.deadline:
            self.reset()
            return True
        return False

    def answer(self, ease, now, window, count_hard=True, shrink_percent=0, minimum_percent=25):
        self.expire(now)
        correct = ease in ((2, 3, 4) if count_hard else (3, 4))
        if not correct:
            self.reset()
            return 0
        self.count += 1
        self.active_window = window_for_count(self.count, window, shrink_percent, minimum_percent)
        self.deadline = now + self.active_window
        return min(self.count, 5)

    def remaining(self, now):
        return max(0., self.deadline - now) if self.deadline is not None else 0.
