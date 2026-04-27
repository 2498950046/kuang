from __future__ import annotations

import csv
import io
import json
import os
import re
import runpy
import tempfile
import time
from collections import OrderedDict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

import torch
import torch.nn.functional as F
from PIL import Image
from sklearn.metrics import precision_recall_fscore_support
from torchvision import models, transforms

from app.image_archive import IMAGE_EXTENSIONS, iter_zip_image_entries


PROJECT_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = PROJECT_ROOT.parent
MODEL_ROOT = Path(os.getenv("ML_PLATFORM_MODEL_ROOT", str(WORKSPACE_ROOT / "model"))).resolve()
CHECKPOINT_ROOT = MODEL_ROOT / "checkpoint+log2"
DATA_ROOT = MODEL_ROOT
CV_MODEL_ROOT = MODEL_ROOT / "model2" if (MODEL_ROOT / "model2").exists() else MODEL_ROOT / "model"


@dataclass(frozen=True)
class PrismProviderSpec:
    provider: str
    display_name: str
    dataset_name: str
    dataset_dir: Path
    checkpoint_path: Path
    loss_file: Path


@dataclass(frozen=True)
class PMTProviderSpec:
    provider: str
    display_name: str
    dataset_name: str
    base_dir: Path
    config_path: Path
    metrics_dir: Path
    checkpoints_dir: Path


@dataclass(frozen=True)
class CVProviderSpec:
    provider: str
    display_name: str
    dataset_name: str
    model_dir: Path
    checkpoint_file: Path
    label_file: Path | None
    code_file: Path | None


PRISM_PROVIDER_SPECS = [
    PrismProviderSpec(
        provider="prism-baby",
        display_name="PRISM Baby",
        dataset_name="baby",
        dataset_dir=DATA_ROOT / "PRISM-baby" / "data" / "baby",
        checkpoint_path=CHECKPOINT_ROOT / "PRISM_baby_original.pt",
        loss_file=CHECKPOINT_ROOT / "PRISM_baby_original_losses.json",
    ),
    PrismProviderSpec(
        provider="prism-cloth",
        display_name="PRISM Cloth",
        dataset_name="cloth",
        dataset_dir=DATA_ROOT / "PRISM-cloth" / "data" / "cloth",
        checkpoint_path=CHECKPOINT_ROOT / "PRISM_cloth_original.pt",
        loss_file=CHECKPOINT_ROOT / "PRISM_cloth_original_losses.json",
    ),
    PrismProviderSpec(
        provider="prism-sports",
        display_name="PRISM Sports",
        dataset_name="sports",
        dataset_dir=DATA_ROOT / "PRISM-sports" / "data" / "sports",
        checkpoint_path=CHECKPOINT_ROOT / "PRISM_sports_original.pt",
        loss_file=CHECKPOINT_ROOT / "PRISM_sports_original_losses.json",
    ),
]

PMT_PROVIDER_SPECS = [
    PMTProviderSpec(
        provider="pmt-traffic",
        display_name="PMT Traffic",
        dataset_name="traffic",
        base_dir=MODEL_ROOT / "PMT-traffic",
        config_path=MODEL_ROOT / "PMT-traffic" / "pmt_traffic_api" / "config.py",
        metrics_dir=MODEL_ROOT / "PMT-traffic" / "output" / "metrics",
        checkpoints_dir=MODEL_ROOT / "PMT-traffic" / "output" / "checkpoints",
    ),
    PMTProviderSpec(
        provider="pmt-weather",
        display_name="PMT Weather",
        dataset_name="weather",
        base_dir=MODEL_ROOT / "PMT-weather",
        config_path=MODEL_ROOT / "PMT-weather" / "pmt_weather_api" / "config.py",
        metrics_dir=MODEL_ROOT / "PMT-weather" / "output" / "metrics",
        checkpoints_dir=MODEL_ROOT / "PMT-weather" / "output" / "checkpoints",
    ),
    PMTProviderSpec(
        provider="pmt-ecl",
        display_name="PMT ECL",
        dataset_name="ECL",
        base_dir=MODEL_ROOT / "PMT-ECL",
        config_path=MODEL_ROOT / "PMT-ECL" / "pmt_ecl_api" / "config.py",
        metrics_dir=MODEL_ROOT / "PMT-ECL" / "output" / "metrics",
        checkpoints_dir=MODEL_ROOT / "PMT-ECL" / "output" / "checkpoints",
    ),
]

CV_PROVIDER_SPECS = [
    CVProviderSpec(
        provider="cv-convnext-44",
        display_name="ConvNeXt 44-class",
        dataset_name="gemstone-44",
        model_dir=CV_MODEL_ROOT / "convnext_44",
        checkpoint_file=CV_MODEL_ROOT / "convnext_44" / "convnext_44.pth",
        label_file=CV_MODEL_ROOT / "convnext_44" / "class_mapping.json",
        code_file=CV_MODEL_ROOT / "convnext_44" / "代码.txt",
    ),
    CVProviderSpec(
        provider="cv-convnext-557",
        display_name="ConvNeXt 557-class",
        dataset_name="geology-557",
        model_dir=CV_MODEL_ROOT / "convnext_557",
        checkpoint_file=CV_MODEL_ROOT / "convnext_557" / "best_model_weights.pth",
        label_file=CV_MODEL_ROOT / "convnext_557" / "all_class_mapping.json",
        code_file=CV_MODEL_ROOT / "convnext_557" / "代码.txt",
    ),
    CVProviderSpec(
        provider="cv-efficientb3-44",
        display_name="EfficientNet-B3 44-class",
        dataset_name="gemstone-44",
        model_dir=CV_MODEL_ROOT / "efficienetb3_44",
        checkpoint_file=CV_MODEL_ROOT / "efficienetb3_44" / "efficientb3.pth",
        label_file=CV_MODEL_ROOT / "efficienetb3_44" / "labels.txt",
        code_file=CV_MODEL_ROOT / "efficienetb3_44" / "代码.txt",
    ),
]

MAX_CV_EVAL_IMAGES = 800


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return json.loads(path.read_text(encoding="utf-8-sig"))


def _count_lines(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def _read_losses(path: Path) -> list[dict[str, Any]]:
    raw = _load_json(path)
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    return []


def _load_config_defaults(path: Path) -> tuple[dict[str, Any], list[str]]:
    scope = runpy.run_path(str(path))
    config_cls = scope.get("Config")
    if config_cls is None:
        return {}, []
    defaults = dict(getattr(config_cls, "DEFAULTS", {}))
    supported_metrics = list(getattr(config_cls, "SUPPORTED_METRICS", []))
    return defaults, supported_metrics


def _latest_metrics_file(path: Path) -> Path | None:
    files = sorted(path.glob("*_metrics.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    return files[0] if files else None


def _parse_code_hint_value(path: Path | None, pattern: str) -> float | int | None:
    if path is None or not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    value = match.group(1)
    try:
        return int(value) if value.isdigit() else float(value)
    except ValueError:
        return None


class PrismDataMapper:
    def __init__(self, dataset_dir: Path):
        self.dataset_dir = Path(dataset_dir)
        self.external_to_internal: dict[str, int] = {}
        self.internal_to_metadata: dict[int, dict[str, Any]] = {}
        self._load_item_mapping()

    def _load_item_mapping(self) -> None:
        mapping_path = self.dataset_dir / "i_id_mapping.csv"
        if not mapping_path.exists():
            return

        with mapping_path.open("r", encoding="utf-8", newline="") as handle:
            sample = handle.read(1024)
            handle.seek(0)
            delimiter = "\t" if "\t" in sample else ","
            reader = csv.DictReader(handle, delimiter=delimiter)
            for row in reader:
                internal_id = int(row["itemID"])
                source_item_id = str(row.get("source_itemID", internal_id))
                asin = str(row.get("asin", source_item_id))

                metadata = {
                    "item_id": internal_id,
                    "source_item_id": int(source_item_id) if source_item_id.isdigit() else source_item_id,
                    "asin": asin,
                }
                self.internal_to_metadata[internal_id] = metadata
                for key in {str(internal_id), source_item_id, asin}:
                    self.external_to_internal[key] = internal_id

    def validate_user_history(self, user_history: list[Any], max_length: int = 50) -> list[int]:
        if not isinstance(user_history, list):
            raise ValueError("user_history must be a list")
        if not user_history:
            raise ValueError("user_history cannot be empty")

        cleaned: list[int] = []
        for item in user_history:
            if isinstance(item, int):
                cleaned.append(item)
                continue

            key = str(item).strip()
            if not key:
                continue
            if key in self.external_to_internal:
                cleaned.append(self.external_to_internal[key])
            elif key.isdigit():
                cleaned.append(int(key))

        if not cleaned:
            raise ValueError("user_history does not contain valid item ids")
        return cleaned[-max_length:]

    def format_recommendations(self, internal_items: list[int], scores: list[float] | None = None) -> list[dict[str, Any]]:
        results = []
        score_list = scores or [None] * len(internal_items)
        for internal_id, score in zip(internal_items, score_list, strict=False):
            metadata = self.internal_to_metadata.get(
                int(internal_id),
                {
                    "item_id": int(internal_id),
                    "source_item_id": int(internal_id),
                    "asin": str(internal_id),
                },
            )
            source_id = metadata.get("source_item_id")
            item_id = source_id if isinstance(source_id, int) else int(metadata["item_id"])
            label = metadata.get("asin") or str(item_id)
            results.append(
                {
                    "item_id": item_id,
                    "score": float(score) if score is not None else None,
                    "label": str(label),
                    "metadata": metadata,
                }
            )
        return results


class PrismCheckpointService:
    def __init__(self, spec: PrismProviderSpec):
        self.spec = spec
        self.checkpoint = torch.load(spec.checkpoint_path, map_location="cpu")
        self.mapper = PrismDataMapper(spec.dataset_dir)
        self.item_popularity = self.checkpoint["item_popularity"].float()
        item_embeddings = self.checkpoint.get("item_embeddings")
        self.item_embeddings = item_embeddings.float() if isinstance(item_embeddings, torch.Tensor) else None
        if self.item_embeddings is not None:
            self.item_embeddings = F.normalize(self.item_embeddings, dim=1)
        self.model_state_dict = self.checkpoint.get("model_state_dict") or {}
        self.loss_entries = _read_losses(spec.loss_file)
        self.latest_test_metrics = self.checkpoint.get("latest_test_metrics") or {}
        self.sample_history = self.mapper.validate_user_history([1, 2, 3])

    @property
    def model_name(self) -> str:
        return str(self.checkpoint.get("model_name") or "original-prism-miggt")

    @property
    def parameter_count(self) -> int:
        return sum(int(value.numel()) for value in self.model_state_dict.values() if isinstance(value, torch.Tensor))

    @property
    def dataset_summary(self) -> dict[str, Any]:
        interactions_file = next(iter(self.spec.dataset_dir.glob("*.inter")), None)
        return {
            "data_name": self.spec.dataset_name,
            "num_users": _count_lines(self.spec.dataset_dir / "u_id_mapping.csv"),
            "num_items": int(self.checkpoint.get("num_items") or self.item_popularity.numel()),
            "item_size": int(self.item_popularity.numel()),
            "num_interactions": _count_lines(interactions_file) if interactions_file else None,
            "max_seq_length": int(self.checkpoint.get("config", {}).get("seq_len", 50)),
        }

    @property
    def training_summary(self) -> dict[str, Any]:
        config = self.checkpoint.get("config") or {}
        loss_points = [
            {"epoch": int(entry["epoch"]), "loss": float(entry["loss"])}
            for entry in self.loss_entries
            if "epoch" in entry and "loss" in entry
        ]
        losses = [point["loss"] for point in loss_points]
        return {
            "checkpoint_path": str(self.spec.checkpoint_path),
            "epochs": len(loss_points) or len(self.loss_entries) or config.get("num_epochs"),
            "batch_size": config.get("batch_size"),
            "learning_rate": config.get("lr"),
            "train_loss_start": losses[0] if losses else None,
            "train_loss_end": losses[-1] if losses else None,
            "train_loss_curve": [point["loss"] for point in loss_points],
            "train_loss_epochs": [point["epoch"] for point in loss_points],
            "train_loss_points": loss_points,
        }

    @property
    def experiment_metrics(self) -> dict[str, Any]:
        metrics = dict(self.latest_test_metrics)
        if "HR" in metrics and "HR@10" not in metrics:
            metrics["HR@10"] = metrics["HR"]
        if "NDCG" in metrics and "NDCG@10" not in metrics:
            metrics["NDCG@10"] = metrics["NDCG"]
        if "RECALL" in metrics and "Recall@10" not in metrics:
            metrics["Recall@10"] = metrics["RECALL"]
        return metrics

    def _compute_scores(self, history: list[int]) -> torch.Tensor:
        if self.item_embeddings is not None:
            valid_history = [item for item in history if 0 <= item < self.item_embeddings.size(0)]
            if valid_history:
                profile = self.item_embeddings[valid_history].mean(dim=0)
                profile = F.normalize(profile.unsqueeze(0), dim=1).squeeze(0)
                scores = self.item_embeddings @ profile
                scores = scores + 0.05 * self.item_popularity
            else:
                scores = self.item_popularity.clone()
        else:
            scores = self.item_popularity.clone()

        for item_id in set(history):
            if 0 <= item_id < scores.size(0):
                scores[item_id] = -1e9
        return scores

    def _recommend_internal(self, history: list[int], top_k: int) -> tuple[list[int], list[float]]:
        scores = self._compute_scores(history)
        valid_top_k = min(max(1, top_k), scores.size(0))
        top_scores, top_items = torch.topk(scores, valid_top_k)
        items = top_items.tolist()
        values = [round(float(score), 6) for score in top_scores.tolist()]
        return items, values

    def recommend(self, user_history: list[Any], top_k: int = 10) -> dict[str, Any]:
        history = self.mapper.validate_user_history(user_history)
        started = time.perf_counter()
        items, scores = self._recommend_internal(history, top_k)
        latency_ms = round((time.perf_counter() - started) * 1000, 3)
        return {
            "latency_ms": latency_ms,
            "history": history,
            "recommendations": self.mapper.format_recommendations(items, scores),
            "mode": "checkpoint-live",
            "uses_item_embeddings": self.item_embeddings is not None,
        }

    def measure_sample_latency(self, runs: int = 5, top_k: int = 10) -> float | None:
        latencies: list[float] = []
        try:
            for _ in range(max(1, runs)):
                started = time.perf_counter()
                self._recommend_internal(self.sample_history, top_k)
                latencies.append((time.perf_counter() - started) * 1000)
        except Exception:
            return None
        return round(sum(latencies) / len(latencies), 3) if latencies else None


class PMTCheckpointService:
    def __init__(self, spec: PMTProviderSpec):
        self.spec = spec
        self.config_defaults, self.supported_metrics = _load_config_defaults(spec.config_path)
        self.metrics_file = _latest_metrics_file(spec.metrics_dir)
        self.metrics_entries = _read_losses(self.metrics_file) if self.metrics_file else []
        checkpoint_files = sorted(spec.checkpoints_dir.glob("**/checkpoint.pth"))
        if not checkpoint_files:
            checkpoint_files = sorted(spec.checkpoints_dir.glob("**/*.pt"))
        if not checkpoint_files:
            raise FileNotFoundError(f"No PMT checkpoint found under {spec.checkpoints_dir}")
        self.checkpoint_path = checkpoint_files[0]
        self.state_dict = torch.load(self.checkpoint_path, map_location="cpu")
        if not isinstance(self.state_dict, (dict, OrderedDict)):
            raise TypeError(f"Unsupported PMT checkpoint format: {type(self.state_dict).__name__}")

    @property
    def model_name(self) -> str:
        return str(self.config_defaults.get("model") or "PMT-Former")

    @property
    def parameter_count(self) -> int:
        return sum(int(value.numel()) for value in self.state_dict.values() if isinstance(value, torch.Tensor))

    @property
    def final_metrics(self) -> dict[str, Any]:
        final_entry = next(
            (entry for entry in reversed(self.metrics_entries) if str(entry.get("epoch")) == "final" and isinstance(entry.get("metrics"), dict)),
            None,
        )
        if final_entry is not None:
            return dict(final_entry["metrics"])

        latest_numeric = next(
            (entry for entry in reversed(self.metrics_entries) if isinstance(entry.get("metrics"), dict)),
            None,
        )
        return dict(latest_numeric["metrics"]) if latest_numeric else {}

    @property
    def dataset_summary(self) -> dict[str, Any]:
        return {
            "data_name": self.spec.dataset_name,
            "task_name": self.config_defaults.get("task_name"),
            "seq_len": self.config_defaults.get("seq_len"),
            "label_len": self.config_defaults.get("label_len"),
            "pred_len": self.config_defaults.get("pred_len"),
            "feature_dim": self.config_defaults.get("enc_in"),
            "enc_in": self.config_defaults.get("enc_in"),
            "dec_in": self.config_defaults.get("dec_in"),
            "c_out": self.config_defaults.get("c_out"),
        }

    @property
    def training_summary(self) -> dict[str, Any]:
        curve = [
            {
                "epoch": int(entry["epoch"]),
                "loss": float(entry["train_loss"]),
            }
            for entry in self.metrics_entries
            if isinstance(entry.get("epoch"), int) and entry.get("train_loss") is not None
        ]
        train_losses = [point["loss"] for point in curve]
        return {
            "checkpoint_path": str(self.checkpoint_path),
            "epochs": self.config_defaults.get("train_epochs"),
            "batch_size": self.config_defaults.get("batch_size"),
            "learning_rate": self.config_defaults.get("learning_rate"),
            "d_model": self.config_defaults.get("d_model"),
            "n_heads": self.config_defaults.get("n_heads"),
            "e_layers": self.config_defaults.get("e_layers"),
            "d_layers": self.config_defaults.get("d_layers"),
            "d_ff": self.config_defaults.get("d_ff"),
            "train_loss_start": train_losses[0] if train_losses else None,
            "train_loss_end": train_losses[-1] if train_losses else None,
            "train_loss_curve": train_losses,
            "train_loss_epochs": [point["epoch"] for point in curve],
            "train_loss_points": curve,
        }

    @property
    def experiment_metrics(self) -> dict[str, Any]:
        metrics = dict(self.final_metrics)
        metrics["task_name"] = self.config_defaults.get("task_name")
        return metrics


class CVCheckpointService:
    def __init__(self, spec: CVProviderSpec):
        self.spec = spec
        if not spec.checkpoint_file.exists():
            raise FileNotFoundError(f"Checkpoint not found: {spec.checkpoint_file}")
        raw = torch.load(spec.checkpoint_file, map_location="cpu")
        if not isinstance(raw, (dict, OrderedDict)):
            raise TypeError(f"Unsupported CV checkpoint format: {type(raw).__name__}")
        self.state_dict = self._extract_state_dict(raw)
        self.class_names = self._load_class_names(spec.label_file)
        self.config = self._load_optional_json(spec.model_dir / "config.json")
        self.metrics = self._load_optional_json(spec.model_dir / "metrics.json")
        self.training_curve = self._load_optional_json(spec.model_dir / "training_curve.json")
        self.input_size = self._resolve_input_size()
        self.num_classes = self._resolve_num_classes()
        self._idx_to_name = {idx: name for idx, name in enumerate(self.class_names)}
        self._name_to_idx = {name: idx for idx, name in self._idx_to_name.items()}
        self.transform = transforms.Compose(
            [
                transforms.Resize((self.input_size, self.input_size)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )
        self.model = self._build_model()
        missing, unexpected = self.model.load_state_dict(self.state_dict, strict=False)
        if missing or unexpected:
            raise RuntimeError(
                f"State dict mismatch for {spec.provider}: missing={len(missing)} unexpected={len(unexpected)}"
            )
        self.model.eval()

    @staticmethod
    def _extract_state_dict(raw: dict[str, Any] | OrderedDict[str, Any]) -> dict[str, Any]:
        if "state_dict" in raw and isinstance(raw["state_dict"], (dict, OrderedDict)):
            return dict(raw["state_dict"])
        if "model_state_dict" in raw and isinstance(raw["model_state_dict"], (dict, OrderedDict)):
            return dict(raw["model_state_dict"])
        if "model" in raw and isinstance(raw["model"], (dict, OrderedDict)):
            return dict(raw["model"])
        return dict(raw)

    @staticmethod
    def _load_optional_json(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        data = _load_json(path)
        return data if isinstance(data, dict) else {}

    @staticmethod
    def _load_class_names(path: Path | None) -> list[str]:
        if path is None or not path.exists():
            return []
        suffix = path.suffix.lower()
        if suffix == ".json":
            data = _load_json(path)
            if isinstance(data, dict):
                def sort_key(item: tuple[Any, Any]) -> tuple[int, Any]:
                    key = str(item[0]).strip()
                    if key.isdigit():
                        return (0, int(key))
                    return (1, key)

                return [str(value) for _, value in sorted(data.items(), key=sort_key)]
            if isinstance(data, list):
                return [str(value) for value in data]
            return []
        if suffix == ".txt":
            return [line.strip() for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()]
        return []

    def _resolve_num_classes(self) -> int:
        if "classifier.2.weight" in self.state_dict:
            weight = self.state_dict["classifier.2.weight"]
            if isinstance(weight, torch.Tensor):
                return int(weight.shape[0])
        if "classifier.1.weight" in self.state_dict:
            weight = self.state_dict["classifier.1.weight"]
            if isinstance(weight, torch.Tensor):
                return int(weight.shape[0])
        cfg = self.config.get("num_classes")
        if isinstance(cfg, int) and cfg > 1:
            return cfg
        return len(self.class_names) if self.class_names else 2

    def _resolve_input_size(self) -> int:
        raw = self.config.get("input_size")
        if isinstance(raw, list) and raw:
            try:
                return int(raw[-1])
            except (TypeError, ValueError):
                pass
        hint = _parse_code_hint_value(self.spec.code_file, r"IMG_SIZE\s*=\s*([0-9]+)")
        return int(hint) if hint else 224

    def _build_model(self) -> torch.nn.Module:
        lower_name = self.spec.provider.lower()
        if "convnext" in lower_name:
            return models.convnext_tiny(weights=None, num_classes=self.num_classes)
        if "efficient" in lower_name:
            return models.efficientnet_b3(weights=None, num_classes=self.num_classes)
        raise ValueError(f"Unsupported CV architecture for provider: {self.spec.provider}")

    def label_for_index(self, idx: int) -> str:
        if idx in self._idx_to_name:
            return self._idx_to_name[idx]
        return str(idx)

    def index_for_label(self, label: str) -> int | None:
        text = str(label).strip()
        if not text:
            return None
        if text.isdigit():
            idx = int(text)
            return idx if 0 <= idx < self.num_classes else None
        return self._name_to_idx.get(text)

    @torch.inference_mode()
    def predict_image(self, image: Image.Image, top_k: int = 5, threshold: float = 0.0, tta: bool = False) -> dict[str, Any]:
        rgb = image.convert("RGB")
        base = self.transform(rgb).unsqueeze(0)
        logits = self.model(base)
        if tta:
            flipped = self.transform(rgb.transpose(Image.FLIP_LEFT_RIGHT)).unsqueeze(0)
            logits = (logits + self.model(flipped)) / 2.0
        probs = torch.softmax(logits, dim=1).squeeze(0)

        safe_top_k = max(1, min(int(top_k), self.num_classes))
        top_scores, top_indices = torch.topk(probs, safe_top_k)
        top_predictions = []
        for idx, score in zip(top_indices.tolist(), top_scores.tolist(), strict=False):
            top_predictions.append(
                {
                    "class_index": int(idx),
                    "class_name": self.label_for_index(int(idx)),
                    "score": float(score),
                }
            )

        best_idx = int(top_indices[0].item())
        best_score = float(top_scores[0].item())
        accepted = best_score >= float(threshold)
        predicted_idx = best_idx if accepted else -1
        predicted_name = self.label_for_index(best_idx) if accepted else "Unknown"
        return {
            "predicted_index": predicted_idx,
            "predicted_name": predicted_name,
            "confidence": best_score,
            "accepted": accepted,
            "topk": top_predictions,
        }

    @property
    def model_name(self) -> str:
        lower_name = self.spec.provider.lower()
        if "convnext" in lower_name:
            return "ConvNeXt-Tiny"
        if "efficient" in lower_name:
            return "EfficientNet-B3"
        return "ImageClassifier"

    @property
    def parameter_count(self) -> int:
        return sum(int(value.numel()) for value in self.state_dict.values() if isinstance(value, torch.Tensor))

    @property
    def dataset_summary(self) -> dict[str, Any]:
        return {
            "data_name": self.spec.dataset_name,
            "num_classes": self.num_classes,
            "label_source": str(self.spec.label_file) if self.spec.label_file else None,
            "image_size": self.input_size,
        }

    @property
    def training_summary(self) -> dict[str, Any]:
        curve_points: list[dict[str, Any]] = []
        epochs_raw = self.training_curve.get("epochs")
        losses_raw = self.training_curve.get("train_loss")
        if isinstance(epochs_raw, list) and isinstance(losses_raw, list):
            for epoch, loss in zip(epochs_raw, losses_raw, strict=False):
                try:
                    epoch_value = int(epoch)
                    loss_value = float(loss)
                except (TypeError, ValueError):
                    continue
                curve_points.append({"epoch": epoch_value, "loss": loss_value})
        train_losses = [point["loss"] for point in curve_points]
        return {
            "checkpoint_path": str(self.spec.checkpoint_file),
            "batch_size": self.config.get("batch_size") or _parse_code_hint_value(self.spec.code_file, r"BATCH_SIZE\s*=\s*([0-9]+)"),
            "learning_rate": self.config.get("learning_rate") or _parse_code_hint_value(self.spec.code_file, r"LEARNING_RATE\s*=\s*([0-9]*\.?[0-9]+)"),
            "epochs": self.config.get("epochs") or _parse_code_hint_value(self.spec.code_file, r"(?:EPOCHS|NUM_EPOCHS)\s*=\s*([0-9]+)"),
            "input_size": self.input_size,
            "train_loss_start": train_losses[0] if train_losses else None,
            "train_loss_end": train_losses[-1] if train_losses else None,
            "train_loss_curve": train_losses,
            "train_loss_epochs": [point["epoch"] for point in curve_points],
            "train_loss_points": curve_points,
        }

    @property
    def experiment_metrics(self) -> dict[str, Any]:
        metrics = dict(self.metrics)
        metrics["NUM_CLASSES"] = self.config.get("num_classes") or (len(self.class_names) if self.class_names else None)
        return metrics


def _prism_provider_error(spec: PrismProviderSpec, error: Exception) -> dict[str, Any]:
    return {
        "provider": spec.provider,
        "display_name": spec.display_name,
        "task_type": "sequential-recommendation",
        "model_family": "PRISM",
        "runtime": "checkpoint-live",
        "configured_target": str(spec.checkpoint_path),
        "status": "offline",
        "detail": f"模型加载失败: {error}",
        "model_name": None,
        "parameter_count": None,
        "sample_latency_ms": None,
        "sample_result_count": None,
        "experiment_metrics": None,
        "dataset_summary": None,
        "training_summary": None,
        "upstream": {"mode": "checkpoint-live", "error": str(error), "supports_recommendation": True},
    }


def _pmt_provider_error(spec: PMTProviderSpec, error: Exception) -> dict[str, Any]:
    return {
        "provider": spec.provider,
        "display_name": spec.display_name,
        "task_type": "time-series-forecast",
        "model_family": "PMT",
        "runtime": "checkpoint-live",
        "configured_target": str(spec.checkpoints_dir),
        "status": "offline",
        "detail": f"模型加载失败: {error}",
        "model_name": None,
        "parameter_count": None,
        "sample_latency_ms": None,
        "sample_result_count": None,
        "experiment_metrics": None,
        "dataset_summary": None,
        "training_summary": None,
        "upstream": {"mode": "checkpoint-live", "error": str(error), "supports_recommendation": False},
    }


def _cv_provider_error(spec: CVProviderSpec, error: Exception) -> dict[str, Any]:
    return {
        "provider": spec.provider,
        "display_name": spec.display_name,
        "task_type": "image-classification",
        "model_family": "CV",
        "runtime": "checkpoint-live",
        "configured_target": str(spec.checkpoint_file),
        "status": "offline",
        "detail": f"模型加载失败: {error}",
        "model_name": None,
        "parameter_count": None,
        "sample_latency_ms": None,
        "sample_result_count": None,
        "experiment_metrics": None,
        "dataset_summary": None,
        "training_summary": None,
        "upstream": {"mode": "checkpoint-live", "error": str(error), "supports_recommendation": False},
    }


@lru_cache(maxsize=1)
def _load_prism_services() -> dict[str, PrismCheckpointService]:
    return {spec.provider: PrismCheckpointService(spec) for spec in PRISM_PROVIDER_SPECS}


@lru_cache(maxsize=1)
def _load_pmt_services() -> dict[str, PMTCheckpointService]:
    return {spec.provider: PMTCheckpointService(spec) for spec in PMT_PROVIDER_SPECS}


@lru_cache(maxsize=1)
def _load_cv_services() -> dict[str, CVCheckpointService]:
    return {spec.provider: CVCheckpointService(spec) for spec in CV_PROVIDER_SPECS}


def list_provider_health() -> list[dict[str, Any]]:
    prism_services: dict[str, PrismCheckpointService]
    pmt_services: dict[str, PMTCheckpointService]
    cv_services: dict[str, CVCheckpointService]
    try:
        prism_services = _load_prism_services()
    except Exception:
        prism_services = {}
    try:
        pmt_services = _load_pmt_services()
    except Exception:
        pmt_services = {}
    try:
        cv_services = _load_cv_services()
    except Exception:
        cv_services = {}

    providers: list[dict[str, Any]] = []

    for spec in PRISM_PROVIDER_SPECS:
        service = prism_services.get(spec.provider)
        if service is None:
            try:
                service = PrismCheckpointService(spec)
            except Exception as exc:
                providers.append(_prism_provider_error(spec, exc))
                continue

        providers.append(
            {
                "provider": spec.provider,
                "display_name": spec.display_name,
                "task_type": "sequential-recommendation",
                "model_family": "PRISM",
                "runtime": "checkpoint-live",
                "configured_target": str(spec.checkpoint_path),
                "status": "online",
                "detail": "已加载真实 PRISM checkpoint；若缺少 item embeddings，则回退到 popularity 排序。",
                "model_name": service.model_name,
                "parameter_count": service.parameter_count,
                "sample_latency_ms": service.measure_sample_latency(runs=5),
                "sample_result_count": 10,
                "experiment_metrics": service.experiment_metrics,
                "dataset_summary": service.dataset_summary,
                "training_summary": service.training_summary,
                "upstream": {
                    "mode": "checkpoint-live",
                    "checkpoint_path": str(spec.checkpoint_path),
                    "dataset_dir": str(spec.dataset_dir),
                    "uses_item_embeddings": service.item_embeddings is not None,
                    "supports_recommendation": True,
                },
            }
        )

    for spec in PMT_PROVIDER_SPECS:
        service = pmt_services.get(spec.provider)
        if service is None:
            try:
                service = PMTCheckpointService(spec)
            except Exception as exc:
                providers.append(_pmt_provider_error(spec, exc))
                continue

        providers.append(
            {
                "provider": spec.provider,
                "display_name": spec.display_name,
                "task_type": "time-series-forecast",
                "model_family": "PMT",
                "runtime": "checkpoint-live",
                "configured_target": str(service.checkpoint_path),
                "status": "online",
                "detail": "已加载真实 PMT checkpoint、训练指标与配置参数，展示以时序预测指标为主。",
                "model_name": service.model_name,
                "parameter_count": service.parameter_count,
                "sample_latency_ms": None,
                "sample_result_count": None,
                "experiment_metrics": service.experiment_metrics,
                "dataset_summary": service.dataset_summary,
                "training_summary": service.training_summary,
                "upstream": {
                    "mode": "checkpoint-live",
                    "checkpoint_path": str(service.checkpoint_path),
                    "metrics_file": str(service.metrics_file) if service.metrics_file else None,
                    "config_path": str(spec.config_path),
                    "supports_recommendation": False,
                    "supported_metrics": service.supported_metrics,
                },
            }
        )

    for spec in CV_PROVIDER_SPECS:
        service = cv_services.get(spec.provider)
        if service is None:
            try:
                service = CVCheckpointService(spec)
            except Exception as exc:
                providers.append(_cv_provider_error(spec, exc))
                continue

        providers.append(
            {
                "provider": spec.provider,
                "display_name": spec.display_name,
                "task_type": "image-classification",
                "model_family": "CV",
                "runtime": "checkpoint-live",
                "configured_target": str(spec.checkpoint_file),
                "status": "online",
                "detail": "已加载图像分类 checkpoint 与标签映射，支持展示参数规模与类别规模。",
                "model_name": service.model_name,
                "parameter_count": service.parameter_count,
                "sample_latency_ms": None,
                "sample_result_count": None,
                "experiment_metrics": service.experiment_metrics,
                "dataset_summary": service.dataset_summary,
                "training_summary": service.training_summary,
                "upstream": {
                    "mode": "checkpoint-live",
                    "checkpoint_path": str(spec.checkpoint_file),
                    "label_file": str(spec.label_file) if spec.label_file else None,
                    "supports_recommendation": False,
                },
            }
        )

    return providers


def get_dashboard() -> dict[str, Any]:
    providers = list_provider_health()
    latencies = [item["sample_latency_ms"] for item in providers if item["sample_latency_ms"] is not None]
    parameters = [item["parameter_count"] for item in providers if item["parameter_count"] is not None]

    system_summary = {
        "torch_version": getattr(torch, "__version__", "unknown"),
        "cuda_available": bool(torch.cuda.is_available()),
        "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
    }

    return {
        "total_models": len(providers),
        "online_models": sum(1 for item in providers if item["status"] == "online"),
        "average_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else None,
        "total_parameters": sum(parameters) if parameters else None,
        "system_summary": system_summary,
        "providers": providers,
    }


def _parse_labels_text(lines: str | None) -> dict[str, str]:
    if not lines:
        return {}
    mapping: dict[str, str] = {}
    for raw in lines.splitlines():
        text = raw.strip()
        if not text or text.startswith("#"):
            continue
        if "," in text:
            name, label = text.split(",", 1)
        elif "\t" in text:
            name, label = text.split("\t", 1)
        else:
            continue
        mapping[name.strip()] = label.strip()
    return mapping


def _safe_image_name(name: str) -> str:
    normalized = name.replace("\\", "/").split("/")[-1]
    return normalized.strip()


def parse_cv_zip_dataset(zip_source: Path | bytes) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for image in iter_zip_image_entries(zip_source, include_bytes=True, max_items=MAX_CV_EVAL_IMAGES):
        filename = str(image["path"])
        samples.append(
            {
                "name": _safe_image_name(filename),
                "path": filename,
                "bytes": image["bytes"],
                "true_label": image.get("label"),
            }
        )
    return samples


def evaluate_cv(
    provider: str,
    samples: list[dict[str, Any]],
    top_k: int,
    threshold: float,
    tta: bool,
    progress_callback: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    services = _load_cv_services()
    service = services.get(provider)
    if service is None:
        raise KeyError(provider)

    safe_top_k = max(1, min(int(top_k), 20))
    safe_threshold = max(0.0, min(float(threshold), 1.0))

    predictions: list[dict[str, Any]] = []
    y_true: list[int] = []
    y_pred: list[int] = []
    top5_hits = 0
    error_samples: list[dict[str, Any]] = []
    started = time.perf_counter()

    capped_samples = samples[:MAX_CV_EVAL_IMAGES]
    total_samples = len(capped_samples)
    if progress_callback is not None:
        progress_callback(0, total_samples)

    for idx, sample in enumerate(capped_samples, start=1):
        try:
            image = Image.open(io.BytesIO(sample["bytes"]))
        except Exception:
            if progress_callback is not None:
                progress_callback(idx, total_samples)
            continue
        pred = service.predict_image(image, top_k=safe_top_k, threshold=safe_threshold, tta=tta)
        true_label = sample.get("true_label")
        true_idx = service.index_for_label(str(true_label)) if true_label is not None else None
        top_indices = [int(item["class_index"]) for item in pred["topk"]]
        if true_idx is not None:
            y_true.append(true_idx)
            y_pred.append(int(pred["predicted_index"]))
            if true_idx in top_indices[: min(5, len(top_indices))]:
                top5_hits += 1
            if int(pred["predicted_index"]) != true_idx:
                error_samples.append(
                    {
                        "file_name": sample["name"],
                        "true_label": service.label_for_index(true_idx),
                        "pred_label": pred["predicted_name"],
                        "confidence": pred["confidence"],
                    }
                )

        predictions.append(
            {
                "file_name": sample["name"],
                "path": sample.get("path"),
                "true_label": str(true_label) if true_label is not None else None,
                "pred_label": pred["predicted_name"],
                "pred_index": int(pred["predicted_index"]),
                "confidence": float(pred["confidence"]),
                "accepted": bool(pred["accepted"]),
                "topk": pred["topk"],
            }
        )
        if progress_callback is not None:
            progress_callback(idx, total_samples)

    latency_ms = round((time.perf_counter() - started) * 1000, 3)
    metrics: dict[str, Any] = {}
    confusion: dict[str, Any] = {"labels": [], "matrix": []}
    per_class_accuracy: list[dict[str, Any]] = []

    if y_true:
        valid_pairs = [(t, p) for t, p in zip(y_true, y_pred, strict=False) if p >= 0]
        y_true_valid = [item[0] for item in valid_pairs]
        y_pred_valid = [item[1] for item in valid_pairs]
        eval_count = len(y_true)
        top1 = sum(1 for t, p in zip(y_true, y_pred, strict=False) if t == p) / max(1, eval_count)
        top5 = top5_hits / max(1, eval_count)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_true_valid if y_true_valid else y_true,
            y_pred_valid if y_pred_valid else y_pred,
            average="macro",
            zero_division=0,
        )
        metrics = {
            "top1_acc": round(top1, 6),
            "top5_acc": round(top5, 6),
            "precision_macro": round(float(precision), 6),
            "recall_macro": round(float(recall), 6),
            "f1_macro": round(float(f1), 6),
            "eval_samples": eval_count,
            "accepted_ratio": round(sum(1 for p in y_pred if p >= 0) / max(1, len(y_pred)), 6),
        }

        class_ids = sorted(set(y_true + [p for p in y_pred if p >= 0]))
        if len(class_ids) > 40:
            class_ids = class_ids[:40]
        index_map = {cid: idx for idx, cid in enumerate(class_ids)}
        matrix = [[0 for _ in class_ids] for _ in class_ids]
        class_total = {cid: 0 for cid in class_ids}
        class_correct = {cid: 0 for cid in class_ids}
        for true_idx, pred_idx in zip(y_true, y_pred, strict=False):
            if true_idx not in index_map or pred_idx not in index_map:
                continue
            ti = index_map[true_idx]
            pi = index_map[pred_idx]
            matrix[ti][pi] += 1
            class_total[true_idx] += 1
            if true_idx == pred_idx:
                class_correct[true_idx] += 1

        confusion = {
            "labels": [service.label_for_index(cid) for cid in class_ids],
            "matrix": matrix,
        }
        per_class_accuracy = [
            {
                "class_name": service.label_for_index(cid),
                "accuracy": round(class_correct[cid] / max(1, class_total[cid]), 6),
                "correct": int(class_correct[cid]),
                "total": int(class_total[cid]),
            }
            for cid in class_ids
        ]
        per_class_accuracy.sort(key=lambda item: item["accuracy"], reverse=True)

    return {
        "provider": provider,
        "model_name": service.model_name,
        "parameters": {
            "top_k": safe_top_k,
            "threshold": safe_threshold,
            "tta": bool(tta),
            "input_size": service.input_size,
        },
        "summary": {
            "total_uploaded": len(samples),
            "processed": len(predictions),
            "latency_ms": latency_ms,
        },
        "metrics": metrics,
        "confusion_matrix": confusion,
        "per_class_accuracy": per_class_accuracy,
        "error_samples": error_samples[:200],
        "predictions": predictions[:200],
    }


def recommend(provider: str, user_id: str | None, user_history: list[int], top_k: int) -> dict[str, Any]:
    services = _load_prism_services()
    service = services.get(provider)
    if service is None:
        raise KeyError(provider)

    result = service.recommend(user_history, top_k=top_k)
    return {
        "provider": provider,
        "user_id": user_id,
        "latency_ms": result["latency_ms"],
        "recommendations": result["recommendations"],
        "upstream": {
            "mode": result["mode"],
            "checkpoint_path": str(service.spec.checkpoint_path),
            "uses_item_embeddings": result["uses_item_embeddings"],
            "validated_history": result["history"],
        },
    }


def sensitivity(provider: str, user_id: str | None, user_history: list[int], top_k: int, threshold: float, pred_len: int | None) -> dict[str, Any]:
    safe_threshold = max(0.0, min(1.0, float(threshold)))
    safe_top_k = max(1, int(top_k))

    prism_services = _load_prism_services()
    if provider in prism_services:
        service = prism_services[provider]
        result = service.recommend(user_history, top_k=safe_top_k)
        filtered = [item for item in result["recommendations"] if item.get("score") is not None and float(item["score"]) >= safe_threshold]
        kept_scores = [float(item["score"]) for item in filtered if item.get("score") is not None]
        return {
            "provider": provider,
            "user_id": user_id,
            "task_type": "sequential-recommendation",
            "parameters": {"top_k": safe_top_k, "threshold": safe_threshold, "pred_len": pred_len},
            "metrics": {
                "kept_count": len(filtered),
                "kept_ratio": round(len(filtered) / max(1, len(result["recommendations"])), 4),
                "avg_score": round(sum(kept_scores) / len(kept_scores), 6) if kept_scores else None,
                "latency_ms": result["latency_ms"],
            },
            "recommendations": filtered,
            "upstream": {
                "mode": "live-sensitivity",
                "checkpoint_path": str(service.spec.checkpoint_path),
                "validated_history": result["history"],
            },
        }

    pmt_services = _load_pmt_services()
    if provider in pmt_services:
        service = pmt_services[provider]
        baseline = service.final_metrics
        base_pred_len = int(service.dataset_summary.get("pred_len") or 96)
        target_pred_len = int(pred_len or base_pred_len)
        horizon_factor = max(0.5, min(3.0, (target_pred_len / max(1, base_pred_len)) ** 0.5))
        threshold_factor = 1.0 + safe_threshold * 0.15
        mae = baseline.get("MAE")
        rmse = baseline.get("RMSE")
        mape = baseline.get("MAPE")
        return {
            "provider": provider,
            "user_id": user_id,
            "task_type": "time-series-forecast",
            "parameters": {"top_k": safe_top_k, "threshold": safe_threshold, "pred_len": target_pred_len},
            "metrics": {
                "mae_est": round(float(mae) * horizon_factor * threshold_factor, 6) if mae is not None else None,
                "rmse_est": round(float(rmse) * horizon_factor * threshold_factor, 6) if rmse is not None else None,
                "mape_est": round(float(mape) * horizon_factor * threshold_factor, 6) if mape is not None else None,
                "base_pred_len": base_pred_len,
            },
            "recommendations": [],
            "upstream": {
                "mode": "estimate-sensitivity",
                "checkpoint_path": str(service.checkpoint_path),
                "note": "预测窗口与阈值对误差影响的在线估计，用于交互敏感性演示。",
            },
        }

    raise KeyError(provider)
