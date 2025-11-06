from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol, runtime_checkable

import numpy as np


@runtime_checkable
class EmbeddingModel(Protocol):
    def encode(self, sentences: Sequence[str]) -> np.ndarray: ...

    def name(self) -> str: ...


if TYPE_CHECKING:  # for type-checkers only; no runtime dependency
    from sentence_transformers import SentenceTransformer as _SentenceTransformer  # noqa: F401


def load_embedding_model(model_name: str) -> EmbeddingModel:
    """Lazily import sentence-transformers and load a model.

    This keeps the heavy dependency optional and defers import cost until used.
    """

    try:
        from sentence_transformers import SentenceTransformer  # noqa
    except Exception as exc:  # pragma: no cover - import error path
        raise ImportError("sentence-transformers is required for embedding-based evaluators. Install with 'pip install sentence-transformers'.") from exc

    return SentenceTransformer(model_name)
