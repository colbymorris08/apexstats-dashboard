# Apex Preflight CV

Apex-owned computer vision ingest and tracking for pitch-type anticipation.

**Savant CF = proof of concept.** Club delivery uses the same tracker schema on private X1–X4 /
TEAM angles.

```bash
cd pitch-tips/cv
pip install -r requirements.txt
python -m preflight.fetch_savant --play-id <SAVANT_PLAY_ID> --out ../clips
python -m preflight.track_pitcher --clip ../clips/<id>.mp4 --out ../tracks --camera-id CF
python -m preflight.run_poc --pitcher "Logan Webb" --season 2026 --sample 36 --work ../runs/webb_poc
```

| Module | Role |
|--------|------|
| `fetch_savant.py` | Download Savant broadcast MP4 by `playId` |
| `track_pitcher.py` | MediaPipe Tasks Pose + Face → glove/belt/flare/wrist/cheek tracks |
| `thresholds.py` | Count-scaled EV publish gates (early ~55%, two-strike ~70%) |
| `run_poc.py` | Catalog → download → track → holdout → tip cards |

Pitch-type overlays are never written into feature CSVs. Join Statcast / MLB live labels after tracking.
