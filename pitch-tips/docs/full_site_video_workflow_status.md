# Full-site video publishing workflow — status

Updated: 2026-09-03

## Disk discipline
- Hard rule: keep ≥15 GB free; purge `media/video/_tmp`, probe frames, and gitignored `runs/` after each batch.
- Clips ship via GitHub (`origin` + `preflight` subtree / gh-pages). Local machine is not the archive.

## Unlocked arms (lite + full site allowlist)
MLB showcase: Roupp, Webb, E. Rodriguez, Pfaadt, Gausman, Gordon  
Catcher: Gabriel Moreno  
Non-MLB: Burns, Sasaki, Choi, Gu Lin, Ríos, Hughes (MiLB)

All other roster arms remain enterprise-locked (`SHOWCASE_ARM_IDS` / `SHOWCASE_IDS`).

## Players done this pass
| Player | Tip1 pair | Notes |
|--------|-----------|--------|
| Chase Burns | `burns_ff` (101 MPH) vs `burns_sl` (~86) | FB vs breaker |
| Roki Sasaki | `sasaki_fs` vs `sasaki_ff` | Interview B-roll replaced with CF deliveries |
| Won-tae Choi | `choi_ch` vs `choi_si` | Prior verified |
| Gu Lin | `gulin_ff` vs `gulin_cu` | FF trimmed before news cutaway |
| Wilmer Ríos | `rios_si` vs `rios_sl` | Prior verified |
| Gabriel Hughes | `hughes_sl` vs `hughes_ff` | **MiLB** Hartford Yard Goats AA |
| Gabriel Moreno | `moreno_ch` @0.08s vs `moreno_ff` @0.25s | Pre-pitch apex; 6.8in claim softened |

## MLB showcase status
Canonical situational MP4s already in `media/video/` for Roupp/Webb/E-Rod/Pfaadt/Gausman/Gordon. Full n≈10×situation acquisition deferred — **blocker: disk free space ~13 GB (<15 GB floor) + yt-dlp proxy failures** during this session. Do not download further batches until free ≥15 GB.

## UX fixes shipped
- Tip #1–5 pills: event delegation (survives `rebuildTipSelectors`)
- Moreno scrub window 1.2s; distinct CH/FF pre-pitch anchors; Snap seeks to apex
- Tip copy honesty: 6.8in lateral shift not visually measurable on these CF stills
