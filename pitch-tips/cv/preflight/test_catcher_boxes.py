"""
Contract checks for the ``cmitt_*`` box schema.

The schema is a producer/consumer agreement across two agents' code, so these
checks are aimed at the ways such an agreement silently rots: a column renamed on
one side, an absence represented as a plausible number, or the umpire class
quietly reappearing because it has the best coverage in the family.

Run directly: ``python -m preflight.test_catcher_boxes``
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from preflight import catcher_boxes as CB


def _det(name, conf, x1, y1, x2, y2):
    return {"name": name, "conf": conf, "xyxy": [x1, y1, x2, y2], "cls": 0, "model": "gear"}


W, H = 1280, 720


def test_column_set_is_exactly_twentyone_and_stable() -> None:
    """
    The column list is the interface. If it changes, tracks written on either
    side of the change are no longer the same table.
    """
    assert len(CB.BOX_COLUMNS) == 21, CB.BOX_COLUMNS
    assert CB.BOX_COLUMNS[:5] == ["cmitt_cx", "cmitt_cy", "cmitt_bw", "cmitt_bh", "cmitt_conf"]
    assert CB.BOX_COLUMNS[-1] == "cmitt_n"
    for cls in ("catcher_mitt", "plate", "catcher_shin", "catcher_cleat"):
        assert cls in CB.PERSIST_CLASSES
        for f in CB.FIELDS:
            assert f"{CB.PREFIX[cls]}_{f}" in CB.BOX_COLUMNS


def test_umpire_mask_class_is_never_persisted() -> None:
    """
    ``catcher_mask`` fires on 77.5% of frames — the joint-best rate in the family
    — and lands on the UMPIRE. It must not be persisted, and the reason must
    travel with the data rather than living only in a doc.
    """
    assert "catcher_mask" not in CB.PERSIST_CLASSES
    assert "catcher_mask" not in CB.PREFIX
    assert "catcher_mask" in CB.EXCLUDED_CLASSES
    assert "umpire" in CB.EXCLUDED_CLASSES["catcher_mask"]
    assert "catcher_mask" in CB.provenance_block()["excluded_classes"]
    # And no column could ever carry it.
    assert not any("mask" in c for c in CB.BOX_COLUMNS)


def test_mask_detections_are_dropped_even_when_most_confident() -> None:
    row = CB.box_row([_det("catcher_mask", 0.99, 100, 100, 140, 150)], W, H)
    assert all(row[c] == "" for c in CB.BOX_COLUMNS if c != CB.COUNT_COLUMN)
    assert row[CB.COUNT_COLUMN] == 0


def test_row_always_carries_every_column() -> None:
    """
    Fieldnames must not depend on what was detected, or DictWriter breaks
    partway through a clip.
    """
    for dets in ([], [_det("plate", 0.8, 600, 500, 680, 540)]):
        row = CB.box_row(dets, W, H)
        assert set(row) == set(CB.BOX_COLUMNS)


def test_coordinates_are_full_frame_normalised_centre_and_size() -> None:
    row = CB.box_row([_det("plate", 0.8, 640 - 40, 360 - 20, 640 + 40, 360 + 20)], W, H)
    # Tolerances are the 5-decimal rounding the schema applies on the way out.
    assert abs(row["cplate_cx"] - 0.5) < 1e-5
    assert abs(row["cplate_cy"] - 0.5) < 1e-5
    # bw against frame WIDTH, bh against frame HEIGHT — different denominators.
    assert abs(row["cplate_bw"] - 80 / 1280) < 1e-5
    assert abs(row["cplate_bh"] - 40 / 720) < 1e-5


def test_absence_is_blank_not_a_number() -> None:
    """
    No sentinel, no zero, no -1. A number here would be indistinguishable from a
    measurement, which is the shape of every retraction on this project.
    """
    row = CB.box_row([], W, H)
    for c in CB.BOX_COLUMNS:
        if c == CB.COUNT_COLUMN:
            continue
        assert row[c] == "", c
        assert not isinstance(row[c], (int, float)), c


def test_a_class_is_blank_in_all_five_columns_or_none() -> None:
    """A half-populated box is one a consumer can silently misread."""
    row = CB.box_row([_det("catcher_mitt", 0.4, 600, 300, 640, 340)], W, H)
    mitt = [row[f"cmitt_{f}"] for f in CB.FIELDS]
    plate = [row[f"cplate_{f}"] for f in CB.FIELDS]
    assert all(v != "" for v in mitt)
    assert all(v == "" for v in plate)


def test_examined_and_unexamined_frames_are_distinguishable() -> None:
    """
    "Nothing credible was detected here" and "this frame was never run through
    the detector" are different facts, and only ``cmitt_n`` carries the
    difference. Collapsing them into a single 0 would assert an absence that was
    never measured.

    This matters because the recommended integration runs the detector only over
    the actionable span, so most frames in a clip are genuinely unexamined.
    """
    examined = CB.box_row([], W, H)
    unexamined = CB.blank_row(examined=False)
    assert examined[CB.COUNT_COLUMN] == 0
    assert unexamined[CB.COUNT_COLUMN] == ""
    # Otherwise identical, and both carry the full column set.
    assert set(examined) == set(unexamined) == set(CB.BOX_COLUMNS)


def test_count_reports_ambiguity_at_the_credible_level_only() -> None:
    """
    The count is taken at AMBIGUITY_CONF, not at the write floor.

    Measured on real frames, the mitt class returns 5-8 boxes per frame at the
    0.05 write floor because that floor admits the whole noise lobe by design. A
    count of the noise lobe is roughly constant and therefore carries no
    information about ambiguity — a plausible-looking column with nothing in it,
    which is the defect this schema exists to avoid.
    """
    dets = [_det("catcher_mitt", 0.6, 600, 300, 640, 340),
            _det("catcher_mitt", 0.3, 300, 300, 340, 340),
            _det("catcher_mitt", 0.2, 900, 300, 940, 340),
            _det("catcher_mitt", 0.07, 100, 300, 140, 340)]
    row = CB.box_row(dets, W, H)
    assert CB.AMBIGUITY_CONF == 0.25
    # Two of the four clear 0.25; the 0.2 and 0.07 boxes are noise lobe.
    assert row[CB.COUNT_COLUMN] == 2
    # The persisted box is still the most confident one.
    assert abs(row["cmitt_cx"] - 620 / 1280) < 1e-5


def test_count_is_zero_when_only_noise_lobe_detections_exist() -> None:
    """
    A frame with only sub-0.25 mitt boxes has no credible mitt. The box is still
    persisted with its confidence, so the consumer decides — but the count says
    plainly that nothing credible was there.
    """
    row = CB.box_row([_det("catcher_mitt", 0.09, 600, 300, 640, 340)], W, H)
    assert row[CB.COUNT_COLUMN] == 0
    assert row["cmitt_conf"] == 0.09


def test_no_carry_forward_between_frames() -> None:
    """
    ``box_row`` is stateless by construction, so it cannot carry a stale box into
    a frame that had none. This is the guard that the original catcher bug lacked.
    """
    first = CB.box_row([_det("catcher_mitt", 0.9, 600, 300, 640, 340)], W, H)
    second = CB.box_row([], W, H)
    assert first["cmitt_cx"] != ""
    assert second["cmitt_cx"] == ""


def test_write_floor_is_permissive_and_below_the_consumer_floor() -> None:
    """
    Write-time thresholding is unrecoverable without another pixel pass, so the
    write floor must stay below whatever the cue gates at.
    """
    from preflight.catcher_target import MITT_CONF

    assert CB.WRITE_CONF <= 0.05
    assert CB.WRITE_CONF < MITT_CONF
    # A detection between the two floors is persisted, for the consumer to reject.
    row = CB.box_row([_det("catcher_mitt", 0.10, 600, 300, 640, 340)], W, H)
    assert row["cmitt_conf"] == 0.1


def test_below_write_floor_is_dropped() -> None:
    row = CB.box_row([_det("catcher_mitt", 0.01, 600, 300, 640, 340)], W, H)
    assert row["cmitt_cx"] == ""
    assert row[CB.COUNT_COLUMN] == 0


def test_degenerate_frame_size_yields_blanks_not_infinities() -> None:
    row = CB.box_row([_det("plate", 0.9, 0, 0, 10, 10)], 0, 0)
    assert row["cplate_cx"] == ""


def test_roundtrip_through_a_dataframe() -> None:
    rows = [CB.box_row([_det("catcher_mitt", 0.4, 600, 300, 640, 340),
                        _det("plate", 0.8, 600, 500, 680, 540)], W, H),
            CB.box_row([], W, H)]
    df = pd.DataFrame(rows)
    assert CB.has_box_schema(df)
    cx, cy, bw, bh, conf = CB.read_boxes(df, "catcher_mitt")
    assert abs(cx[0] - 620 / 1280) < 1e-5
    assert np.isnan(cx[1])


def test_pre_schema_tracks_read_as_nan_not_an_error() -> None:
    """
    A track written before this schema has no information here. NaN is what that
    means; a KeyError would force every consumer to special-case it.
    """
    df = pd.DataFrame({"frame": [0, 1, 2]})
    assert not CB.has_box_schema(df)
    cx, _, _, _, _ = CB.read_boxes(df, "catcher_mitt")
    assert len(cx) == 3 and np.isnan(cx).all()


def test_provenance_fingerprints_the_model() -> None:
    """
    The detector is about to be retrained, so tracks on either side of the retrain
    will carry different-quality boxes under identical column names. Without a
    fingerprint they cannot be told apart afterwards.
    """
    p = CB.provenance_block(stride=2)
    assert p["schema"] == CB.SCHEMA_VERSION
    assert p["stride"] == 2
    assert p["write_conf"] == CB.WRITE_CONF
    assert p["columns"] == CB.BOX_COLUMNS
    assert p["model_sha256_24_at_schema_v1"] == "15891fea835eecbb406765e2"
    assert "NaN" in p["absent"] or "empty" in p["absent"]
    if p["model_sha256_24"] is not None:
        assert len(p["model_sha256_24"]) == 24


def test_gear_only_path_does_not_pull_in_the_glovehand_model() -> None:
    """
    ``detect_parts`` runs both specialists and doubles the per-frame cost for
    classes this schema does not persist.
    """
    import inspect

    # Strip the docstring: it discusses detect_parts on purpose, and the check is
    # about what the function calls, not what it explains.
    src = inspect.getsource(CB.detect_gear).replace(CB.detect_gear.__doc__ or "", "")
    assert "GLOVEHAND" not in src
    assert "detect_parts(" not in src
    assert CB.gear_weights().name == "parts_gear.pt"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
