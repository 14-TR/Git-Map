# r/gis Post Draft

## Title Options (pick one)
1. **I got tired of "who changed the basemap?" and built Git for ArcGIS web maps [OC]**
2. **GitMap v0.6.0 — open-source version control for ArcGIS Online/Enterprise web maps**
3. **Branch, commit, diff, and merge ArcGIS web maps like Git — open source tool I built**

---

## Recommended Title
**"I built an open-source tool to version control ArcGIS web maps (like Git, but for maps)"**

---

## Post Body

Hey r/gis — I built something I wish existed when I was managing shared web maps on a team.

**The problem:** ArcGIS Online and Enterprise Portal don't have meaningful version control. You can see "Last Modified: yesterday by someone" but you can't see *what* changed, why, or roll it back.

**What I built:** [GitMap](https://github.com/14-TR/Git-Map) — a CLI tool that gives you Git-like workflows for ArcGIS web maps.

```
$ gitmap commit -m "Added flood risk layer"
$ gitmap branch feature/new-basemap
$ gitmap diff
~ Layer: Parcels
  opacity: 0.8 → 1.0
  visible: false → true
$ gitmap merge feature/new-basemap
$ gitmap log
```

It stores snapshots of your web map JSON locally (in a `.gitmap/` directory), so you can:
- See exactly what properties changed between any two commits
- Branch and test changes without touching production
- Revert a specific commit (or the last N commits)
- Cherry-pick a change from another branch
- Push/pull between Portal environments
- Stash work-in-progress
- Get diff visualizations in Mermaid/git-graph/HTML

**Current state:**
- v0.6.0, 660+ tests, Python 3.11/3.12/3.13
- 18 Git-like commands
- ArcGIS Pro toolbox (9 native tools)
- MCP server for AI agent integration
- MIT license, open source

**Install:**
```
pip install gitmap-core
```

I'm a GIS developer who built this over the past year. It started as a personal tool and turned into something I think could actually help teams. Would love feedback from people dealing with this problem day-to-day — what's missing? What workflows matter most to you?

GitHub: https://github.com/14-TR/Git-Map

---

## Posting Tips

- Post on a **Tuesday or Wednesday morning** (MT) — peak r/gis activity
- Use the **[OC]** tag if the subreddit supports it (original content)
- Include a **screenshot or GIF** of the terminal output — visual posts perform better
- Cross-post to:
  - r/esri (if it exists)
  - r/Python (framing it as a Python tool for GIS)
  - r/opensource
  - ArcGIS Community forums (community.esri.com)
  - LinkedIn GIS groups

## Expected Questions to Prepare For

**"Does this work with ArcGIS Pro?"**
Yes — there's a Python toolbox with 9 native tools in `integrations/`.

**"What about AGOL vs Enterprise differences?"**
GitMap works with both. Set `PORTAL_URL` to either your Enterprise instance or `https://www.arcgis.com`.

**"Does it handle feature services / hosted layers?"**
Currently it versions the *web map item JSON* (layer references, symbology, extent, etc.) — not the underlying data. Feature service data versioning is a separate problem.

**"Is it production-ready?"**
It's v0.6.0 with 660+ tests. I use it on real projects. I'd call it "production-ready for developers" — it needs more UX polish before recommending it to non-technical GIS staff.

**"Why not just use ArcGIS Versioning?"**
ArcGIS Versioning is for geodatabase data. This is for web map *configuration* — which layers are shown, how they're symbolized, pop-up templates, extents, etc. Different problem.
