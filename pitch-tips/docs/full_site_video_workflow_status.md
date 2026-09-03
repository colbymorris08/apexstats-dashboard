# Full-site video publishing workflow — status

Updated: 2026-09-03 (follow-up pass)

## Disk discipline
- Hard rule: keep ≥15 GB free; purge `media/video/_tmp`, probe frames, and gitignored `runs/` after each batch.
- Clips ship via GitHub (`origin` + `preflight` subtree / gh-pages). Local machine is not the archive.
- Local `media/videos/` duplicate tree purged (site uses `media/video/` only).

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
| Gabriel Hughes | `hughes_sl` vs `hughes_ff` | **MiLB** Hartford AA |
| Gabriel Moreno | `moreno_ch` @0.08s vs `moreno_ff` @0.25s | Pre-pitch apex |
| Landen Roupp | `roupp_cu` vs `roupp_si` | Tip videoA/B wired; situational matrix present |
| Logan Webb | `webb_ch` vs `webb_si` | Tip videoA/B wired |
| Eduardo Rodriguez | `erod_fc` vs `erod_ch` | Tip videoA/B wired |
| Brandon Pfaadt | `pfaadt_st` vs `pfaadt_si` | Dossier restored; tip videoA/B wired (FC→ST file map) |
| Tanner Gordon | `gordon_ch` vs `gordon_ff` | **Replaced** non-delivery imposters with Savant CF clips; full pitch×situation matrix |

## Remaining blockers
| Item | Status |
|------|--------|
| Kevin Gausman tip dossier | **Missing** from `demo.json` and backups — unlock IDs + `gausman_{ff,fs,sl}*.mp4` exist, but no ranked tips to wire. Needs tip rebuild / merge from pipeline. |
| Genuine n≈10 distinct situational clones for Roupp/Webb/E-Rod/Pfaadt | Canonical + many situational files present; several situational MP4s are still hash-duplicates of the pitch canonical. Distinct Savant refreshes deferred to stay ≥15 GB free after Gordon batch. |
| HTTP proxy to baseballsavant | Intermittent `ProxyError 403` via env proxy — work around with `NO_PROXY=*` / unset proxy for fetches. |

## UX fixes (prior pass, still shipped)
- Tip #1–5 pills: event delegation
- Moreno scrub window 1.2s; distinct CH/FF pre-pitch anchors
- Tip copy honesty: 6.8in lateral shift not visually measurable on these CF stills
