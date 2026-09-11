import copy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest
from urllib.parse import parse_qs, urlparse
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import refresh_profile as profile


NOW = datetime(2026, 9, 12, 12, tzinfo=timezone.utc)
ACCOUNT = {"login": profile.LOGIN, "created_at": "2023-10-05T17:30:47Z"}


def repository(name="project", **changes):
    result = {
        "name": name,
        "owner": {"login": profile.LOGIN},
        "private": False,
        "fork": False,
        "archived": False,
        "language": "Python",
        "pushed_at": "2026-09-12T11:00:00Z",
    }
    result.update(changes)
    return result


class SnapshotTests(unittest.TestCase):
    def test_rejects_private_fork_foreign_and_unclear_visibility(self):
        missing_flag = repository("unclear")
        del missing_flag["private"]
        missing_fork = repository("unknown-origin")
        del missing_fork["fork"]
        repos = [
            repository(), repository("secret", private=True),
            repository("fork", fork=True),
            repository("someone-elses", owner={"login": "other"}),
            repository("internal", visibility="internal"),
            missing_flag, missing_fork,
        ]
        result = profile.build_snapshot(ACCOUNT, repos, NOW)
        self.assertEqual(result["metrics"]["original_public_repositories"], 1)
        self.assertEqual([repo["name"] for repo in result["recent_repositories"]], ["project"])
        self.assertEqual(result["primary_languages"], [{"name": "Python", "repositories": 1}])

    def test_push_counts_boundaries_future_dates_and_profile_exclusion(self):
        repos = [
            repository("exactly-30-days", pushed_at=(NOW - timedelta(days=30)).isoformat()),
            repository("too-old", pushed_at=(NOW - timedelta(days=30, seconds=1)).isoformat()),
            repository("future", pushed_at=(NOW + timedelta(seconds=1)).isoformat()),
            repository("bad-date", pushed_at="not a timestamp"),
            repository("no-timezone", pushed_at="2026-09-12T01:00:00"),
            repository(profile.LOGIN),
            repository("archived", archived=True),
        ]
        result = profile.build_snapshot(ACCOUNT, repos, NOW)
        self.assertEqual(result["metrics"]["original_public_repositories"], 7)
        self.assertEqual(result["metrics"]["repositories_pushed_last_30_days"], 2)
        self.assertEqual([repo["name"] for repo in result["recent_repositories"]], ["exactly-30-days", "too-old"])

    def test_primary_languages_count_repositories_and_recent_list_is_latest_four(self):
        repos = [repository(f"repo-{i}", pushed_at=(NOW - timedelta(days=i)).isoformat()) for i in range(6)]
        repos.extend([repository("no-language", language=None, pushed_at=None), repository("typescript", language="TypeScript", pushed_at=None)])
        result = profile.build_snapshot(ACCOUNT, repos, NOW)
        self.assertEqual(result["metrics"]["primary_languages"], 2)
        self.assertEqual(result["primary_languages"], [{"name": "Python", "repositories": 6}, {"name": "TypeScript", "repositories": 1}])
        self.assertEqual([repo["name"] for repo in result["recent_repositories"]], [f"repo-{i}" for i in range(4)])

    def test_unsafe_metadata_cannot_inject_svg_markdown_or_urls(self):
        name = 'hello](https://example.org) | <script>\nnext'
        language = 'X & <script>"\x01 | [link]'
        result = profile.build_snapshot(ACCOUNT, [repository(name, language=language, html_url="javascript:alert(1)")], NOW)
        svg = profile.render_svg(result)
        ET.fromstring(svg)
        self.assertNotIn("<script>", svg)
        self.assertNotIn("\x01", svg)
        mobile = profile.render_mobile_svg(result)
        ET.fromstring(mobile)
        self.assertNotIn("<script>", mobile)
        self.assertNotIn("\x01", mobile)
        activity = profile.render_activity(result)
        self.assertNotIn("<script>", activity)
        self.assertNotIn("](https://example.org)", activity)
        self.assertNotIn("javascript:", activity)
        self.assertIn("&#124;", activity)
        self.assertTrue(result["recent_repositories"][0]["url"].startswith("https://github.com/iamsrishanth/"))
        self.assertNotIn(" ", result["recent_repositories"][0]["url"])

    def test_foreign_account_and_unaware_clock_are_rejected(self):
        with self.assertRaises(ValueError):
            profile.build_snapshot({**ACCOUNT, "login": "other"}, [], NOW)
        with self.assertRaises(ValueError):
            profile.build_snapshot(ACCOUNT, [], NOW.replace(tzinfo=None))

    def test_empty_snapshot_is_valid_svg(self):
        result = profile.build_snapshot(ACCOUNT, [], NOW)
        ET.fromstring(profile.render_svg(result))
        ET.fromstring(profile.render_mobile_svg(result))
        self.assertEqual(result["metrics"]["primary_languages"], 0)
        self.assertIn("No recent public projects", profile.render_activity(result))

    def test_case_insensitive_owner_and_duplicate_repositories(self):
        first = repository(owner={"login": profile.LOGIN.upper()})
        result = profile.build_snapshot(ACCOUNT, [first, copy.deepcopy(first)], NOW)
        self.assertEqual(result["metrics"]["original_public_repositories"], 1)


class ReadmeTests(unittest.TestCase):
    def test_markers_preserve_surroundings_and_replacement_is_idempotent(self):
        original = f"# My profile\n\n{profile.START}\nold generated content\n{profile.END}\n\nHandwritten footer.\n"
        updated = profile.replace_activity(original, "new activity")
        self.assertEqual(updated, profile.replace_activity(updated, "new activity"))
        self.assertTrue(updated.startswith("# My profile\n\n" + profile.START))
        self.assertTrue(updated.endswith(profile.END + "\n\nHandwritten footer.\n"))
        self.assertNotIn("old generated content", updated)

    def test_invalid_markers_fail_instead_of_overwriting_handwritten_content(self):
        for original in ("No markers", profile.START, profile.END + profile.START, profile.START + profile.START + profile.END):
            with self.subTest(original=original), self.assertRaises(ValueError):
                profile.replace_activity(original, "new activity")


class FetchTests(unittest.TestCase):
    def test_paginates_only_public_users_endpoint(self):
        calls = []

        def request(path, token):
            calls.append(path)
            if path == f"users/{profile.LOGIN}":
                return ACCOUNT
            parsed = urlparse(path)
            self.assertEqual(parsed.path, f"users/{profile.LOGIN}/repos")
            query = parse_qs(parsed.query)
            self.assertEqual(query["type"], ["owner"])
            self.assertEqual(query["per_page"], ["100"])
            return [repository(str(i)) for i in range(100)] if query["page"] == ["1"] else [repository("last")]

        account, repositories = profile.fetch_public_profile("test-token", request=request)
        self.assertEqual(account, ACCOUNT)
        self.assertEqual(len(repositories), 101)
        self.assertEqual(len(calls), 3)
        self.assertNotIn("user/repos", calls)

    def test_api_rejects_authenticated_private_scope_before_network_request(self):
        for path in ("user/repos", "orgs/example/repos", "https://example.org", f"users/{profile.LOGIN}/repos-other"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                profile.api_json(path, "test-token")


if __name__ == "__main__":
    unittest.main()
