"""Оболонка побічних ефектів: читання кошика, час і друк звіту.

Усі обчислення делегуються чистому ядру ``core``; тут лише I/O.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

from core import (
    Item,
    NowFn,
    Receipt,
    accept_positive_qty,
    compose,
    make_cart_processor,
    make_category_discount,
    make_exclude_category,
    make_fixed_coupon,
    make_percent_coupon,
    make_vat,
    stamp_total,
)


def load_cart(path: Path) -> list[Item]:
    """Читає кошик із JSON-файлу."""
    with path.open(encoding="utf-8") as f:
        data: list[Item] = json.load(f)
    return data


def format_report(receipt: Receipt, stamped_at: float) -> str:
    """Формує текст чека з готового результату (без друку)."""
    header = (
        f"{'Товар':<22}{'Категорія':<13}{'Ціна':>9}{'К-сть':>7}"
        f"{'Сума':>10}{'Знижка':>8}{'Після':>10}"
    )
    rows = [
        f"{p['name']:<22}{p['category']:<13}{p['price']:>9.2f}{p['qty']:>7}"
        f"{p['line_total']:>10.2f}{p['discount_rate'] * 100:>7.0f}%"
        f"{p['discounted_total']:>10.2f}"
        for p in receipt["items"]
    ]
    stamp = datetime.fromtimestamp(stamped_at).astimezone()
    totals = [
        f"{'Subtotal:':<24}{receipt['subtotal']:>12.2f}",
        f"{'Категоріальна знижка:':<24}{-receipt['category_discount']:>12.2f}",
        f"{'Купон:':<24}{-receipt['coupon_discount']:>12.2f}",
        f"{'ПДВ:':<24}{receipt['vat']:>+12.2f}",
        f"{'До сплати:':<24}{receipt['total']:>12.2f}",
        f"Час розрахунку: {stamp:%Y-%m-%d %H:%M:%S}",
    ]
    separator = "-" * 79
    return "\n".join([header, separator, *rows, separator, *totals])


def render_report(result: Receipt, now: NowFn = time.time) -> None:
    """Оболонка виводу: лише споживає чистий результат і друкує чек."""
    _, stamped_at = stamp_total(result["total"], now)
    print(format_report(result, stamped_at))


def run(
    cart: list[Item],
    *,
    category_rates: dict[str, float],
    coupon_percent: float,
    vat_rate: float,
) -> None:
    """Рахує кошик за двома наборами політик і друкує чеки."""
    processor = make_cart_processor(
        accept=accept_positive_qty,
        category_discount=make_category_discount(category_rates),
        apply_coupon=make_percent_coupon(coupon_percent),
        apply_tax=make_vat(vat_rate),
    )
    print(f"=== Кошик: купон {coupon_percent:g}%, ПДВ {vat_rate:.0%} ===")
    render_report(processor(cart))

    combo_coupon = compose(
        make_fixed_coupon(100, min_amount=1000),
        make_percent_coupon(5),
    )
    alt = make_cart_processor(
        accept=make_exclude_category("food"),
        category_discount=make_category_discount({"electronics": 0.10}),
        apply_coupon=combo_coupon,
        apply_tax=make_vat(vat_rate),
    )
    print()
    print("=== Інша політика: без food, купон 5% + 100 грн від 1000 грн ===")
    render_report(alt(cart))


def main() -> None:
    """Точка входу: шлях до кошика можна передати аргументом."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    default_path = Path(__file__).with_name("cart.json")
    cart_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_path
    run(
        load_cart(cart_path),
        category_rates={"electronics": 0.05, "books": 0.10, "clothes": 0.15},
        coupon_percent=10,
        vat_rate=0.20,
    )


if __name__ == "__main__":
    main()
