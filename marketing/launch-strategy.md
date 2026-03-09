# GitMap Community Launch Strategy

**Goal:** Get real users for GitMap. Move from "personal tool on GitHub" to "known solution in the GIS community."

**Target audience:** GIS professionals managing shared ArcGIS web maps on teams (government, utilities, consulting firms, enterprise).

---

## Phase 1 — Polish Before Launch (1–2 weeks)

Before posting anywhere, nail the first-impression UX:

### Must-haves
- [ ] **Demo GIF / video** (60–90 sec) showing the core workflow: init → commit → branch → diff → merge
  - Use `terminalizer` or `asciinema` for terminal recording
  - Embed in README and landing page
  - Upload to YouTube for portability

- [ ] **PyPI `gitmap` name** (or `gitmap-core` with clear install instructions)
  - Update README badge: `pip install gitmap-core`
  - Make `pip install gitmap-core && gitmap --help` work flawlessly

- [ ] **Quick-start that actually works**
  - Test the README quickstart on a clean machine with a real (or mock) Portal
  - The first 5 minutes MUST work without reading docs

- [ ] **Landing page live** at ingramgeoai.com/gitmap or gitmap.io
  - One-liner value prop
  - Install command
  - Demo GIF
  - Link to GitHub

### Nice-to-haves
- CONTRIBUTING.md with "good first issue" labels
- Discord or GitHub Discussions enabled for community Q&A

---

## Phase 2 — Community Launch (week 3–4)

### Platform order (highest → lowest expected ROI)

#### 1. ArcGIS Community Forums (community.esri.com)
- **Why first:** ESRI's own forum is where GIS professionals already go for ArcGIS questions. This is the highest-relevance audience.
- **Where:** Post in "ArcGIS Online" or "Web AppBuilder" community
- **Framing:** "I built an open-source tool to solve X — looking for beta testers"
- **Key:** Mention it's MIT, no Esri affiliation, community project

#### 2. r/gis (reddit.com/r/gis)
- ~150k members, active community
- Use the blog post draft in `marketing/reddit-rgis-post.md`
- Post Tuesday/Wednesday 8–10am MT
- Include terminal screenshot or GIF

#### 3. LinkedIn (GIS professional network)
- Post as TR Ingram with GitHub link
- Tag: #GIS #ArcGIS #OpenSource #Python
- Reach out to GIS connections directly (5–10 targeted DMs)
- Share to GIS-focused LinkedIn groups

#### 4. Twitter/X #GISchat
- Short post with GIF + link
- Hashtags: #GIS #ArcGIS #OpenSource #Python #GISchat
- Tag @EsriCommunity if possible

#### 5. dev.to / Hashnode
- Publish the blog post from `marketing/blog-post.md`
- Tags: gis, python, opensource, cli

#### 6. Hacker News (Show HN)
- Lower relevance but higher volume
- Title: "Show HN: GitMap – version control for ArcGIS web maps (open source)"
- Best time: Monday/Tuesday 9am ET

---

## Phase 3 — Follow-Through (ongoing)

### GitHub hygiene
- **Issues:** Create 5–10 "good first issue" items for contributors
- **Discussions:** Enable GitHub Discussions for Q&A
- **Releases:** Tag v0.6.0 properly with release notes pulled from CHANGELOG
- **Stars goal:** 100 stars = meaningful social proof, 500+ = credibility with enterprise

### Content cadence
- Monthly: Update CHANGELOG and post release notes
- Quarterly: New blog post (tutorial, case study, or deep dive)
- On milestones: "GitMap just hit 100 stars — here's what's coming next"

### Partnership opportunities
- Reach out to GIS consulting firms (Woolpert, AECOM, WSP) — they manage dozens of web maps
- Contact ESRI user group leaders about presenting at virtual meetups
- Seek "built with ArcGIS Python API" community recognition from ESRI

---

## Metrics to Track

| Metric | Baseline | 30-day goal | 90-day goal |
|--------|----------|-------------|-------------|
| GitHub stars | (current) | +50 | +200 |
| PyPI downloads/month | 0 | 50 | 500 |
| GitHub issues opened | 0 | 5 | 20 |
| Forks | (current) | +5 | +20 |
| r/gis post upvotes | - | 50+ | - |

---

## Key Messages

**For GIS analysts:** "Stop playing 'who changed the map.' GitMap gives you a full audit trail."

**For GIS managers:** "Test major map redesigns in isolation before pushing to production."

**For developers:** "It's Git, but for web maps. The CLI is familiar, the workflow is familiar."

**For enterprises:** "Track who changed what, when, and why — across every web map in your organization."

---

## Sample Outreach Template (cold DM / email)

> Subject: Open-source version control for ArcGIS web maps
>
> Hi [Name],
>
> I'm reaching out because I saw your work with ArcGIS [at X / on r/gis].
>
> I built GitMap — an open-source CLI that gives Git-like version control to ArcGIS web maps. You can commit snapshots, branch, diff, merge, and revert — same mental model as Git, but operating on web map JSON from Portal.
>
> It's at v0.6.0 with 660+ tests: https://github.com/14-TR/Git-Map
>
> Would you be willing to try it on a non-critical map and give me 10 minutes of feedback? I'm specifically looking to understand what's broken or missing before a wider launch.
>
> No pressure — just looking for real GIS users to test it.
>
> — TR

---

## Timing

Suggested launch window: **Late March 2026**
- After any remaining polish from Phase 1
- Avoids ESRI UC (typically June) where community attention is on ESRI announcements
- Enough runway to respond to early feedback before spring GIS conference season
