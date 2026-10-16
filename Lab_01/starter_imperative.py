"""Стартовий імперативний фрагмент з умови (для порівняння, НЕ використовується).

Проблеми: глобал TAX_RATE, print усередині, мутації o, змішане обчислення та I/O.
Функціональна версія — ``core.process_orders_pure`` / ``core.make_processor``.
"""

from typing import Any

TAX_RATE = 0.2


def process_orders(
    orders: list[Any], min_total: float, discount: float
) -> dict[str, Any]:
    """Імперативна версія з побічними ефектами (оригінал з умови)."""
    valid = []
    total_revenue = 0.0

    for o in orders:
        if not o["paid"]:
            continue
        print("Processing order:", o["id"])

        order_total = 0.0
        for it in o["items"]:
            order_total += it["price"] * it["qty"]
        if order_total < min_total:
            continue

        order_total = order_total * (1 - discount)
        order_total = order_total * (1 + TAX_RATE)

        o["total"] = order_total
        valid.append(o)
        total_revenue += order_total

    return {"count": len(valid), "revenue": total_revenue, "orders": valid}


CATEGORY_RATES = {"electronics": 0.1, "books": 0.2}
COUPON_PERCENT = 10
VAT_RATE = 0.2


def process_cart(items: list[Any]) -> dict[str, Any]:
    """Імперативна версія кошика (варіант 4): глобали, print і мутації."""
    subtotal = 0.0
    after_category = 0.0
    for it in items:
        if it["qty"] <= 0 or it["price"] < 0:
            continue
        print("Processing item:", it["name"])
        it["line_total"] = it["price"] * it["qty"]
        it["discount_rate"] = CATEGORY_RATES.get(it["category"], 0.0)
        it["discounted_total"] = it["line_total"] * (1 - it["discount_rate"])
        subtotal += it["line_total"]
        after_category += it["discounted_total"]
    after_coupon = after_category * (1 - COUPON_PERCENT / 100)
    total = after_coupon * (1 + VAT_RATE)
    return {"subtotal": subtotal, "after_coupon": after_coupon, "total": total}
