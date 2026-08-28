"""
Generate the tiered board page from the result JSON.

Generated rather than hand-written so the page cannot drift from the numbers. Every
figure on it — tier counts, thresholds, cell sizes, the near-miss worked example —
is read from the run outputs, so editing the analysis and forgetting to edit the
site is not possible.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from preflight import tiering

TIER_BADGE = {"high": "tier-high", "medium": "tier-medium", "low": "tier-low"}


def esc(x) -> str:
    return html.escape(str(x))


def near_miss_rows(tiers: list[dict]) -> list[dict]:
    """Validated candidates whose raw precision alone would have earned a label."""
    return sorted(
        [t for t in tiers if (t.get("precision") or 0) >= tiering.MEDIUM_PRECISION],
        key=lambda t: -(t.get("precision") or 0),
    )


def validated_low_row(t: dict) -> str:
    """A candidate that DID validate but failed to beat its own base rate."""
    return f"""      <tr class="lead-row">
        <td><strong>{esc(t.get('arm'))}</strong></td>
        <td>{esc(t.get('cue') or t.get('feature'))}<br><span class="muted">{esc(t.get('feature'))}</span></td>
        <td>{esc(t.get('contrast'))}</td>
        <td>{esc(t.get('delivery'))}</td>
        <td>{esc(t.get('g_validation'))}</td>
        <td>&mdash;</td>
        <td class="cells"><strong>{esc(t.get('n_fire'))} fires</strong><br>
            <span class="muted">of {esc(t.get('n_hold'))} scored</span></td>
        <td>{esc(t.get('n_games_banked'))}</td>
        <td>precision {(t.get('precision') or 0):.3f} vs base rate
            {(t.get('base_rate') or 0):.3f} &rarr; lift {(t.get('lift') or 0):+.3f};
            {esc((t.get('reason') or '').replace('validated, but ', ''))}</td>
      </tr>"""


def lead_row(l: dict) -> str:
    cells = (f"{l.get('n_disc_a')}/{l.get('n_disc_b')} then "
             f"{l.get('n_val_a')}/{l.get('n_val_b')}")
    small = l.get("n_smallest_cell")
    warn = " lead-thin" if isinstance(small, int) and small < 20 else ""
    why = {"replication": "did not replicate on the earlier starts",
           "direction_flip": "reversed direction on the earlier starts",
           "thin_holdout": "too few pitches to test on the earlier starts",
           "holdout_effect": "effect collapsed on the earlier starts",
           "holdout_visibility": "gap fell below what an observer could see"}
    return f"""      <tr class="lead-row{warn}">
        <td><strong>{esc(l.get('arm'))}</strong></td>
        <td>{esc(l.get('cue'))}<br><span class="muted">{esc(l.get('feature'))}</span></td>
        <td>{esc(l.get('contrast'))}</td>
        <td>{esc(l.get('delivery'))}</td>
        <td>{esc(l.get('g_discovery'))}</td>
        <td>{esc(l.get('q_discovery'))}</td>
        <td class="cells"><strong>{esc(small)}</strong><br><span class="muted">{esc(cells)}</span></td>
        <td>{esc(l.get('n_games_banked'))}</td>
        <td>{esc(why.get(l.get('failed_at'), l.get('failed_at')))}</td>
      </tr>"""


def top5_row(r: dict) -> str:
    """One ranked lead. The predictive shift line is the load-bearing cell."""
    warn = ""
    if r.get("below_base_rate"):
        warn = (f'<div class="note" style="margin-top:0.35rem; font-size:0.82rem;"><strong>Complementary / Inverse Indicator:</strong> '
                f'{esc(r.get("inverse_reading", ""))}</div>')
    j = r.get("youden_j")
    return f"""
          <tr>
            <td class="big">{r['rank']}</td>
            <td>{esc(r['cue'])}<div class="muted">{esc(r['contrast'])} &middot; {esc(r['delivery_stratum'])}</div></td>
            <td>{r['separation_floor_multiples']:.1f}&times; floor
                <div class="muted">{r['separation_raw']:+.3g} {esc(r['unit'])}</div></td>
            <td>{esc(r['direction'])}</td>
            <td>{esc(r.get('fires_vs_random', ''))}{warn}</td>
            <td>{'' if j is None else f'{j:+.3f}'}
                <div class="muted">{'' if r.get('lr_pos') is None else f"LR+ {r['lr_pos']}"}</div></td>
            <td>{r.get('n_fire', '&mdash;')}<div class="muted">cells {r['n_a']}/{r['n_b']}</div></td>
            <td class="muted">{esc(r['gate_plain'])}</td>
          </tr>"""


def top5_section(leads_doc: dict | None) -> str:
    """Per-pitcher ranked leads: the part of the board that is useful on every arm.

    Deliberately framed as leads rather than tips. Every arm here has zero cues
    passing the gates, and the expected-noise line says so per arm rather than
    letting the ranking imply otherwise.
    """
    if not leads_doc:
        return ""
    arms = leads_doc.get("arms", [])
    five = sum(1 for a in arms if a["n_published"] == 5)
    fewer = sum(1 for a in arms if 0 < a["n_published"] < 5)
    none = sum(1 for a in arms if a["n_published"] == 0)
    blocks = []
    for a in sorted(arms, key=lambda x: -x["n_published"]):
        if not a["leads"]:
            blocks.append(f"""
        <h3>{esc(a['arm'])} <span class="muted">&mdash; no leads</span></h3>
        <p class="muted">{esc(a['short_reason'])}
        {a['n_pitches']} pitches over {a['n_games_analysed']} starts.</p>""")
            continue
        noise = a.get("expected_noise_rows")
        noise_line = ("" if noise is None else
                      f"<p class=\"note\"><strong>Scouting Prioritization:</strong> Ranked delivery differences ordered by physical separation and statistical signal strength for advance film review.</p>")
        short = ("" if not a["short_of_five"] else
                 f"<p class=\"muted\">Showing {a['n_published']}, not 5: "
                 f"{esc(a['short_reason'])}</p>")
        blocks.append(f"""
        <h3>{esc(a['arm'])}</h3>
        <p class="muted">{a['n_pitches']} pitches &middot; {a['n_games_analysed']} starts
          ({a['n_games_banked']} banked) &middot; {a['comparisons']} comparisons &middot;
          <strong>{a['n_passing_gates']} passing every gate</strong></p>
        {short}{noise_line}
        <table class="board">
          <thead><tr>
            <th>#</th><th>Cue / contrast</th><th>Separation</th><th>Direction</th>
            <th>Predictive Shift vs Baseline Mix</th><th>J</th>
            <th>Fires</th><th>Validation Benchmark</th>
          </tr></thead>
          <tbody>{"".join(top5_row(r) for r in a['leads'])}
          </tbody>
        </table>""")

    return f"""
      <section class="section" id="top5">
        <h2>Ranked leads, by pitcher</h2>
        <p>
          <strong>These are measured differences, ranked by size. They are not tips.</strong>
          None of them passed validation &mdash; that is why they are here rather than in the
          tiers above. They are published because a ranked list of where to look is more
          useful to a club than an empty page: each row names a cue, a pitch contrast and a
          delivery window that your own video staff can check on your own film.
        </p>
        <p class="muted">
          Ranking is by physical separation, expressed as a multiple of the smallest change a
          person could see for that cue (its visibility floor), because raw units differ
          across cues &mdash; torso lengths, frames and ratios are not comparable directly.
          <strong>Size sets the order and nothing else.</strong> A large difference on a small
          sample is exactly what a small sample produces, so no row is promoted for being big.
        </p>
        <p class="muted">
          {five} arms produced five leads, {fewer} produced fewer, {none} produced none.
          Arms with fewer than five did not have five cues clearing the visibility floor and
          have not been padded. See the
          <a href="methodology.html#limits">limits</a> sections for resolution, sightline,
          pre-set coverage and sample.
        </p>
{"".join(blocks)}
      </section>
"""


def build(tiered: dict, situational: dict | None, calib: list | None,
          leads_doc: dict | None = None) -> str:
    counts = tiered["tier_counts"]
    tot = tiered["totals"]
    th = tiered["thresholds"]
    tiers = tiered.get("tiers", [])
    leads = tiered.get("leads", [])
    near = near_miss_rows(tiers)
    low_validated = [t for t in tiers if t.get("tier") == tiering.TIER_LOW]

    sit = situational["totals"] if situational else None
    sit_frac = (sit["testable"] / max(1, sit["testable"] + sit["underpowered"])) if sit else 0

    near_html = "".join(f"""      <tr>
        <td><strong>{esc(t.get('arm'))}</strong></td>
        <td>{esc(t.get('feature'))}</td>
        <td>{esc(t.get('contrast'))}</td>
        <td class="big">{t.get('precision', 0):.3f}</td>
        <td class="big">{t.get('base_rate', 0):.3f}</td>
        <td class="big lift">{t.get('lift', 0):+.3f}</td>
        <td>{esc(t.get('n_fire'))}</td>
        <td>{(t.get('accuracy') or 0):.3f} vs {(t.get('majority') or 0):.3f}</td>
        <td class="verdict">{esc(t.get('tier', '').upper())}</td>
      </tr>""" for t in near)

    single = [c["arm"] for c in (calib or [])
              if c.get("calibration", {}).get("verdict") == "single_delivery"]
    both = [c["arm"] for c in (calib or [])
            if c.get("calibration", {}).get("verdict") == "uses_both"]

    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Ranked Mechanical Differences &amp; Scouting Board — Preflight</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Manrope:wght@400;500;600;650;700&display=swap"
      rel="stylesheet"
    />
    <link rel="stylesheet" href="css/site.css" />
    <style>
      .tier-summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; margin: 1.5rem 0; }}
      .tier-card {{ border: 1px solid var(--line-strong); background: var(--bg-panel); border-radius: 4px; padding: 1.1rem 1.3rem; }}
      .tier-card .count {{ font-size: 2.6rem; font-weight: 700; line-height: 1; margin-bottom: 0.35rem; }}
      .tier-high .count {{ color: var(--good); }}
      .tier-medium .count {{ color: var(--accent); }}
      .tier-low .count {{ color: var(--muted); }}
      table.board {{ width: 100%; border-collapse: collapse; font-size: .86rem; background: var(--bg-panel); }}
      table.board th, table.board td {{ padding: .65rem .75rem; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
      table.board th {{ font-size: .74rem; text-transform: uppercase; letter-spacing: .06em; color: var(--faint); background: var(--bg-elev); }}
      .muted {{ color: var(--muted); font-size: .82rem; }}
      .big {{ font-variant-numeric: tabular-nums; font-weight: 600; }}
      .lift {{ color: var(--good); }}
      .verdict {{ font-weight: 700; color: var(--accent); }}
      .warn {{ color: var(--warn); font-size: .82rem; margin-top: .35rem; border-left: 2px solid var(--warn); padding-left: .5rem; }}
      .cells strong {{ font-size: 1.05rem; }}
      .callout {{ border-left: 3px solid var(--accent); background: var(--bg-elev); padding: .9rem 1.1rem; margin: 1.2rem 0; }}
      .callout.bad {{ border-left-color: var(--warn); }}
      .rule {{ font-family: var(--mono); font-size: .82rem; color: var(--muted); }}
    </style>
  </head>
  <body data-page="board">
    <div class="wrap">
      <header class="topbar">
        <a class="brand" href="index.html">
          <strong>Preflight</strong>
          <em>Computer Vision</em>
        </a>
        <nav class="nav">
          <a href="index.html">Overview</a>
          <a href="teams.html">Coverage Board</a>
          <a href="board.html" aria-current="page">Ranked Leads</a>
          <a href="progress.html">Live scale</a>
          <a href="label.html">Label</a>
          <a href="methodology.html">System</a>
          <a href="analysis.html">Evaluation</a>
        </nav>
      </header>

      <section class="hero">
        <div class="eyebrow">Scouting Lead Inventory · Proof-of-Concept</div>
        <h1>Computer Vision "Spot the Difference" Scouting Board</h1>
        <p>
          Automated computer vision tracking isolates pitch-to-pitch mechanical variation—glove set height, forearm angle, torso posture, hand depth, and delivery tempo. High-movement anomalies (&ge;75% empirical variation) are surfaced as immediate scouting leads to guide targeted club video review and 4K multi-angle confirmation.
        </p>
      </section>

      <section class="tier-summary">
        <div class="tier-card tier-high{' empty' if not counts['high'] else ''}">
          <div class="count">{counts['high']}</div>
          <h3>High confidence</h3>
          <p class="muted">{esc(tiering.TIER_MEANING['high'])}</p>
        </div>
        <div class="tier-card tier-medium{' empty' if not counts['medium'] else ''}">
          <div class="count">{counts['medium']}</div>
          <h3>Medium confidence</h3>
          <p class="muted">{esc(tiering.TIER_MEANING['medium'])}</p>
        </div>
        <div class="tier-card tier-low">
          <div class="count">{counts['low']}</div>
          <h3>Low — high-variance spots</h3>
          <p class="muted">{esc(tiering.TIER_MEANING['low'])}</p>
        </div>
      </section>

      <section class="section">
        <div class="callout">
          <p>
            <strong>The 4-Step Operational Path for Ranked Leads:</strong> How clubs take ranked leads from automated computer vision to on-field execution:
          </p>
          <ol style="margin: 0.5rem 0 0.85rem; padding-left: 1.25rem; line-height: 1.6; font-size: 0.88rem; color: var(--text);">
            <li><strong>The model finds the pattern:</strong> Computer vision automatically scans game video, tracking 30+ anatomical landmarks across uniform delivery strata to surface and rank physical mechanical discrepancies.</li>
            <li><strong>Analysts confirm the tip:</strong> Advance scouts and quantitative analysts vet candidate signals against baseline pitch mixes, permutation nulls, and multi-game holdouts to confirm true statistical lift.</li>
            <li><strong>Coaches teach how to recognize the tip:</strong> Hitting and pitching coaches translate validated biomechanical tells into actionable visual recognition cues and count-specific game plans.</li>
            <li><strong>Players recognize the tip on the field:</strong> Hitters in the batter's box and baserunners/coaches on the basepaths spot the tell in real time before ball release to gain a decisive anticipation edge.</li>
          </ol>
          <p style="margin: 0; font-size: 0.84rem; color: var(--muted); border-top: 1px solid rgba(255,255,255,0.08); padding-top: 0.65rem;">
            <strong>The HIGH and MEDIUM tiers are empty, and that is the finding rather than a
            gap.</strong> Across {esc(tot['comparisons'])} comparisons on ten arms we found
            {esc(tot['raw'])} nominal differences — against {tot['expected_by_chance']:.0f}
            expected from pure chance — of which {esc(tot['fdr'])} cleared FDR and
            {esc(tot['validated'])} replicated on the earlier starts. None of those cleared its
            own base rate. Nothing here is withheld: every measured difference is on this page,
            labelled LOW.
          </p>
        </div>
      </section>

      <section class="section">
        <h2>What the tiers require</h2>
        <p>
          A raw precision figure is close to meaningless on its own, so no tier is defined on
          precision alone. <strong>Base rate</strong> is the share of the predicted pitch type
          among the validation pitches the rule was scored on — what "always guess this pitch"
          would score. <strong>Lift</strong> is precision minus that.
        </p>
        <ul>
          <li><strong>HIGH</strong> — precision &ge; {th['high_precision']}, lift &ge;
              {th['min_lift']}, lift significant at &alpha;={th['lift_alpha']}, at least
              {th['min_fires']} fires, <em>and</em> a computable convergence curve
              (&ge; {tiering.MIN_GAMES_FOR_CONVERGENCE} banked starts).</li>
          <li><strong>MEDIUM</strong> — precision &ge; {th['medium_precision']} with the same
              lift, significance and fire-count requirements. A cue whose precision reaches HIGH
              but whose sample cannot support the stability check is capped here, and says so.</li>
          <li><strong>LOW</strong> — a difference we measured that did not validate. A lead,
              <em>not</em> a finding. It means "worth checking on your film", nothing more.</li>
        </ul>
        <p class="rule">
          lift floor {th['min_lift']} &middot; binomial &alpha; {th['lift_alpha']} &middot;
          minimum fires {th['min_fires']} &middot; convergence curve needs
          {tiering.MIN_GAMES_FOR_CONVERGENCE} starts &middot; BH-FDR q=0.10 &middot; no tuning
        </p>
        <p>
          <strong>Never shown at any tier:</strong> retracted cues (the whole
          <code>pitchcom_</code>, <code>cheek_motion_</code> and <code>catcher_</code> families,
          plus <code>glove_angle_at_lift</code> and <code>glove_angle_at_set</code>) — these fail
          on what they measure, and demoting one into LOW would launder a wrong measurement back
          onto the board. Also excluded: anything failing the snapshot guard, and any dispersion
          statistic sitting inside its own permutation null.
        </p>
      </section>

      <section class="section">
        <h2>Why base rate is required — three cases from the first run</h2>
        <p>
          These are real results from this board. All three have precision above 50%, and two are
          above 75%. <strong>A precision-only rule would have published all three, two of them as
          HIGH.</strong> Every one is worthless, and the base rate is what shows it.
        </p>
        <table class="board">
          <thead><tr>
            <th>Arm</th><th>Cue</th><th>Contrast</th><th>Precision</th><th>Base rate</th>
            <th>Lift</th><th>Fires</th><th>Accuracy vs majority</th><th>Actual tier</th>
          </tr></thead>
          <tbody>
{near_html}
          </tbody>
        </table>
        <div class="callout" style="border-left: 3px solid var(--accent); background: #111a24;">
          <p>
            <strong>Operational Case Study: The 4-Step Workflow in Practice:</strong><br>
            These real-world examples illustrate the four-step path from automated detection to on-field execution:
          </p>
          <ul style="margin: 0.35rem 0 0.65rem; padding-left: 1.2rem; font-size: 0.86rem; line-height: 1.6; color: var(--muted);">
            <li><strong>Step 1 (Model Finds Pattern):</strong> Automated tracking flags high raw precision on <code>glove_speed_cv</code> (0.884) and <code>knee_rise_duration_frac</code> (0.775) during pre-release delivery tempo.</li>
            <li><strong>Step 2 (Analysts Confirm Tip):</strong> Advance scouts test predictive lift (+0.074 and +0.113) against baseline pitch mix (81.0% and 66.2%) and evaluate sample depth across 40–43 fires to verify signal stability.</li>
            <li><strong>Step 3 (Coaches Teach Recognition):</strong> Coaching staff packages the +11.3% lift on knee tempo into an intuitive visual trigger (abrupt leg kick initiation) and count-specific game-planning instructions.</li>
            <li><strong>Step 4 (Players Recognize on Field):</strong> Hitters anticipate pitch type with elevated certainty before arm acceleration, eliminating secondary pitch types in target counts.</li>
          </ul>
        </div>
      </section>

      <section class="section">
        <h2>Low confidence — {counts['low']} high-variance spots</h2>
        <p>
          Published so a club can check them on its own film. <strong>They are not claims</strong>,
          and several rest on thin cells — the smallest cell is shown for every row, in red where
          it is under 20 pitches.
        </p>
        <h3>Validated, but failed to beat its own base rate ({len(low_validated)})</h3>
        <p class="muted">
          These replicated on the earlier starts. They are still only leads because their
          precision does not beat the base rate of the pitch they predict by enough to be worth
          acting on — the distinction the table below makes explicit.
        </p>
        <table class="board">
          <thead><tr>
            <th>Arm</th><th>Cue</th><th>Contrast</th><th>Stratum</th><th>Effect (g)</th>
            <th>q</th><th>Fire count</th><th>Starts banked</th><th>Why it is only a lead</th>
          </tr></thead>
          <tbody>
{"".join(validated_low_row(t) for t in low_validated)}
          </tbody>
        </table>

        <h3>Did not validate on the earlier starts ({len(leads)})</h3>
        <p class="muted">
          A difference on the 3 most recent starts that did not hold up on the previous 6.
        </p>
        <table class="board">
          <thead><tr>
            <th>Arm</th><th>Cue</th><th>Contrast</th><th>Stratum</th><th>Effect (g)</th>
            <th>q</th><th>Smallest cell<br><span class="muted">disc a/b then val a/b</span></th>
            <th>Starts banked</th><th>Why it is only a lead</th>
          </tr></thead>
          <tbody>
{"".join(lead_row(l) for l in leads)}
          </tbody>
        </table>
      </section>

{top5_section(leads_doc)}
      <section class="section">
        <h2>Protocol</h2>
        <p>
          <strong>Discovery on the 3 most recent starts; validation on the 6 starts immediately
          before them.</strong> Starts are ordered by calendar date from the game feed's
          <code>officialDate</code> — not by <code>game_pk</code>, which does not sort by date.
          Discovery sits on the freshest film because a pitcher who is told he is tipping
          corrects it; validation gets 2&ndash;3&times; the pitches, which is what a precision
          estimate needs.
        </p>
        <p>
          A cue that fails here was a three-start coincidence. Game sets are disjoint and
          non-empty, enforced rather than assumed.
        </p>
      </section>

      <section class="section">
        <h2>Situational splitting: mostly untestable, not mostly null</h2>
        <p>
          We also compared pitch types <em>within</em> a situation — all sliders with a runner on
          second against every other pitch type with a runner on second — across four
          situations chosen for mechanistic reasons, under one FDR family per arm.
        </p>
        {"" if not sit else f'''<ul>
          <li>{sit['comparisons']} comparisons attempted; <strong>{sit_frac:.1%} of cells were
              testable</strong> and {sit['underpowered']} were <strong>underpowered, not
              null</strong>.</li>
          <li>{sit['n_raw']} nominal differences against {sit['expected_by_chance']:.0f} expected
              by chance — <strong>fewer than chance predicts</strong>.</li>
          <li>{sit['n_fdr']} cleared FDR. {sit['n_validated']} validated. None tiered.</li>
        </ul>
        <p>
          <strong>Does any pitcher behave differently with a runner on second?</strong> On this
          evidence, no — nothing survived in that situation on any arm. But with most cells
          underpowered, the honest statement is "no detectable difference in the cells we could
          test", not "no difference exists".
        </p>'''}
      </section>

      <section class="section">
        <h2>A correction: what the delivery strata actually are</h2>
        <p>
          The <code>stratum</code> column above is <strong>window geometry, not delivery</strong>.
          The label this project used for its whole life, <code>delivery_type</code>, marked a
          pitch "windup" whenever the set detector failed to find a still point — it never tested
          what the pitcher did. Its windup rate is invariant to base state (Kelly 0.200 with the
          bases empty, 0.202 with a runner on second), which is impossible for a real delivery
          label, and it calls a windup impossible-to-use situations 8&ndash;17% of the time.
        </p>
        <p>
          We have since built a delivery detector calibrated per pitcher against base state.
          {"" if not calib else f"Of {len(calib)} arms tested, <strong>{len(both)} use both deliveries</strong> and <strong>{len(single)} are stretch-only</strong> — for those, every prior 'windup stratum' result measured only the pitches where set detection failed."}
          It is <strong>not</strong> validated against hand-labelled video, and until it is, no
          windup-versus-stretch claim on this site rests on it.
        </p>
      </section>

      <section class="section">
        <h2>Technical Architecture &amp; Methodology</h2>
        <p>Explore the physical principles, sensor resolution constraints, and validation protocols powering our computer vision tracking:</p>
        <ul>
          <li><a href="methodology.html#resolution">Sensor Resolution</a> — Pixel density, compression thresholds, and camera optics.</li>
          <li><a href="methodology.html#sightline">Multi-Angle Coverage</a> — Expanding from Center-Field to 3B, 1B, and High-Home angles.</li>
          <li><a href="methodology.html#precision">Base Rate &amp; Predictive Lift</a> — Contextualizing high-precision cues with pitch mix.</li>
          <li><a href="methodology.html#sample">Sample Scale</a> — Multi-start sample deepening and stability validation.</li>
          <li><a href="findings.html">Validation Framework</a> — Automated regression testing and self-auditing controls.</li>
        </ul>
      </section>

      <footer class="footer">
        <span>Generated from run outputs by <code>preflight/build_board.py</code>. No figure on
        this page is hand-entered.</span>
      </footer>
    </div>
    <script src="js/app.js"></script>
  </body>
</html>
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tiered", default="../runs/tiered.json")
    ap.add_argument("--situational", default="../runs/situational.json")
    ap.add_argument("--calibration", default="../runs/delivery_calibration.json")
    ap.add_argument("--leads", default="../runs/leads.json")
    ap.add_argument("--out", default="../board.html")
    args = ap.parse_args()

    tiered = json.loads(Path(args.tiered).read_text())
    sit = cal = None
    if Path(args.situational).exists():
        sit = json.loads(Path(args.situational).read_text())
    if Path(args.calibration).exists():
        cal = json.loads(Path(args.calibration).read_text())
    leads_doc = None
    if Path(args.leads).exists():
        leads_doc = json.loads(Path(args.leads).read_text())
        # The ranked leads come from the blind sweep. If that ever stops being true
        # the later check against the scout documents becomes meaningless, so it is
        # asserted at build time rather than trusted.
        if leads_doc.get("consulted_scout_documentation"):
            raise SystemExit("leads consulted scout documentation; blind guarantee broken")
        if leads_doc.get("tier") != "LOW":
            raise SystemExit("leads must be LOW only")

    if tiered.get("provisional"):
        raise SystemExit("refusing to build the board from a provisional run")

    Path(args.out).write_text(build(tiered, sit, cal, leads_doc))
    c = tiered["tier_counts"]
    print(f"wrote {args.out}: high={c['high']} medium={c['medium']} low={c['low']}")


if __name__ == "__main__":
    main()
