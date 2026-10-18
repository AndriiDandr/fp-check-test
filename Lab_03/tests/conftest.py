"""Спільні фікстури тестів і фабрики контрольних копій."""

import sys
from collections.abc import Callable
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from model import StockRecord, make_record


def build_record() -> StockRecord:
    """Будує новий запис, рівний фікстурі record."""
    return make_record(
        sku="LAP-01",
        name="Laptop",
        price=1000.0,
        category="electronics",
        quantity=4,
        min_quantity=5,
        tags=("new",),
        supplier={"name": "TechImport", "city": "Kyiv"},
    )


def build_records() -> tuple[StockRecord, ...]:
    """Будує новий кортеж, рівний фікстурі records."""
    return (
        build_record(),
        make_record(
            sku="BOO-02",
            name="Book",
            price=200.0,
            category="books",
            quantity=10,
            min_quantity=3,
            tags=("bestseller",),
        ),
        make_record(
            sku="TSH-03",
            name="T-shirt",
            price=50.0,
            category="clothes",
            quantity=1,
            min_quantity=4,
        ),
    )


@pytest.fixture
def record() -> StockRecord:
    """Один запис складу."""
    return build_record()


@pytest.fixture
def records() -> tuple[StockRecord, ...]:
    """Кортеж із трьох записів складу."""
    return build_records()


@pytest.fixture
def fresh_record() -> Callable[[], StockRecord]:
    """Фабрика нових записів, рівних record (deepcopy не працює з MappingProxyType)."""
    return build_record


@pytest.fixture
def fresh_records() -> Callable[[], tuple[StockRecord, ...]]:
    """Фабрика нових кортежів, рівних records."""
    return build_records
