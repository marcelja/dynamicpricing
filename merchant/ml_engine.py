from abc import ABC, abstractmethod
from threading import Lock
from typing import List


class MlEngine(ABC):
    def __init__(self):
        self.product_model_dict = dict()
        self.universal_model = None

    @abstractmethod
    def train_model(self, features):
        pass

    @abstractmethod
    def train_universal_model(self, features: dict):
        pass

    @abstractmethod
    def predict(self, product_id: str, situations: List[List[int]]):
        pass

    @abstractmethod
    def predict_with_universal_model(self, situations: List[List[int]]):
        pass

    def set_product_model_thread_safe(self, product_id, product_model):
        lock = Lock()
        lock.acquire()
        self.product_model_dict[product_id] = product_model
        lock.release()

    def set_universal_model_thread_safe(self, universal_model):
        lock = Lock()
        lock.acquire()
        self.universal_model = universal_model
        lock.release()
