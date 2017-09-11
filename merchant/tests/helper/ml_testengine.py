from typing import List

from ml_engine import MlEngine


# TODO: modify to fit test requirements...
class MlTestEngine(MlEngine):
    def predict_with_universal_model(self, situations: List[List[int]]):
        return 0

    def predict(self, product_id: str, situations: List[List[int]]):
        return 0

    def train_model(self, features):
        pass

    def train_universal_model(self, features: dict):
        pass
