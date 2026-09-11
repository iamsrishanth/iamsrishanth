#!/usr/bin/env python3
"""Refresh a public-only GitHub profile snapshot using Python's standard library.

Only GET /users/{login} and /users/{login}/repos are requested. A token is
optional and never broadens that scope. Private, foreign-owned and forked
repositories are also explicitly rejected before any data is written.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
from html import escape
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


LOGIN = "iamsrishanth"
ROOT = Path(__file__).resolve().parents[1]
START = "<!-- ACTIVITY:START -->"
END = "<!-- ACTIVITY:END -->"
COLORS = ("#c7f284", "#88d8ff", "#b7a3ff", "#f0bd83", "#f49bb0", "#7de0c4", "#8dacf4", "#c4cdd8")


def clean_text(value: object) -> str:
    """Keep XML-safe visible characters and collapse external whitespace."""
    value = str(value)
    safe = "".join(
        char for char in value
        if char in "\t\n\r"
        or 0x20 <= ord(char) <= 0xD7FF
        or 0xE000 <= ord(char) <= 0xFFFD
        or 0x10000 <= ord(char) <= 0x10FFFF
    )
    return " ".join(safe.split())


def markdown_text(value: object) -> str:
    text = escape(clean_text(value), quote=True)
    for char in "\\`[]()*_|":
        text = text.replace(char, f"&#{ord(char)};")
    return text


def parse_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else None


def public_originals(repositories: list[dict], login: str = LOGIN) -> list[dict]:
    """Fail closed for missing visibility/fork flags; deduplicate by name."""
    originals = {}
    for repo in repositories:
        owner = repo.get("owner") or {}
        name = repo.get("name")
        if (
            repo.get("private") is False
            and repo.get("fork") is False
            and repo.get("visibility", "public") == "public"
            and str(owner.get("login", "")).casefold() == login.casefold()
            and isinstance(name, str)
            and name.strip()
        ):
            originals[name.casefold()] = repo
    return list(originals.values())


def build_snapshot(account: dict, repositories: list[dict], now: datetime, login: str = LOGIN) -> dict:
    if now.tzinfo is None:
        raise ValueError("The snapshot time must include a timezone.")
    now = now.astimezone(timezone.utc)
    if str(account.get("login", "")).casefold() != login.casefold():
        raise ValueError("The public account response does not match the profile owner.")
    created = parse_time(account.get("created_at"))
    if created is None or created > now:
        raise ValueError("The public account creation date is invalid.")
    originals = public_originals(repositories, login)
    counts = Counter(clean_text(repo["language"]) for repo in originals if repo.get("language") and clean_text(repo["language"]))
    pushes = []
    for repo in originals:
        pushed = parse_time(repo.get("pushed_at"))
        if repo["name"].casefold() != login.casefold() and pushed is not None and pushed <= now:
            pushes.append((pushed, repo))
    pushes.sort(key=lambda item: (item[0], item[1]["name"].casefold()), reverse=True)
    recent = []
    for pushed, repo in pushes:
        if not repo.get("archived", False):
            recent.append({
                "name": clean_text(repo["name"]),
                "url": f"https://github.com/{quote(login, safe='')}/{quote(repo['name'], safe='')}",
                "pushed_date_utc": pushed.date().isoformat(),
                "language": clean_text(repo.get("language") or "—"),
            })
        if len(recent) == 4:
            break
    return {
        "schema_version": 1,
        "login": login,
        "snapshot_date_utc": now.date().isoformat(),
        "account_created_year": created.year,
        "metrics": {
            "original_public_repositories": len(originals),
            "primary_languages": len(counts),
            "repositories_pushed_last_30_days": sum(now - timedelta(days=30) <= pushed <= now for pushed, _ in pushes),
        },
        "primary_languages": [{"name": name, "repositories": count} for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0].casefold()))],
        "recent_repositories": recent,
    }


def metric_cards(snapshot: dict) -> list[tuple[int, str, str]]:
    metrics = snapshot["metrics"]
    return [
        (metrics["original_public_repositories"], "original public repos", "#c7f284"),
        (metrics["primary_languages"], "primary languages", "#88d8ff"),
        (metrics["repositories_pushed_last_30_days"], "repos pushed / 30d", "#b7a3ff"),
        (snapshot["account_created_year"], "on GitHub since", "#edf3fa"),
    ]


def render_svg(snapshot: dict) -> str:
    metrics = snapshot["metrics"]
    languages = snapshot["primary_languages"]
    # Four columns keep the legend readable without squeezing language names.
    legend_rows = max(1, (len(languages) + 3) // 4)
    height = 292 + legend_rows * 28
    date = escape(clean_text(snapshot["snapshot_date_utc"]))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{height}" viewBox="0 0 1100 {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Srishanth’s public GitHub pulse</title>',
        f'<desc id="desc">Public snapshot, {date} UTC. {metrics["original_public_repositories"]} original public repositories, {metrics["primary_languages"]} primary languages, {metrics["repositories_pushed_last_30_days"]} repositories pushed in the last 30 days. Account created in {snapshot["account_created_year"]}. Language segments count repositories, not code bytes. Forks are excluded; push activity also excludes this profile repository.</desc>',
        f'<rect x="1" y="1" width="1098" height="{height - 2}" rx="22" fill="#0b1018" stroke="#253245"/>',
        '<g font-family="ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace">',
        '<circle cx="35" cy="37" r="4" fill="#c7f284"/>',
        '<text x="50" y="42" fill="#c7f284" font-size="13" letter-spacing="2">GITHUB PULSE</text>',
        f'<text x="1066" y="42" text-anchor="end" fill="#9baabe" font-size="12">SNAPSHOT · {date} UTC</text>',
    ]
    for index, (value, label, color) in enumerate(metric_cards(snapshot)):
        x = 28 + index * 264
        parts.extend([
            f'<rect x="{x}" y="65" width="252" height="113" rx="12" fill="#111a26" stroke="#253245"/>',
            f'<text x="{x + 20}" y="121" fill="{color}" font-size="42" font-weight="700">{value}</text>',
            f'<text x="{x + 20}" y="151" fill="#9baabe" font-size="13">{label}</text>',
        ])
    parts.extend([
        '<text x="30" y="210" fill="#edf3fa" font-size="13">PRIMARY LANGUAGES</text>',
        '<text x="1068" y="210" text-anchor="end" fill="#9baabe" font-size="11">REPOSITORY COUNTS · EXCLUDES REPOS WITH NO DETECTED LANGUAGE</text>',
        '<defs><clipPath id="language-bar"><rect x="30" y="225" width="1040" height="9" rx="4.5"/></clipPath></defs>',
        '<rect x="30" y="225" width="1040" height="9" rx="4.5" fill="#253245"/>',
        '<g clip-path="url(#language-bar)">',
    ])
    total = sum(language["repositories"] for language in languages)
    position = 30.0
    for index, language in enumerate(languages):
        width = 1040 * language["repositories"] / total
        parts.append(f'<rect x="{position:.3f}" y="225" width="{width:.3f}" height="9" fill="{COLORS[index % len(COLORS)]}"/>')
        position += width
    parts.append('</g>')
    for index, language in enumerate(languages):
        x = 35 + (index % 4) * 264
        y = 260 + (index // 4) * 28
        name = clean_text(language["name"])
        display_name = name if len(name) <= 23 else name[:22] + "…"
        parts.extend([
            f'<circle cx="{x}" cy="{y - 4}" r="4" fill="{COLORS[index % len(COLORS)]}"/>',
            f'<text x="{x + 13}" y="{y}" fill="#9baabe" font-size="12"><title>{escape(name)}</title>{escape(display_name)} <tspan fill="#edf3fa">{language["repositories"]}</tspan></text>',
        ])
    if not languages:
        parts.append('<text x="30" y="260" fill="#9baabe" font-size="12">No primary languages detected yet.</text>')
    parts.extend([
        f'<text x="30" y="{height - 18}" fill="#9baabe" font-size="10">PUBLIC ORIGINALS ONLY · PUSH ACTIVITY EXCLUDES THIS PROFILE · LANGUAGE SEGMENTS COUNT REPOSITORIES</text>',
        '</g>',
        '</svg>',
    ])
    return "\n".join(parts) + "\n"


def render_mobile_svg(snapshot: dict) -> str:
    """Use a separate viewport so GitHub's picture element stays legible on phones."""
    metrics = snapshot["metrics"]
    languages = snapshot["primary_languages"]
    legend_rows = max(1, (len(languages) + 1) // 2)
    height = 378 + legend_rows * 28
    date = escape(clean_text(snapshot["snapshot_date_utc"]))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="440" height="{height}" viewBox="0 0 440 {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Srishanth’s public GitHub pulse</title>',
        f'<desc id="desc">Snapshot {date} UTC. {metrics["original_public_repositories"]} original public repositories, {metrics["primary_languages"]} primary languages, {metrics["repositories_pushed_last_30_days"]} repositories pushed in the last 30 days. On GitHub since {snapshot["account_created_year"]}. Language segments count repositories, not code bytes. Forks are excluded; push activity also excludes this profile repository.</desc>',
        f'<rect x="1" y="1" width="438" height="{height - 2}" rx="20" fill="#0b1018" stroke="#253245"/>',
        '<g font-family="ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace">',
        '<circle cx="25" cy="34" r="4" fill="#c7f284"/>',
        '<text x="38" y="39" fill="#c7f284" font-size="12" letter-spacing="1.4">GITHUB PULSE</text>',
        f'<text x="418" y="39" text-anchor="end" fill="#9baabe" font-size="11">{date} UTC</text>',
    ]
    for index, (value, label, color) in enumerate(metric_cards(snapshot)):
        x = 20 + (index % 2) * 204
        y = 64 + (index // 2) * 112
        parts.extend([
            f'<rect x="{x}" y="{y}" width="196" height="100" rx="12" fill="#111a26" stroke="#253245"/>',
            f'<text x="{x + 14}" y="{y + 49}" fill="{color}" font-size="36" font-weight="700">{value}</text>',
            f'<text x="{x + 14}" y="{y + 78}" fill="#9baabe" font-size="13">{label}</text>',
        ])
    parts.extend([
        '<text x="22" y="311" fill="#edf3fa" font-size="13">PRIMARY LANGUAGES</text>',
        '<text x="22" y="331" fill="#9baabe" font-size="11">Repository counts · not code bytes</text>',
        '<defs><clipPath id="language-bar"><rect x="22" y="346" width="396" height="9" rx="4.5"/></clipPath></defs>',
        '<rect x="22" y="346" width="396" height="9" rx="4.5" fill="#253245"/>',
        '<g clip-path="url(#language-bar)">',
    ])
    total = sum(language["repositories"] for language in languages)
    position = 22.0
    for index, language in enumerate(languages):
        width = 396 * language["repositories"] / total
        parts.append(f'<rect x="{position:.3f}" y="346" width="{width:.3f}" height="9" fill="{COLORS[index % len(COLORS)]}"/>')
        position += width
    parts.append('</g>')
    for index, language in enumerate(languages):
        x = 27 + (index % 2) * 204
        y = 378 + (index // 2) * 28
        name = clean_text(language["name"])
        display_name = name if len(name) <= 16 else name[:15] + "…"
        parts.extend([
            f'<circle cx="{x}" cy="{y - 4}" r="4" fill="{COLORS[index % len(COLORS)]}"/>',
            f'<text x="{x + 13}" y="{y}" fill="#9baabe" font-size="12"><title>{escape(name)}</title>{escape(display_name)} <tspan fill="#edf3fa">{language["repositories"]}</tspan></text>',
        ])
    if not languages:
        parts.append('<text x="22" y="378" fill="#9baabe" font-size="12">No primary languages detected yet.</text>')
    parts.extend([
        f'<text x="22" y="{height - 12}" fill="#9baabe" font-size="9">Public originals · push counts exclude this profile</text>',
        '</g>',
        '</svg>',
    ])
    return "\n".join(parts) + "\n"


def render_activity(snapshot: dict) -> str:
    metrics = snapshot["metrics"]
    language_counts = " · ".join(
        f"{markdown_text(language['name'])} **{language['repositories']}**"
        for language in snapshot["primary_languages"]
    ) or "No detected primary languages yet."
    lines = [
        f"**{metrics['original_public_repositories']}** original public repos · **{metrics['primary_languages']}** primary languages · **{metrics['repositories_pushed_last_30_days']}** repos pushed / 30 days · Account created **{snapshot['account_created_year']}**",
        "",
        f"Primary languages by repository count: {language_counts}",
        "",
        "| Recently pushed | Primary language | Last push (UTC) |",
        "| :--- | :--- | :--- |",
    ]
    for repo in snapshot["recent_repositories"]:
        lines.append(f"| [{markdown_text(repo['name'])}]({repo['url']}) | {markdown_text(repo['language'])} | {repo['pushed_date_utc']} |")
    if not snapshot["recent_repositories"]:
        lines.append("| No recent public projects to display yet | — | — |")
    lines.extend([
        "",
        f"<sub>Snapshot: {snapshot['snapshot_date_utc']} UTC. Metrics count original public repositories, including archived projects and this profile; 30-day pushes exclude this profile. Language counts omit repos with no detected primary language. The table excludes forks, archived projects and this profile. Pushes can include collaborator or automated updates.</sub>",
    ])
    return "\n".join(lines)


def replace_activity(readme: str, activity: str) -> str:
    if readme.count(START) != 1 or readme.count(END) != 1:
        raise ValueError("README must contain exactly one ACTIVITY:START / ACTIVITY:END marker pair.")
    before, remainder = readme.split(START, 1)
    if END not in remainder:
        raise ValueError("README activity markers are out of order.")
    _, after = remainder.split(END, 1)
    return f"{before}{START}\n\n{activity}\n\n{END}{after}"


def api_json(path: str, token: str | None = None) -> dict | list:
    # Construct only fixed public account paths; never consume external URLs.
    if not (path == f"users/{LOGIN}" or path.startswith(f"users/{LOGIN}/repos?")):
        raise ValueError("Only the configured user's public account endpoints are allowed.")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "iamsrishanth-public-profile", "X-GitHub-Api-Version": "2026-03-10"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"https://api.github.com/{path}", headers=headers)
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_public_profile(token: str | None = None, request=api_json) -> tuple[dict, list[dict]]:
    account = request(f"users/{LOGIN}", token)
    if not isinstance(account, dict):
        raise ValueError("Unexpected public account response.")
    repositories = []
    page = 1
    while True:
        query = urlencode({"type": "owner", "sort": "full_name", "direction": "asc", "per_page": 100, "page": page})
        batch = request(f"users/{LOGIN}/repos?{query}", token)
        if not isinstance(batch, list) or any(not isinstance(repo, dict) for repo in batch):
            raise ValueError("Unexpected public repository response.")
        repositories.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return account, repositories


def write_if_changed(path: Path, content: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets-only", action="store_true", help="Generate the public JSON and SVG without editing README.")
    args = parser.parse_args()
    try:
        readme = None if args.assets_only else (ROOT / "README.md").read_text(encoding="utf-8")
        if readme is not None:
            replace_activity(readme, "")  # Check the hand-maintained file before API calls or writes.
        account, repositories = fetch_public_profile(os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"))
        snapshot = build_snapshot(account, repositories, datetime.now(timezone.utc))
        outputs = {
            ROOT / "assets/github-pulse.svg": render_svg(snapshot),
            ROOT / "assets/github-pulse-mobile.svg": render_mobile_svg(snapshot),
            ROOT / "data/public-profile.json": json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
        }
        if readme is not None:
            outputs[ROOT / "README.md"] = replace_activity(readme, render_activity(snapshot))
        changed = [str(path.relative_to(ROOT)) for path, content in outputs.items() if write_if_changed(path, content)]
    except HTTPError as error:
        print(f"Public GitHub request failed (HTTP {error.code}); existing snapshot was preserved.", file=sys.stderr)
        return 1
    except (OSError, URLError, ValueError, TypeError, KeyError) as error:
        print(f"Profile refresh failed: {error}", file=sys.stderr)
        return 1
    print(f"Public snapshot {snapshot['snapshot_date_utc']} UTC: {snapshot['metrics']['original_public_repositories']} original repos; updated {', '.join(changed) if changed else 'nothing'}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
