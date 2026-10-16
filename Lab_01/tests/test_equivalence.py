"""Еквівалентність: функціональна версія дає той самий результат, що й імперативна."""

import sys
from copy import deepcopy
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import Item, Order, process_cart_pure, process_orders_pure
from starter_imperative import process_cart, process_orders


def test_matches_imperative_orders(
    sample_orders: list[Order], capsys: pytest.CaptureFixture[str]
) -> None:
    """process_orders_pure збігається зі стартовим process_orders."""
    expected = process_orders(deepcopy(sample_orders), min_total=100, discount=0.1)
    capsys.readouterr()
    actual = process_orders_pure(
        sample_orders, min_total=100, discount=0.1, tax_rate=0.2
    )
    assert actual == expected


def test_matches_imperative_cart(
    sample_cart: list[Item], capsys: pytest.CaptureFixture[str]
) -> None:
    """process_cart_pure дає ті самі суми, що й імперативний process_cart."""
    expected = process_cart(deepcopy(sample_cart))
    assert "Processing item:" in capsys.readouterr().out
    actual = process_cart_pure(
        sample_cart,
        category_rates={"electronics": 0.1, "books": 0.2},
        coupon_percent=10,
        vat_rate=0.2,
    )
    assert actual["subtotal"] == pytest.approx(expected["subtotal"])
    assert actual["after_coupon"] == pytest.approx(expected["after_coupon"])
    assert actual["total"] == pytest.approx(expected["total"])


def test_imperative_version_mutates_but_pure_does_not(
    sample_cart: list[Item], capsys: pytest.CaptureFixture[str]
) -> None:
    """Імперативна версія мутує вхід, чиста — ні (саме це ми й виправили)."""
    imperative_input = deepcopy(sample_cart)
    process_cart(imperative_input)
    capsys.readouterr()
    assert imperative_input != sample_cart
    original = deepcopy(sample_cart)
    process_cart_pure(sample_cart, category_rates={}, coupon_percent=0, vat_rate=0)
    assert sample_cart == original
