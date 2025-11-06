from abc import ABC, abstractmethod

import numpy as np


class TypedEvaluator(ABC):
    @abstractmethod
    def __call__(self, values0: list, values1: list) -> np.ndarray:
        pass

    @abstractmethod
    def name(self) -> str:
        pass
