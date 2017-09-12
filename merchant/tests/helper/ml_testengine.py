from typing import List

import numpy as np

from ml_engine import MlEngine


# TODO: modify to fit test requirements...
class MlTestEngine(MlEngine):
    def predict_with_universal_model(self, situations: List[List[int]]):
        probas = list()
        for i in range(len(situations)):
            probas.append(0.2)
        return np.array(probas)

    def predict(self, product_id: str, situations: List[List[int]]):
        probas = list()
        for i in range(len(situations)):
            probas.append(0.2)
        return np.array(probas)

    def train_model(self, features):
        pass

    def train_universal_model(self, features: dict):
        pass
