import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('core', Path(__file__).resolve().parents[1] / 'addon' / 'core.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


class Rules(unittest.TestCase):
    def test_each_correct_restarts_window(self):
        s=core.Streak()
        self.assertEqual(s.answer(3, 100, 30),1)
        self.assertEqual(s.answer(3, 129, 30),2)
        self.assertEqual(s.answer(4, 158, 30),3)
        self.assertEqual(s.deadline,188)

    def test_exact_deadline_starts_new_streak(self):
        s=core.Streak(); s.answer(3, 100, 30)
        self.assertEqual(s.answer(3, 130, 30),1)
        self.assertEqual(s.count,1)

    def test_again_resets_immediately(self):
        s=core.Streak(); s.answer(3, 0, 30); s.answer(4, 1, 30)
        self.assertEqual(s.answer(1, 2, 30),0)
        self.assertIsNone(s.deadline)
        self.assertEqual(s.answer(3, 3, 30),1)

    def test_hard_setting(self):
        s=core.Streak()
        self.assertEqual(s.answer(2, 0, 30),1)
        self.assertEqual(s.answer(2, 1, 30, False),0)
        self.assertEqual(s.answer(3, 2, 30, False),1)

    def test_fifth_sound_repeats_but_count_grows(self):
        s=core.Streak()
        self.assertEqual([s.answer(3,i,30) for i in range(8)],[1,2,3,4,5,5,5,5])
        self.assertEqual(s.count,8)

    def test_expiry_without_answer_and_long_sleep(self):
        s=core.Streak(); s.answer(3,10,30)
        self.assertEqual(s.remaining(20),20)
        self.assertFalse(s.expire(39.999))
        self.assertTrue(s.expire(40))
        self.assertEqual(s.remaining(10000),0)
        self.assertEqual(s.answer(4,10000,30),1)

    def test_invalid_ratings_and_reset(self):
        s=core.Streak(); s.answer(3,10,30)
        self.assertEqual(s.answer(99,11,30),0)
        s.answer(4,12,30);s.reset()
        self.assertEqual((s.count,s.deadline),(0,None))

    def test_malformed_config(self):
        self.assertEqual(core.settings(None),core.DEFAULTS)
        c=core.settings({'volume':999,'window_seconds':float('nan'),'enabled':'false','popup_seconds':-1,'position':'bad'})
        self.assertEqual(c['volume'],100)
        self.assertEqual(c['window_seconds'],30)
        self.assertTrue(c['enabled'])
        self.assertEqual(c['popup_seconds'],.5)
        self.assertEqual(c['position'],'bottom_center')

    def test_accelerates_through_ace_and_repeats(self):
        s=core.Streak()
        expected=[10,8,6.4,5.12,4.096,3.2768,2.62144,2.5,2.5]
        for i,window in enumerate(expected):
            kill=s.answer(3,i,10,True,20,25)
            self.assertEqual(kill,min(i+1,5))
            self.assertAlmostEqual(s.active_window,window)
            self.assertAlmostEqual(s.deadline,i+window)

    def test_shorter_deadline_really_expires(self):
        s=core.Streak();s.answer(3,0,10,True,20,25)
        s.answer(3,1,10,True,20,25)
        self.assertEqual(s.deadline,9)
        # Inside the former 10-second window, but exactly at the new deadline.
        self.assertEqual(s.answer(3,9,10,True,20,25),1)
        self.assertEqual(s.active_window,10)

    def test_after_ace_reset_recovers_full_window(self):
        s=core.Streak()
        for i in range(12):s.answer(3,i,10,True,20,25)
        self.assertEqual(s.active_window,2.5)
        s.answer(1,12,10,True,20,25)
        self.assertEqual(s.active_window,0)
        self.assertEqual(s.answer(4,13,10,True,20,25),1)
        self.assertEqual(s.active_window,10)

    def test_window_scales_and_has_a_floor(self):
        self.assertAlmostEqual(core.window_for_count(3,30,20,25),19.2)
        self.assertEqual(core.window_for_count(100000,30,20,25),7.5)
        self.assertEqual(core.window_for_count(100,10,0,25),10)
        self.assertEqual(core.window_for_count(2,10,20,100),10)

    def test_existing_settings_migrate_without_losing_preferences(self):
        c=core.settings({'collection':'prime','window_seconds':10,'volume':37})
        self.assertEqual((c['collection'],c['window_seconds'],c['volume']),('prime',10,37))
        self.assertEqual((c['timing_mode'],c['shrink_percent'],c['minimum_window_percent']),('accelerating',20,25))
        fixed=core.settings(dict(c,timing_mode='fixed'))
        self.assertEqual(fixed['timing_mode'],'fixed')


if __name__=='__main__':unittest.main(verbosity=2)
