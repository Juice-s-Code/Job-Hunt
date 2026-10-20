"""Synthetic public-response fixtures, not real applications."""
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import source_jobs as source


def fixture():
    return {"jobs": [{"id": 123, "title": "Fixture Analyst", "absolute_url": "https://example.com/jobs/123", "location": {"name": "Fixture City"}, "content": "<p>SYNTHETIC SOURCE ONLY</p>"}]}


class SourceTests(unittest.TestCase):
    def test_entity_encoded_html_retains_readable_full_body(self):
        data = fixture()
        data['jobs'][0]['content'] = '&lt;p&gt;Full source&lt;/p&gt;&lt;p&gt;No AI assistance&lt;/p&gt;'
        result = source.normalize(data, 'Fixture Employer')[0]
        self.assertIn('Full source', result['source_text'])
        self.assertIn('No AI assistance', result['source_text'])
        self.assertNotIn('<p>', result['source_text'])
        self.assertIsNone(result['no_ai'])  # A parser cannot authorize application work.

    def test_reported_inventory_must_match_response(self):
        data = fixture()
        data['meta'] = {'total': 2}
        with self.assertRaises(source.SourceError):
            source.normalize(data, 'Fixture Employer')
        data['meta']['total'] = 1
        self.assertEqual(len(source.normalize(data, 'Fixture Employer')), 1)

    def test_control_characters_in_upstream_fields_refused(self):
        data = fixture()
        data['jobs'][0]['title'] = 'Fake\u202eTitle'
        with self.assertRaises(source.SourceError):
            source.normalize(data, 'Fixture Employer')

    def test_normalize_preserves_source_and_unknowns(self):
        jobs = source.normalize(fixture(), "Fixture Employer")
        self.assertEqual(jobs[0]["id"], "123")
        self.assertEqual(jobs[0]["employer"], "Fixture Employer")
        self.assertIn("SYNTHETIC SOURCE ONLY", jobs[0]["source_text"])
        for field in ("start_date", "min_years_experience", "country", "role_family", "internship", "no_ai"):
            self.assertIsNone(jobs[0][field])

    def test_bad_envelope_is_not_zero_jobs(self):
        with self.assertRaises(source.SourceError):
            source.normalize({"error": "fixture"}, "Fixture Employer")

    def test_duplicate_upstream_ids_fail(self):
        data = fixture()
        data["jobs"] *= 2
        with self.assertRaises(source.SourceError):
            source.normalize(data, "Fixture Employer")

    def test_bad_id_not_repaired(self):
        data = fixture()
        data["jobs"][0]["id"] = " 123 "
        with self.assertRaises(source.SourceError):
            source.normalize(data, "Fixture Employer")

    def test_board_validation_precedes_network(self):
        with patch.object(source, "fetch_json") as fetch:
            with self.assertRaises(source.SourceError):
                source.collect("../not-a-board", "Fixture Employer")
            fetch.assert_not_called()

    def test_only_verified_api_host_allowed_for_redirect(self):
        handler = source.PublicRedirect()
        with self.assertRaises(source.SourceError):
            handler.redirect_request(None, None, 302, "", {}, "http://127.0.0.1/private")

    def test_collect_uses_real_contract_and_returns_counted_list(self):
        with patch.object(source, "fetch_json", return_value=fixture()) as fetch:
            jobs = source.collect("fixtureboard", "Fixture Employer")
        self.assertEqual(len(jobs), 1)
        self.assertEqual(fetch.call_args.args[0], "https://boards-api.greenhouse.io/v1/boards/fixtureboard/jobs?content=true")

    def test_output_never_overwrites(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "source.json"
            p.write_bytes(b"PRESERVE")
            with self.assertRaises(source.SourceError):
                source.save_jobs(p, [])
            self.assertEqual(p.read_bytes(), b"PRESERVE")

    def test_no_candidate_or_application_status_in_output(self):
        text = json.dumps(source.normalize(fixture(), "Fixture Employer"))
        self.assertNotIn("applied", text)
        self.assertNotIn("candidate", text)


if __name__ == "__main__":
    unittest.main()
