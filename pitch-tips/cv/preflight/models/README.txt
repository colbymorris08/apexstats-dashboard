# Parts detector weights

Production entry point: cv/preflight/parts_detect.py -> detect_parts(image)
It runs both specialists and returns detections in the original 10-class index
space (0 pitcher_glove .. 9 plate), so it is a drop-in superset of the old
single-model output.

  parts_glovehand.pt  classes 0-1, trained on all 64 glove/hand frames
  parts_gear.pt       classes 2-9, trained on the 28 fully-labeled frames

Do not train one 10-class model across both label sets: the 2-class hard-glove
frames contain unlabeled catchers and plates, which YOLO reads as background and
learns to suppress (this collapsed catcher_mitt mAP50 0.729 -> 0.132).

parts_yolov8n.pt is the older single 10-class model (v2), kept for backward
compatibility with anything loading it directly. Prefer parts_detect.py.
parts_yolov8n_v2_backup_20260826.pt is an identical safety copy.
