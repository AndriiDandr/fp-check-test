"""Мінімальні тести з умови лабораторної для базового завдання (замовлення)."""

from copy import deepcopy
from typing import Callable

import pytest

from core import (
    Order,
    make_processor,
    order_subtotal,
    process_orders_pure,
    with_total,
)


def test_referential_transparency(sample_orders: list[Order]) -> None:
    """Той самий вхід → той самий вихід."""
    args = {"min_total": 100, "discount": 0.1, "tax_rate": 0.2}
    r1 = process_orders_pure(sample_orders, **args)
    r2 = process_orders_pure(sample_orders, **args)
    assert r1 == r2


def test_no_mutation(sample_orders: list[Order]) -> None:
    """Вхідні замовлення не змінюються."""
    original = deepcopy(sample_orders)
    process_orders_pure(sample_orders, min_total=0, discount=0.0, tax_rate=0.0)
    assert sample_orders == original


def test_callable_policies(sample_orders: list[Order]) -> None:
    """Політики з Callable дають правильний revenue."""

    def accept(s: float) -> bool:
        return s >= 50

    def apply_discount(s: float) -> float:
        return s * 0.9

    def apply_tax(s: float) -> float:
        return s * 1.2

    discount: Callable[[float], float] = apply_discount
    tax: Callable[[float], float] = apply_tax
    processor = make_processor(accept=accept, apply_discount=discount, apply_tax=tax)
    result = processor(sample_orders)
    assert result["count"] == 2
    assert result["revenue"] == pytest.approx((120.0 + 90.0) * 0.9 * 1.2)


def test_process_orders_pure_values(sample_orders: list[Order]) -> None:
    """Відбираються оплачені замовлення з сумою від min_total."""
    result = process_orders_pure(
        sample_orders, min_total=100, discount=0.1, tax_rate=0.2
    )
    orders = result["orders"]
    assert isinstance(orders, list)
    assert [o["id"] for o in orders] == [1]
    assert result["revenue"] == pytest.approx(120.0 * 0.9 * 1.2)


def test_with_total_returns_new_order(sample_orders: list[Order]) -> None:
    """with_total створює новий словник, не чіпаючи вхідний."""
    order = sample_orders[0]
    new_order = with_total(order, order_subtotal(order))
    assert new_order is not order
    assert new_order["total"] == pytest.approx(120.0)
    assert "total" not in order
