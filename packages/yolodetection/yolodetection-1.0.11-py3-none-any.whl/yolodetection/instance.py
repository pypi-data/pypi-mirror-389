from .model_provider import get_sahi_model
from .predict import sliced_predict

class InferenceModelInstance:
    def __init__(self, model, predictor):
        self.model = model
        self.predictor = predictor
    def predict(self, images, options=None):
        return self.predictor(images, self.model, options)

class SahiModelInstance(InferenceModelInstance):
    def __init__(self, weights):
        super().__init__(get_sahi_model(weights), sliced_predict)