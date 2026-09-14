"""Publication gate tests: no network calls or website writes."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('publish_missing_sundays_v1.py')
MANIFEST = SCRIPT.parents[1] / 'social/published_sundays.json'
GATE = SCRIPT.read_text(encoding='utf-8').split('# Download the exact published media')[0]


class PublicationGateTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(MANIFEST.read_text(encoding='utf-8'))

    def validate(self, data):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'publications.json'
            source.write_text(json.dumps(data), encoding='utf-8')
            previous = sys.argv[:]
            try:
                sys.argv = [str(SCRIPT), str(Path(folder) / 'unused-site'), str(source)]
                exec(compile(GATE, str(SCRIPT), 'exec'), {'__file__': str(SCRIPT)})
            finally:
                sys.argv = previous
            self.assertFalse((Path(folder) / 'unused-site').exists())

    def test_confirmed_publications_are_accepted(self):
        self.validate(self.data)

    def test_pending_posts_are_rejected(self):
        self.data['posts'][-1]['status'] = 'PENDING'
        with self.assertRaisesRegex(SystemExit, 'confirmed published'):
            self.validate(self.data)

    def test_reels_are_not_sunday_image_entries(self):
        self.data['posts'][-1]['type'] = 'REEL'
        with self.assertRaisesRegex(SystemExit, 'confirmed published'):
            self.validate(self.data)

    def test_future_timestamp_is_rejected(self):
        self.data['posts'][-1]['publishedAt'] = '2099-01-01T19:00:00+01:00'
        with self.assertRaisesRegex(SystemExit, 'Future'):
            self.validate(self.data)

    def test_duplicate_numbers_are_rejected(self):
        self.data['posts'].append(copy.deepcopy(self.data['posts'][-1]))
        with self.assertRaisesRegex(SystemExit, 'duplicate'):
            self.validate(self.data)

    def test_wrong_sunday_date_is_rejected(self):
        self.data['posts'][-1]['date'] = '2026-09-14'
        with self.assertRaisesRegex(SystemExit, 'date does not match'):
            self.validate(self.data)

    def test_missing_instagram_evidence_is_rejected(self):
        self.data['posts'][-1]['instagram'] = 'https://www.instagram.com/oolita.es/'
        with self.assertRaisesRegex(SystemExit, 'publication evidence'):
            self.validate(self.data)


if __name__ == '__main__':
    unittest.main()
