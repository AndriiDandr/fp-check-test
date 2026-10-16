"""Property-based тести (Hypothesis): інваріанти чистого ядра."""

import sys
from copy import deepcopy
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import Item, cart_subtotal, process_cart_pure

items_strategy = st.lists(
    st.fixed_dictionaries(
        {
            "name": st.text(min_size=1, max_size=10),
            "price": st.floats(min_value=0, max_value=10_000, allow_nan=False),
            "qty": st.integers(min_value=0, max_value=100),
            "category": st.sampled_from(["books", "food", "electronics", "toys"]),
        }
    ),
    max_size=20,
)
rates_strategy = st.dictionaries(
    st.sampled_from(["books", "food", "electronics"]),
    st.floats(min_value=0, max_value=1, allow_nan=False),
)


@given(items=items_strategy, rates=rates_strategy)
def test_property_no_mutation(items: list[Item], rates: dict[str, float]) -> None:
    """Для будь-якого кошика вхідні дані не змінюються."""
    original = deepcopy(items)
    process_cart_pure(items, category_rates=rates, coupon_percent=10, vat_rate=0.2)
    assert items == original


@given(items=items_strategy, rates=rates_strategy)
def test_property_referential_transparency(
    items: list[Item], rates: dict[str, float]
) -> None:
    """Повторний виклик з тими самими аргументами дає той самий результат."""
    first = process_cart_pure(
        items, category_rates=rates, coupon_percent=5, vat_rate=0.2
    )
    second = process_cart_pure(
        items, category_rates=rates, coupon_percent=5, vat_rate=0.2
    )
    assert first == second


@given(items=items_strategy, rates=rates_strategy)
def test_property_discounts_never_increase_total(
    items: list[Item], rates: dict[str, float]
) -> None:
    """Знижки не збільшують суму, а без ПДВ підсумок не перевищує subtotal."""
    r = process_cart_pure(items, category_rates=rates, coupon_percent=10, vat_rate=0)
    assert r["total"] <= r["subtotal"] + 1e-6
    assert r["category_discount"] >= -1e-6
    assert r["subtotal"] == pytest.approx(cart_subtotal(items))
