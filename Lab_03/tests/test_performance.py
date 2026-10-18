"""Вимірювання до/після переходу на незмінні структури (pytest-benchmark)."""

from typing import Any

from pytest_benchmark.fixture import BenchmarkFixture

from core import add_tag, change_price, reorder_cost, restock
from model import StockRecord, make_record
from mutable_model import (
    add_tag_in_place,
    change_price_in_place,
    make_mutable_record,
    restock_in_place,
)

OPERATIONS = 2_000


def immutable_workload() -> StockRecord:
    """2000 pure-оновлень незмінного запису."""
    record = make_record(
        sku="A1", name="Item", price=10.0, category="misc", quantity=0, min_quantity=5
    )
    for i in range(OPERATIONS):
        record = restock(record, 1)
        record = change_price(record, 10.0 + i % 7)
        record = add_tag(record, f"t{i % 5}")
    return record


def mutable_workload() -> dict[str, Any]:
    """2000 in-place оновлень мутабельного запису."""
    record = make_mutable_record("A1", 10.0, 0, 5)
    for i in range(OPERATIONS):
        restock_in_place(record, 1)
        change_price_in_place(record, 10.0 + i % 7)
        add_tag_in_place(record, f"t{i % 5}")
    return record


def test_before_mutable_operations(benchmark: BenchmarkFixture) -> None:
    """Час ДО: мутабельна модель."""
    result = benchmark(mutable_workload)
    assert result["quantity"] == OPERATIONS


def test_after_immutable_operations(benchmark: BenchmarkFixture) -> None:
    """Час ПІСЛЯ: незмінна модель."""
    result = benchmark(immutable_workload)
    assert result.quantity == OPERATIONS
    assert len(result.movements) == OPERATIONS


def test_reorder_cost_without_cache(benchmark: BenchmarkFixture) -> None:
    """reorder_cost без lru_cache."""
    record = make_record(
        sku="A1", name="Item", price=10.0, category="misc", quantity=1, min_quantity=50
    )
    benchmark(reorder_cost.__wrapped__, record)


def test_reorder_cost_with_cache(benchmark: BenchmarkFixture) -> None:
    """reorder_cost з lru_cache."""
    record = make_record(
        sku="A1", name="Item", price=10.0, category="misc", quantity=1, min_quantity=50
    )
    reorder_cost(record)
    benchmark(reorder_cost, record)


def test_stock_value_benchmark(benchmark: BenchmarkFixture) -> None:
    """Бенчмарк обчислення вартості залишку незмінного запису."""
    record = make_record(
        sku="A1", name="Item", price=10.0, category="misc", quantity=7, min_quantity=5
    )
    assert benchmark(record.stock_value) == 70.0
