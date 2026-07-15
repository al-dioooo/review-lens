from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources

from reviewlens.exceptions import ConfigurationError


@lru_cache(maxsize=1)
def _canonical_slang_items() -> tuple[tuple[str, str], ...]:
    resource = resources.files("reviewlens.resources").joinpath("slang_id.json")
    payload = json.loads(resource.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in payload.items()
    ):
        raise ConfigurationError("The packaged Indonesian slang map is invalid.")
    return tuple(sorted(payload.items()))


def load_slang_map(
    extra_slang: tuple[tuple[str, str], ...] = (),
) -> dict[str, str]:
    slang = dict(_canonical_slang_items())
    for key, value in extra_slang:
        if not key.strip() or not value.strip():
            raise ConfigurationError("Slang keys and values must not be empty.")
        slang[key] = value
    return slang
