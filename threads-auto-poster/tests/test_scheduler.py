import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from threads_poster.scheduler import due_slot, slot_key

JST = ZoneInfo("Asia/Tokyo")
SLOTS = ["07:00", "12:15", "21:00"]


def at(hour, minute):
    return datetime(2026, 10, 21, hour, minute, tzinfo=JST)


class DueSlotTest(unittest.TestCase):
    def test_inside_window(self):
        self.assertEqual(due_slot(at(7, 0), SLOTS, 60), "07:00")
        self.assertEqual(due_slot(at(12, 50), SLOTS, 60), "12:15")
        self.assertEqual(due_slot(at(21, 59), SLOTS, 60), "21:00")

    def test_outside_window(self):
        self.assertIsNone(due_slot(at(6, 59), SLOTS, 60))
        self.assertIsNone(due_slot(at(8, 0), SLOTS, 60))
        self.assertIsNone(due_slot(at(23, 0), SLOTS, 60))

    def test_overlapping_windows_pick_latest(self):
        self.assertEqual(due_slot(at(12, 20), ["12:00", "12:15"], 60), "12:15")

    def test_slot_key(self):
        self.assertEqual(slot_key(at(7, 5), "07:00"), "2026-10-21 07:00")


if __name__ == "__main__":
    unittest.main()
