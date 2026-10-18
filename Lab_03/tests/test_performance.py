"""Порівняння часу до/після переходу на незмінні структури (без зовнішніх плагінів)."""

from collections.abc import Callable
from time import perf_counter
from typing import Any

from core import add_tag, change_price, reorder_cost, restock
from model import StockRecord, make_record
from mutable_model import (
    add_tag_in_place,
    change_price_in_place,
    make_mutable_record,
    restock_in_place,
)

OPERATIONS = 2_000


def measure(fn: Callable[[], object], repeat: int = 5) -> float:
    """Повертає найкращий час виконання функції у секундах."""
    timings = []
    for _ in range(repeat):
        start = perf_counter()
        fn()
        timings.append(perf_counter() - start)
    return min(timings)


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


def test_before_mutable_operations() -> None:
    """Час ДО: мутабельна модель дає правильний результат."""
    result = mutable_workload()
    assert result["quantity"] == OPERATIONS
    assert len(result["movements"]) == OPERATIONS


def test_after_immutable_operations() -> None:
    """Час ПІСЛЯ: незмінна модель дає той самий результат."""
    result = immutable_workload()
    mutable = mutable_workload()
    assert result.quantity == mutable["quantity"]
    assert result.product.price == mutable["product"]["price"]
    assert result.product.tags == frozenset(mutable["product"]["tags"])
    assert len(result.movements) == OPERATIONS


def test_compare_time_before_and_after() -> None:
    """Порівняння часу: незмінна версія повільніша, але в межах мілісекунд."""
    before = measure(mutable_workload)
    after = measure(immutable_workload)
    print(f"\nbefore (mutable): {before * 1000:.2f} ms")
    print(f"after (immutable): {after * 1000:.2f} ms")
    print(f"ratio: {after / before:.1f}x")
    assert before > 0
    assert after < 1.0


def test_lru_cache_speeds_up_repeated_calls() -> None:
    """Повторний виклик reorder_cost береться з кешу."""
    record = make_record(
        sku="A1", name="Item", price=10.0, category="misc", quantity=1, min_quantity=50
    )
    reorder_cost.cache_clear()

    def cached_calls() -> None:
        """10000 викликів з кешем."""
        for _ in range(10_000):
            reorder_cost(record)

    def uncached_calls() -> None:
        """10000 викликів без кешу."""
        for _ in range(10_000):
            reorder_cost.__wrapped__(record)

    cached = measure(cached_calls)
    uncached = measure(uncached_calls)
    print(f"\nlru_cache: {cached * 1000:.2f} ms, без кешу: {uncached * 1000:.2f} ms")
    assert reorder_cost.cache_info().hits > 0


def test_stock_value_benchmark() -> None:
    """Обчислення вартості залишку незмінного запису."""
    record = make_record(
        sku="A1", name="Item", price=10.0, category="misc", quantity=7, min_quantity=5
    )

    def many_calls() -> None:
        """10000 обчислень вартості."""
        for _ in range(10_000):
            record.stock_value()

    assert record.stock_value() == 70.0
    assert measure(many_calls) < 1.0
