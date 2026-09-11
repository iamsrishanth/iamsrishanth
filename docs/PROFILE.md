# Behind the profile

This is the profile repository for [Srishanth Goud / @iamsrishanth](https://github.com/iamsrishanth). GitHub displays the root `README.md` on the account's profile.

The design takes its content from public repository metadata and project READMEs. Featured projects are curated for variety: systems, AI integration, Android, and web design. Forked projects are not presented as original work. The profile makes no claims about employment, qualifications, availability, or private work.

## Design references

The artwork and copy are original. These profiles informed the approach:

- [Anurag Hazra](https://github.com/anuraghazra/anuraghazra): a recognizable introduction and emphasis on selected projects.
- [DenverCoder1](https://github.com/DenverCoder1/DenverCoder1): coordinated visuals, expandable sections, and meaningful links.
- [Sindre Sorhus](https://github.com/sindresorhus/sindresorhus): concise copy, personality, and small local visual assets.
- [Awesome GitHub Profile README](https://github.com/abhisheknaiidu/awesome-github-profile-readme): a wider reference gallery for creative, dynamic, and interactive profiles.

The theme is a builder's control room: dark navy, lime, ice blue, and lavender. SVG artwork lives in this repository, uses no external fonts or image services, and respects reduced-motion preferences. The hero has a separate narrow-screen composition. Project cards wrap onto separate lines when there is insufficient room.

GitHub supports [native expandable sections](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/organizing-information-with-collapsed-sections). Its [rendering pipeline](https://github.com/github/markup) sanitizes scripts and inline styles, so this profile uses links, disclosures, and SVG animation for interaction. The “Say hello” link opens a public issue form; the visitor chooses whether to submit it.

## Edit the profile

- Edit `README.md` to change the introduction, project links, paths, or puzzle.
- Edit `scripts/render_brand_assets.py` to change artwork, titles, colors, or project-card descriptions, then run `python3 scripts/render_brand_assets.py`.
- Keep each image's alt text in `README.md` consistent with its visible content.
- Edit `.github/ISSUE_TEMPLATE/say-hello.yml` to change the conversation form.
- Keep the activity markers intact; their contents are maintained automatically.

## Public activity snapshots

`scripts/refresh_profile.py` fetches the account's public repository data, writes `data/public-profile.json` and `assets/github-pulse.svg`, and updates the activity block in `README.md`. It uses only Python's standard library. No third-party stats service or personal access token is required for the scheduled workflow.

The metric definitions, snapshot date, and recent repository push dates are included in the activity disclosure. Primary-language counts describe repositories, not coding time or lines of code. Repository pushes can include changes from collaborators or automation; they are not a count of personally authored commits. Private repositories and forks are excluded. The profile repository is excluded from recent-activity metrics so automatic refreshes do not look like project work.

The refresh workflow runs daily and can also be started from **Actions → Refresh public profile → Run workflow**. GitHub may delay scheduled jobs and [disables schedules in public repositories after prolonged inactivity](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule); the checked-in snapshot remains visible if a refresh does not run. The workflow needs the repository's built-in token to have `contents: write` permission to save changed snapshots. It never force-pushes.

Run locally:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/render_brand_assets.py
python3 scripts/refresh_profile.py
```

The refresh script can use `GH_TOKEN` or `GITHUB_TOKEN` for GitHub API rate limits. Never commit a token. Preview `README.md` on GitHub to verify its sanitized rendering; generic Markdown previews may differ.
