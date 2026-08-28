# pitch-tips

Static scouting board + computer-vision diagnostics for preflight tip detection.

## Serve locally

```bash
cd pitch-tips
python -m http.server 8000
```

Open http://localhost:8000/index.html (or `board.html`).

## Pages
- `index.html` — landing page
- `board.html` — interactive scouting board (reads `data/demo.json`)
- `label.html` — web-based bounding box labeler for glove/hand fine-tuning
