"""Оболонка I/O: читає склад з JSON, виконує pure-оновлення і друкує таблиці."""

import json
import sys
from collections.abc import Sequence
from pathlib import Path

from core import (
    add_tag,
    apply_price_rule,
    change_price,
    index_by_sku,
    make_category_discount,
    reorder_cost,
    restock,
    ship,
    supplier_name,
    to_reorder,
    top_valuable,
    total_value,
    update_supplier,
)
from model import StockRecord, make_record


def load_records(path: Path) -> tuple[StockRecord, ...]:
    """Читає записи складу з JSON-файлу і робить їх незмінними."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    return tuple(make_record(**row) for row in raw)


def format_table(records: Sequence[StockRecord]) -> str:
    """Формує текст таблиці складу (без друку)."""
    header = f"{'SKU':<8}{'Товар':<17}{'Ціна':>10}{'К-сть':>7}{'Вартість':>12}  Теги"
    rows = [
        f"{r.product.sku:<8}{r.product.name:<17}{r.product.price:>10.2f}"
        f"{r.quantity:>7}{r.stock_value():>12.2f}  {', '.join(sorted(r.product.tags))}"
        for r in records
    ]
    return "\n".join([header, "-" * 70, *rows])


def main() -> None:
    """Точка входу: демонструє pure-оновлення складу."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(__file__).with_name("warehouse.json")
    )
    records = load_records(path)
    print("=== Початковий склад ===")
    print(format_table(records))
    print(f"Загальна вартість: {total_value(records):.2f}")

    by_sku = index_by_sku(records)
    laptop = restock(by_sku["LAP-01"], 6)
    laptop = add_tag(change_price(laptop, 23999.0), "promo")
    mouse = update_supplier(ship(by_sku["MOU-02"], 15), city="Одеса")
    updated = tuple(
        {"LAP-01": laptop, "MOU-02": mouse}.get(r.product.sku, r) for r in records
    )

    print("\n=== Після pure-оновлень ===")
    print(format_table(updated))
    print(f"Рухи LAP-01: {laptop.movements}")
    print(f"Постачальник MOU-02: {supplier_name(mouse.supplier)}, {mouse.supplier}")
    print(f"Оригінал LAP-01 не змінився: {by_sku['LAP-01'].quantity} шт.")

    print("\n=== Потребують дозамовлення ===")
    for r in to_reorder(updated):
        print(
            f"{r.product.sku}: {r.quantity} < {r.min_quantity}, дозамовлення на {reorder_cost(r):.2f}"
        )

    discounted = apply_price_rule(updated, make_category_discount({"books": 0.1}))
    print("\n=== Знижка 10% на книги (новий кортеж записів) ===")
    print(format_table(discounted))
    top = ", ".join(r.product.sku for r in top_valuable(updated, 2))
    print(f"Найдорожчі позиції: {top}")


if __name__ == "__main__":
    main()
