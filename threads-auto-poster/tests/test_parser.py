import unittest

from threads_poster.parser import MAX_CHARS, parse_inbox


class ParseInboxTest(unittest.TestCase):
    def test_splits_blocks_and_reads_meta(self):
        raw = """---
ジャンル: 副業
アカウント: sub
月5万円を達成するまでにやったこと

1. 毎朝30分
---
genre：朝活
朝活で気づいたこと
---
"""
        drafts, errors = parse_inbox(raw)
        self.assertEqual(errors, [])
        self.assertEqual(len(drafts), 2)
        self.assertEqual(drafts[0].genre, "副業")
        self.assertEqual(drafts[0].account, "sub")
        self.assertEqual(drafts[0].text, "月5万円を達成するまでにやったこと\n\n1. 毎朝30分")
        self.assertEqual(drafts[1].genre, "朝活")
        self.assertIsNone(drafts[1].account)

    def test_meta_only_at_top(self):
        drafts, _ = parse_inbox("本文です\nジャンル: これは本文")
        self.assertIsNone(drafts[0].genre)
        self.assertEqual(drafts[0].text, "本文です\nジャンル: これは本文")

    def test_errors_for_empty_and_too_long(self):
        raw = f"ジャンル: 空\n---\n{'あ' * (MAX_CHARS + 1)}\n---\nOK"
        drafts, errors = parse_inbox(raw)
        self.assertEqual([d.text for d in drafts], ["OK"])
        self.assertEqual([e.index for e in errors], [1, 2])

    def test_empty_input(self):
        self.assertEqual(parse_inbox("\n---\n\n"), ([], []))


if __name__ == "__main__":
    unittest.main()
