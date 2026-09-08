# Full-site video publishing workflow — status

Updated: 2026-09-03 (Gausman/Hughes restore + tip1 situational distinctness)

## Disk discipline
- Hard rule: keep ≥15 GB free; purge `media/video/_tmp`, probe frames, and gitignored `runs/` after each batch.
- Clips ship via GitHub (`origin` + `preflight` subtree / gh-pages). Local machine is not the archive.
- Local `media/videos/` duplicate tree purged (site uses `media/video/` only).
- Identical situational copies hardlinked in-place to reclaim space without changing URLs.

## Unlocked arms (lite + full site allowlist)
MLB showcase: Roupp, Webb, E. Rodriguez, Pfaadt, Gausman, Gordon  
Catcher: Gabriel Moreno  
Non-MLB: Burns, Sasaki, Choi, Gu Lin, Ríos, Hughes (MiLB)

All other roster arms remain enterprise-locked (`SHOWCASE_ARM_IDS` / `SHOWCASE_IDS`).

## Players done
| Player | Tip1 pair | Notes |
|--------|-----------|--------|
| Chase Burns | `burns_ff` vs `burns_sl` | FB vs breaker |
| Roki Sasaki | `sasaki_fs` vs `sasaki_ff` | CF deliveries |
| Won-tae Choi | `choi_ch` vs `choi_si` | Verified |
| Gu Lin | `gulin_ff` vs `gulin_cu` | Trimmed |
| Wilmer Ríos | `rios_si` vs `rios_sl` | Verified |
| Gabriel Hughes | `hughes_sl` vs `hughes_ff` | **MiLB** Hartford AA — dossier restored after Gordon publish drop |
| Gabriel Moreno | `moreno_ch` @0.08s vs `moreno_ff` @0.25s | Pre-pitch apex |
| Landen Roupp | `roupp_cu` vs `roupp_si` | Tip1×situation matrix **5/5 distinct** (refreshed bases_empty + runners_on) |
| Logan Webb | `webb_ch` vs `webb_si` | Tip1 runners_on distinct |
| Eduardo Rodriguez | `erod_fc` vs `erod_ch` | Tip1 runners_on distinct |
| Brandon Pfaadt | `pfaadt_st` vs `pfaadt_si` | Tip1 runners_on distinct |
| Tanner Gordon | `gordon_ch` vs `gordon_ff` | Full pitch×situation matrix |
| Kevin Gausman | `gausman_ff` vs `gausman_fs` (+ SL tips) | **Dossier restored** from Aug 30 findings (holdout failed historically); tip1 runners_on distinct; pitchcom tips filtered |

## Remaining blockers
| Item | Status |
|------|--------|
| Genuine n≈10 distinct situational clones for all pitch codes (not just tip1) | Tip1 pairs improved; other pitch-code sits + non-MLB sits still largely hash-copies of canons. Deferred under ≥15 GB floor. |
| Gausman holdout republish | Showcase tips wired for demo; pipeline holdout still failed — full re-run left to tracking agents. |
| HTTP proxy to baseballsavant | Intermittent `ProxyError 403` via env proxy — work around with `NO_PROXY=*` / unset proxy for fetches. |

## Closed 2026-09-07
| Item | Status |
|------|--------|
| Mitt publish gap (Moreno) | `cmitt_target_*` wired into catcher discovery prefixes + `_feature_vector`; showcase/lite ship real mitt tips (no fabricated 6.8in `catcher_target_shift_x_in`). |
| Enterprise tip1 `runners_on` | Tip1 A/B `*_runners_on.mp4` hardlinked from distinct `runner_1b` / canon B-side maps; site filter `loaded`/`12`/`13`/`23` resolves suffix. |
| Roupp apex timing | Tip1 anchors CU@3.00s / SI@2.10s (leg-lift); removed forced 3.40 near-release override; scrub span 2.8s. |

## Closed 2026-09-07 — San Diego Padres team matrix
| Item | Status |
|------|--------|
| Team | **San Diego Padres** — King, Vásquez, Ray, Buehler + catchers Díaz, Campusano |
| Pitcher video matrix | **100/100** cells (5 pitch codes × canon+4 filters); n≈10 sample → dated exemplar |
| Tips | **5 top tips / pitcher** published on full site |
| Catchers | Tip A/B videos published (canon+bases_empty+runners_on); anchors 0.40/0.50s |
| Mitt/cmitt | Detector returned no mitt boxes on these CF crops — remine queued; prior catcher tips retained |
| Disk | GitHub-as-archive; local purge after push; ≥15 GB floor |


## In progress 2026-09-07 — Colorado Rockies full-staff benchmark
| Item | Status |
|------|--------|
| Team | **Colorado Rockies** — 12 pitchers with **zero** prior tip1 videos (+ Gordon/Hughes had tip1 showcase, excluded from timed set) + catchers Romo, Stallings |
| Pitchers | Castaño, Bernardino, Hill, Herget, Romano, Mejia, Manfredi, Adams, Frasso, Feltner, Sugano, Agnos |
| Note | Padres slide was a **partial matrix refresh** of already-started arms — not a full untouched staff |
| Disk | Phased push+purge under ≥12.5 GB hard floor (target ≥15 GB) |
