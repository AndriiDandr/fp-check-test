"""Тести чистого ядра: референтна прозорість, відсутність мутацій, політики."""

from copy import deepcopy
from typing import Callable

import pytest

from core import (
    CartProcessor,
    Item,
    TaxFn,
    cart_subtotal,
    compose,
    identity,
    line_total,
    make_cart_processor,
    make_category_discount,
    make_fixed_coupon,
    make_multiplier,
    make_percent_coupon,
    make_vat,
    process_cart_pure,
    scale_prices,
    stamp_total,
    with_qty,
    without_category,
)

RATES = {"electronics": 0.1, "books": 0.2}
COUPON = 10
VAT = 0.2


def test_line_total_and_subtotal(sample_cart: list[Item]) -> None:
    """Сума позиції та кошика рахуються як ціна × кількість."""
    assert line_total(sample_cart[1]) == 400.0
    assert cart_subtotal(sample_cart) == 1000.0 + 400.0 + 150.0


def test_referential_transparency(sample_cart: list[Item]) -> None:
    """Той самий вхід дає той самий вихід."""
    r1 = process_cart_pure(
        sample_cart, category_rates=RATES, coupon_percent=COUPON, vat_rate=VAT
    )
    r2 = process_cart_pure(
        sample_cart, category_rates=RATES, coupon_percent=COUPON, vat_rate=VAT
    )
    assert r1 == r2


def test_no_mutation(sample_cart: list[Item]) -> None:
    """Вхідний кошик не змінюється, результат містить нові об'єкти."""
    original = deepcopy(sample_cart)
    receipt = process_cart_pure(
        sample_cart, category_rates=RATES, coupon_percent=COUPON, vat_rate=VAT
    )
    assert sample_cart == original
    assert all(
        p is not it for p, it in zip(receipt["items"], sample_cart[:3], strict=True)
    )
    with_qty(sample_cart[0], 7)
    without_category(sample_cart, "food")
    scale_prices(sample_cart, 2)
    assert sample_cart == original


def test_process_cart_pure_values(sample_cart: list[Item]) -> None:
    """Підсумки кошика обчислено правильно."""
    r = process_cart_pure(
        sample_cart, category_rates=RATES, coupon_percent=COUPON, vat_rate=VAT
    )
    after_category = 900.0 + 320.0 + 150.0
    assert len(r["items"]) == 3
    assert r["subtotal"] == pytest.approx(1550.0)
    assert r["after_category"] == pytest.approx(after_category)
    assert r["category_discount"] == pytest.approx(180.0)
    assert r["after_coupon"] == pytest.approx(after_category * 0.9)
    assert r["total"] == pytest.approx(after_category * 0.9 * 1.2)
    assert r["vat"] == pytest.approx(after_category * 0.9 * 0.2)


def test_callable_policies(sample_cart: list[Item]) -> None:
    """Передані Callable-політики застосовуються до кошика."""

    def apply_coupon(s: float) -> float:
        return s - 50

    def apply_tax(s: float) -> float:
        return s * 1.2

    coupon: Callable[[float], float] = apply_coupon
    tax: TaxFn = apply_tax
    discount: Callable[[Item], float] = make_category_discount({"books": 0.5})
    processor = make_cart_processor(
        accept=lambda it: it["qty"] > 0 and it["category"] != "food",
        category_discount=discount,
        apply_coupon=coupon,
        apply_tax=tax,
    )
    r = processor(sample_cart)
    assert [p["name"] for p in r["items"]] == ["Phone", "Book"]
    assert r["after_category"] == pytest.approx(1200.0)
    assert r["total"] == pytest.approx((1200.0 - 50) * 1.2)


def test_policies_are_swappable(sample_cart: list[Item]) -> None:
    """Заміна однієї політики змінює лише відповідну частину розрахунку."""

    def build(tax: TaxFn) -> CartProcessor:
        return make_cart_processor(
            accept=lambda it: it["qty"] > 0,
            category_discount=lambda _: 0.0,
            apply_coupon=identity,
            apply_tax=tax,
        )

    assert build(identity)(sample_cart)["total"] == pytest.approx(1550.0)
    assert build(make_vat(0.2))(sample_cart)["total"] == pytest.approx(1860.0)


def test_category_discount_factory() -> None:
    """Фабрика знижки повертає ставку за категорією або 0."""
    policy = make_category_discount(RATES)
    item: Item = {"name": "x", "price": 1.0, "qty": 1, "category": "books"}
    other: Item = {"name": "y", "price": 1.0, "qty": 1, "category": "toys"}
    assert policy(item) == pytest.approx(0.2)
    assert policy(other) == pytest.approx(0.0)


def test_coupons_and_compose() -> None:
    """Купони працюють окремо та в композиції."""
    fixed = make_fixed_coupon(100, min_amount=1000)
    assert fixed(999) == pytest.approx(999)
    assert fixed(1000) == pytest.approx(900)
    assert make_fixed_coupon(500)(300) == pytest.approx(0.0)
    combo = compose(fixed, make_percent_coupon(10))
    assert combo(2000) == pytest.approx(1700)
    assert combo(1000) == pytest.approx(900)


def test_make_multiplier() -> None:
    """Фабрика множників повертає налаштовані функції."""
    assert make_multiplier(3)(5) == 15
    assert list(map(make_multiplier(2), [1, 2, 3])) == [2, 4, 6]


def test_stamp_total_uses_injected_clock() -> None:
    """Час береться з переданої функції, а не з системного годинника."""
    assert stamp_total(10.0, lambda: 123.0) == (10.0, 123.0)


def test_empty_cart() -> None:
    """Порожній кошик дає нульові підсумки."""
    r = process_cart_pure([], category_rates={}, coupon_percent=0, vat_rate=VAT)
    assert r["items"] == []
    assert r["total"] == pytest.approx(0.0)
