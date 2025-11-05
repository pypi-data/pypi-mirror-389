import json
import uuid
from pathlib import Path
from PIL import Image
from sahi.predict import get_sliced_prediction

SAVE_LOCAL_JSON = "save_json"
SAVE_LOCAL_MASKS = "save_masks"
JSON_OUTPUT_PATH = "json_output_path"
MASK_OUTPUT_PATH = "mask_output_path"

def sliced_predict(images, model, options=None):
    """
    Use YOLO + sahi (sliced prediction) to predict objects in images
    :param images: path to images
    :param model: model instance
    :param options: { "save_json": True, "json_output_path": "/path", "save_masks" : True, "mask_output_path": "/path" }
    :return: json serialized results
    """

    results = predict_images(images, model, options)
    options = validate_options(options)
    if options.get(SAVE_LOCAL_JSON):
        save_as_json(results, options[JSON_OUTPUT_PATH])
    return results

def validate_options(options):
    if options is None:
        return {
            SAVE_LOCAL_JSON: True,
            JSON_OUTPUT_PATH: str(Path.cwd()),
            SAVE_LOCAL_MASKS: True,
            MASK_OUTPUT_PATH: str(Path.cwd())
        }
    if options.get(JSON_OUTPUT_PATH) is None and options.get(SAVE_LOCAL_JSON):
        options[JSON_OUTPUT_PATH] = str(Path.cwd())
    if options.get(MASK_OUTPUT_PATH) is None and options.get(SAVE_LOCAL_MASKS):
        options[MASK_OUTPUT_PATH] = str(Path.cwd())
    return options

def predict_images(images, model, options):
    results = []
    paths = [p for p in Path(images).iterdir() if p.is_file()]
    for path in paths:
        predictions = get_sliced_prediction(Image.open(path), model, slice_height=1024, slice_width=1024)
        results.extend(serialize_predictions(predictions, path))
        if options.get(SAVE_LOCAL_MASKS):
            predictions.export_visuals(export_dir=options[MASK_OUTPUT_PATH], file_name=f"mask_{uuid.uuid4()}")
    return results

def serialize_predictions(result, path):
    results = []
    predictions = result.to_coco_predictions()
    for prediction in predictions:
        serialized = serialize_prediction(prediction, path)
        results.append(serialized)
    return results

def serialize_prediction(result, path):
    return {
        "path": str(path),
        "class": result["category_name"],
        "confidence": result["score"],
        "bbox": result["bbox"],
        "centroid": get_centroid(result["bbox"])
    }

def get_centroid(bbox):
    x_min, y_min, width, height = bbox
    centroid_x = x_min + width / 2
    centroid_y = y_min + height / 2
    return centroid_x, centroid_y

def save_as_json(data, path):
    output_path = f"{path}/detections_{uuid.uuid4()}.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=4)
    print(f"✅ Results saved to {output_path}")