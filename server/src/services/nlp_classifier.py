from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)


class NLPClassifier:
    """Generic ONNX-based text classifier using tokenizers + onnxruntime."""

    def __init__(
        self,
        name: str,
        repo_id: str,
        onnx_filename: str,
        tokenizer_filename: str,
        labels: dict[int, str],
        *,
        multi_label: bool,
        use_token_type_ids: bool,
        positive_labels: list[str] | None = None,
        model_dir: str = "data/models",
    ) -> None:
        self.name = name
        self._labels = labels
        self._multi_label = multi_label
        self._use_token_type_ids = use_token_type_ids
        self._positive_labels = positive_labels
        self._session = None
        self._tokenizer = None

        try:
            self._load(repo_id, onnx_filename, tokenizer_filename, model_dir)
            logger.info("NLP classifier '%s' loaded", name)
        except Exception:
            logger.warning(
                "NLP classifier '%s' failed to load — unavailable", name, exc_info=True
            )

    @property
    def available(self) -> bool:
        return self._session is not None and self._tokenizer is not None

    def _load(
        self,
        repo_id: str,
        onnx_filename: str,
        tokenizer_filename: str,
        model_dir: str,
    ) -> None:
        from huggingface_hub import hf_hub_download
        from tokenizers import Tokenizer
        import onnxruntime as ort

        onnx_path = hf_hub_download(repo_id, onnx_filename, local_dir=model_dir)
        tokenizer_path = hf_hub_download(
            repo_id, tokenizer_filename, local_dir=model_dir
        )

        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        opts.intra_op_num_threads = 1
        self._session = ort.InferenceSession(
            onnx_path, opts, providers=["CPUExecutionProvider"]
        )

        self._tokenizer = Tokenizer.from_file(tokenizer_path)
        self._tokenizer.enable_truncation(max_length=512)

    def classify(self, text: str) -> dict[str, float]:
        """Classify text and return per-label scores (0.0-1.0)."""
        if not self.available:
            return {}

        encoding = self._tokenizer.encode(text)

        feeds: dict[str, np.ndarray] = {
            "input_ids": np.array([encoding.ids], dtype=np.int64),
            "attention_mask": np.array([encoding.attention_mask], dtype=np.int64),
        }
        if self._use_token_type_ids:
            feeds["token_type_ids"] = np.array([encoding.type_ids], dtype=np.int64)

        logits = self._session.run(None, feeds)[0][0]

        if self._multi_label:
            scores = 1.0 / (1.0 + np.exp(-logits))
        else:
            exp = np.exp(logits - np.max(logits))
            scores = exp / exp.sum()

        return {self._labels[i]: float(scores[i]) for i in range(len(scores))}

    def check(self, text: str, threshold: float) -> tuple[bool, dict[str, float]]:
        """Check text against threshold. Returns (flagged, scores).

        Only positive_labels are checked against the threshold.
        If positive_labels is None, all labels are checked.
        """
        scores = self.classify(text)
        if not scores:
            return False, {}
        check_labels = self._positive_labels or list(scores.keys())
        flagged = any(scores.get(label, 0) >= threshold for label in check_labels)
        return flagged, scores


def create_toxicity_classifier(model_dir: str = "data/models") -> NLPClassifier:
    return NLPClassifier(
        name="toxicity",
        repo_id="minuva/MiniLMv2-toxic-jigsaw-onnx",
        onnx_filename="model_optimized_quantized.onnx",
        tokenizer_filename="tokenizer.json",
        labels={
            0: "toxic",
            1: "severe_toxic",
            2: "obscene",
            3: "threat",
            4: "insult",
            5: "identity_hate",
        },
        multi_label=True,
        use_token_type_ids=True,
        model_dir=model_dir,
    )


def create_injection_classifier(model_dir: str = "data/models") -> NLPClassifier:
    return NLPClassifier(
        name="injection",
        repo_id="protectai/deberta-v3-base-prompt-injection-v2",
        onnx_filename="onnx/model.onnx",
        tokenizer_filename="onnx/tokenizer.json",
        labels={0: "SAFE", 1: "INJECTION"},
        multi_label=False,
        use_token_type_ids=False,
        positive_labels=["INJECTION"],
        model_dir=model_dir,
    )
