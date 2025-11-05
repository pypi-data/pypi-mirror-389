# yolodetection

`yolodetection` is a lightweight wrapper around Ultralytics YOLO + SAHI sliced inference.

Main goals:
- Simple interface
- Handles large images using SAHI slicing
- Exports clean, JSON-ready detections (with centroids)
- Optional saving of prediction JSON + visualization masks to disk

---

## 🔧 Installation

```bash
pip install yolodetection
```

## Usage
```
from yolodetect import YoloInstance

options = {
    "save_json": True,
    "json_output_path": str(Path.cwd() / "exports"),
    "save_masks": True,
    "mask_output_path": str(Path.cwd() / "outputs"),
}

instance = SahiModelInstance("models/best.pt")
instance.predict("path/to/images", options)
```