import torch
from sahi import AutoDetectionModel

def get_sahi_model(weights, conf=0.6, model_type="ultralytics"):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print("Using device: ", device)
    return AutoDetectionModel.from_pretrained(
        model_type=model_type,
        model_path=weights,
        device=device,
        confidence_threshold=conf,
    )