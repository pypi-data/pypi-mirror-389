"""Validation utilities for leap-bundle directory validation."""

import json
import os
from pathlib import Path
from typing import Any, Callable, List, Optional, cast

MAX_FILE_SIZE_GB = 10.0
MAX_DIRECTORY_SIZE_GB = 10.0
MIN_DIRECTORY_SIZE_MB = 1.0


class ValidationError(Exception):
    """Exception raised when directory validation fails."""

    pass


def validate_safetensors_files_exist(directory_path: Path) -> None:
    """Check that one or more .safetensors files exist in the directory."""
    safetensors_files = [
        f
        for f in directory_path.glob("**/*.safetensors")
        if not any(part.startswith(".") for part in f.parts)
    ]
    if not safetensors_files:
        raise ValidationError("No .safetensors files found in directory")


def validate_file_sizes(
    directory_path: Path, max_size_gb: float = MAX_FILE_SIZE_GB
) -> None:
    """Check that each file is less than the specified size limit."""
    max_size_bytes = int(max_size_gb * 1024 * 1024 * 1024)

    for root, dirnames, filenames in os.walk(directory_path):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for filename in filenames:
            if filename.startswith("."):
                continue
            file_path = Path(root) / filename
            file_size = file_path.stat().st_size
            if file_size > max_size_bytes:
                file_size_gb = file_size / (1024 * 1024 * 1024)
                relative_path = file_path.relative_to(directory_path)
                raise ValidationError(
                    f"File {relative_path} is {file_size_gb:.1f}GB, "
                    f"which exceeds the {max_size_gb}GB limit"
                )


def validate_directory_size(
    directory_path: Path,
    max_size_gb: float = MAX_DIRECTORY_SIZE_GB,
    min_size_mb: float = MIN_DIRECTORY_SIZE_MB,
) -> None:
    """Check that the total directory size is within the specified limits."""
    max_size_bytes = int(max_size_gb * 1024 * 1024 * 1024)
    min_size_bytes = int(min_size_mb * 1024 * 1024)
    total_size = 0

    for root, dirnames, filenames in os.walk(directory_path):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for filename in filenames:
            if filename.startswith("."):
                continue
            file_path = Path(root) / filename
            total_size += file_path.stat().st_size

    if total_size > max_size_bytes:
        total_size_gb = total_size / (1024 * 1024 * 1024)
        raise ValidationError(
            f"Directory total size is {total_size_gb:.1f}GB, "
            f"exceeding the {max_size_gb}GB limit and unsupported by the bundle service for now"
        )

    if total_size < min_size_bytes:
        total_size_mb = total_size / (1024 * 1024)
        raise ValidationError(
            f"Directory total size is {total_size_mb:.1f}MB, "
            f"which is unlikely a valid model checkpoint"
        )


def validate_model_type(config_data: dict[str, Any]) -> None:
    """Check that config.json contains a valid model_type field."""

    model_type = config_data.get("model_type")
    if model_type is None:
        raise ValidationError(
            "The config.json file does not have the 'model_type' field. "
            "This means this model checkpoint is not supported by the bundle service. "
            "Please do not manually add this field. "
            "Doing so may temporarily bypass the validation, but the bundle processor will eventually fail."
        )


def validate_visual_model(config_data: dict[str, Any]) -> None:
    model_type = config_data.get("model_type")
    required_fields = ["text_config", "vision_config"]
    if model_type != "lfm2-vl":
        return

    missing_fields = [field for field in required_fields if field not in config_data]
    if missing_fields:
        raise ValidationError(
            f"The config.json file is missing required fields for visual models: {', '.join(missing_fields)}"
        )


def reject_audio_model(config_data: dict[str, Any]) -> None:
    audio_fields = ["preprocessor", "encoder", "lfm"]
    if all(field in config_data for field in audio_fields):
        raise ValidationError(
            "Audio models are currently not supported by the bundle service. It will be in a future release."
        )


VALIDATION_FUNCTIONS: List[Callable[[Path], None]] = [
    validate_safetensors_files_exist,
    validate_file_sizes,
    validate_directory_size,
]


CONFIG_VALIDATION_FUNCTIONS: List[Callable[[dict[str, Any]], None]] = [
    validate_visual_model,
    reject_audio_model,
    validate_model_type,
]


def validate_directory(directory_path: Path) -> None:
    """Run all validation checks on the directory."""
    for validation_func in VALIDATION_FUNCTIONS:
        validation_func(directory_path)
    validate_config(directory_path)


def validate_config(directory_path: Path) -> None:
    config_path = directory_path / "config.json"
    if not config_path.exists():
        raise ValidationError("No config.json found in directory.")
    validate_config_file(config_path)


def validate_config_file(config_path: Path) -> None:
    try:
        with open(config_path, encoding="utf-8") as f:
            config_data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in config.json: {e}") from e
    except Exception as e:
        raise ValidationError(f"Failed to read config.json: {e}") from e

    if not isinstance(config_data, dict):
        raise ValidationError("The config.json file must contain a JSON object")

    for validation_func in CONFIG_VALIDATION_FUNCTIONS:
        validation_func(config_data)


def get_model_type(directory_path: Path) -> Optional[str]:
    config_path = directory_path / "config.json"
    try:
        with open(config_path, encoding="utf-8") as f:
            config_data = json.load(f)
            return cast(Optional[str], config_data.get("model_type"))
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in config.json: {e}") from e
    except Exception as e:
        raise ValidationError(f"Failed to read config.json: {e}") from e
