import numpy as np

from structeval.compare.methods.helpers.cosine import cosine_similarity
from structeval.compare.methods.helpers.embedding import EmbeddingModel, load_embedding_model

from .typed_evaluator import TypedEvaluator


class CosineTypedEvaluator(TypedEvaluator):
    def __init__(self, embedding_model: EmbeddingModel, model_name: str = ""):
        self.embedding_model = embedding_model
        self.model_name = model_name

    def __call__(self, values0: list[str], values1: list[str]) -> np.ndarray:
        embeddings0 = self.embedding_model.encode(values0)
        embeddings1 = self.embedding_model.encode(values1)
        return cosine_similarity(embeddings0, embeddings1)

    def name(self) -> str:
        return f"Cosine_{self.model_name}"

    @classmethod
    def from_model_name(cls, model_name: str) -> "CosineTypedEvaluator":
        model = load_embedding_model(model_name)
        return cls(embedding_model=model, model_name=model_name)
