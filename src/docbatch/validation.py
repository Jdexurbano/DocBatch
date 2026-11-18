import math
import numbers
import unicodedata
from dataclasses import dataclass
from pathlib import Path

MEGABYTE_BYTES = 1024 * 1024
MAX_PART_SIZE_MB = 25.0
DEFAULT_MAX_SIZE_MB = MAX_PART_SIZE_MB
WINDOWS_INVALID_CHARACTERS = frozenset('\\/:*?"<>|')
RESERVED_DEVICE_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{number}" for number in range(1, 10)}
    | {f"LPT{number}" for number in range(1, 10)}
)


class PlanValidationError(Exception):
    def __init__(self, messages):
        self.messages = tuple(messages)
        super().__init__("; ".join(self.messages))


def normalize_batch_name(batch_name: str) -> str:
    return batch_name.strip().upper()


@dataclass(frozen=True)
class _ValidatedInputs:
    source: Path | None
    destination: Path | None
    batch_name: str
    max_size_mb: float | None
    errors: tuple[str, ...]


def _resolve_folder(value, label, errors):
    try:
        path = Path(value).resolve()
    except (TypeError, ValueError, OSError):
        errors.append(f"{label} path is invalid")
        return None
    if not path.exists():
        errors.append(f"{label} folder does not exist: {path}")
    elif not path.is_dir():
        errors.append(f"{label} path is not a folder: {path}")
    return path


def _path_key(path):
    return tuple(part.casefold() for part in path.parts)


def _validate_batch_name(batch_name, errors):
    if not isinstance(batch_name, str):
        errors.append("Batch name must be text")
        return ""
    normalized = normalize_batch_name(batch_name)
    if not normalized:
        errors.append("Batch name is required")
    invalid_characters = sorted(
        {character for character in batch_name if character in WINDOWS_INVALID_CHARACTERS}
    )
    if invalid_characters:
        errors.append(f"Batch name contains invalid characters: {' '.join(invalid_characters)}")
    if any(unicodedata.category(character) == "Cc" for character in batch_name):
        errors.append("Batch name contains control characters")
    if batch_name.endswith((".", " ")):
        errors.append("Batch name cannot end with a dot or space")
    if normalized.split(".", 1)[0].rstrip(" .") in RESERVED_DEVICE_NAMES:
        errors.append(f"Batch name is a reserved Windows device name: {normalized}")
    return normalized


def _validate_limit(max_size_mb, errors):
    if isinstance(max_size_mb, bool) or not isinstance(max_size_mb, numbers.Real):
        errors.append("Part-size limit must be a number")
        return None
    limit = float(max_size_mb)
    if not math.isfinite(limit):
        errors.append("Part-size limit must be a finite number")
        return None
    if limit <= 0:
        errors.append("Part-size limit must be greater than zero")
        return None
    if limit > MAX_PART_SIZE_MB:
        errors.append(f"Part-size limit cannot exceed {MAX_PART_SIZE_MB:g} MB")
        return None
    return limit


def _same_or_nested(source, destination):
    source_key = _path_key(source)
    destination_key = _path_key(destination)
    return (
        source_key == destination_key
        or source_key[: len(destination_key)] == destination_key
        or destination_key[: len(source_key)] == source_key
    )


def _validate_inputs(
    source: Path | str,
    destination: Path | str,
    batch_name: str,
    max_size_mb: float,
) -> _ValidatedInputs:
    errors = []
    normalized_name = _validate_batch_name(batch_name, errors)
    limit = _validate_limit(max_size_mb, errors)
    source_path = _resolve_folder(source, "Source", errors)
    destination_path = _resolve_folder(destination, "Destination", errors)

    if source_path is not None and destination_path is not None:
        if _same_or_nested(source_path, destination_path):
            errors.append(
                "Destination folder must be distinct from and not nested with "
                f"the Source folder: {source_path} / {destination_path}"
            )

    return _ValidatedInputs(
        source=source_path,
        destination=destination_path,
        batch_name=normalized_name,
        max_size_mb=limit,
        errors=tuple(errors),
    )
