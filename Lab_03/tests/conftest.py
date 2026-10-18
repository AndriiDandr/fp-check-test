"""Спільні фікстури тестів."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from factories import build_record, build_records
from model import StockRecord


@pytest.fixture
def record() -> StockRecord:
    """Один запис складу."""
    return build_record()


@pytest.fixture
def records() -> tuple[StockRecord, ...]:
    """Кортеж із трьох записів складу."""
    return build_records()
