"""Чисте ядро розрахунку кошика покупця (варіант 4).

Усі функції модуля чисті: не виконують I/O, не використовують глобальний стан
і не змінюють вхідні дані — замість цього повертають нові об'єкти.
Політики фільтрації, знижки, купона та податку передаються як ``Callable``.
"""

from collections.abc import Iterable, Mapping
from functools import reduce
from typing import Callable, TypedDict


class Item(TypedDict):
    """Товар у кошику."""

    name: str
    price: float
    qty: int
    category: str


class PricedItem(TypedDict):
    """Новий запис позиції кошика з розрахованими сумами."""

    name: str
    price: float
    qty: int
    category: str
    line_total: float
    discount_rate: float
    discounted_total: float


class Receipt(TypedDict):
    """Результат обробки кошика: нові позиції та підсумки."""

    items: list[PricedItem]
    subtotal: float
    category_discount: float
    after_category: float
    coupon_discount: float
    after_coupon: float
    vat: float
    total: float


ItemFilterFn = Callable[[Item], bool]
CategoryDiscountFn = Callable[[Item], float]
CouponFn = Callable[[float], float]
TaxFn = Callable[[float], float]
NowFn = Callable[[], float]
CartProcessor = Callable[[Iterable[Item]], Receipt]


def compose[A, B, C](f: Callable[[B], C], g: Callable[[A], B]) -> Callable[[A], C]:
    """Повертає композицію функцій: x -> f(g(x))."""
    return lambda x: f(g(x))


def identity[A](x: A) -> A:
    """Повертає аргумент без змін (нейтральна політика)."""
    return x


def make_multiplier(k: int) -> Callable[[int], int]:
    """Фабрика функцій, що множать число на k."""
    return lambda x: x * k


def line_total(item: Item) -> float:
    """Вартість позиції: ціна × кількість."""
    return item["price"] * item["qty"]


def cart_subtotal(items: Iterable[Item]) -> float:
    """Сума всіх позицій кошика без знижок і податків."""
    return reduce(lambda acc, it: acc + line_total(it), items, 0.0)


def price_item(item: Item, discount_rate: float) -> PricedItem:
    """Створює новий запис позиції з сумою до і після знижки."""
    total = line_total(item)
    return {
        "name": item["name"],
        "price": item["price"],
        "qty": item["qty"],
        "category": item["category"],
        "line_total": total,
        "discount_rate": discount_rate,
        "discounted_total": total * (1 - discount_rate),
    }


def with_qty(item: Item, qty: int) -> Item:
    """Повертає копію товару з новою кількістю."""
    return {**item, "qty": qty}


def with_price(item: Item, price: float) -> Item:
    """Повертає копію товару з новою ціною."""
    return {**item, "price": price}


def without_category(items: Iterable[Item], category: str) -> list[Item]:
    """Повертає новий список без товарів заданої категорії."""
    return list(filter(lambda it: it["category"] != category, items))


def scale_prices(items: Iterable[Item], k: float) -> list[Item]:
    """Повертає новий список товарів з ціною, помноженою на k."""

    def scaled(it: Item) -> Item:
        """Копія товару з помноженою ціною."""
        return with_price(it, it["price"] * k)

    return list(map(scaled, items))


def make_category_discount(rates: Mapping[str, float]) -> CategoryDiscountFn:
    """Фабрика політики знижки: ставка залежить від категорії товару."""
    frozen = dict(rates)
    return lambda item: frozen.get(item["category"], 0.0)


def make_percent_coupon(percent: float) -> CouponFn:
    """Фабрика купона на відсоток від суми."""
    return lambda amount: amount * (1 - percent / 100)


def make_fixed_coupon(value: float, min_amount: float = 0.0) -> CouponFn:
    """Фабрика купона на фіксовану суму, що діє від min_amount."""

    def apply(amount: float) -> float:
        """Віднімає value, якщо сума не менша за min_amount."""
        if amount < min_amount:
            return amount
        return max(amount - value, 0.0)

    return apply


def make_vat(rate: float) -> TaxFn:
    """Фабрика політики ПДВ із заданою ставкою."""
    return lambda amount: amount * (1 + rate)


def accept_positive_qty(item: Item) -> bool:
    """Фільтр: беремо лише товари з додатною кількістю і невідʼємною ціною."""
    return item["qty"] > 0 and item["price"] >= 0


def make_exclude_category(category: str) -> ItemFilterFn:
    """Фабрика фільтра: позиції з додатною кількістю, крім заданої категорії."""
    return lambda item: accept_positive_qty(item) and item["category"] != category


def make_cart_processor(
    *,
    accept: ItemFilterFn,
    category_discount: CategoryDiscountFn,
    apply_coupon: CouponFn,
    apply_tax: TaxFn,
) -> CartProcessor:
    """Функція вищого порядку: збирає обробник кошика з переданих політик."""

    def process(items: Iterable[Item]) -> Receipt:
        """Повертає новий чек для кошика, не змінюючи вхідні товари."""
        priced = [price_item(it, category_discount(it)) for it in items if accept(it)]
        subtotal = sum(p["line_total"] for p in priced)
        after_category = sum(p["discounted_total"] for p in priced)
        after_coupon = apply_coupon(after_category)
        total = apply_tax(after_coupon)
        return {
            "items": priced,
            "subtotal": subtotal,
            "category_discount": subtotal - after_category,
            "after_category": after_category,
            "coupon_discount": after_category - after_coupon,
            "after_coupon": after_coupon,
            "vat": total - after_coupon,
            "total": total,
        }

    return process


def process_cart_pure(
    items: Iterable[Item],
    *,
    category_rates: Mapping[str, float],
    coupon_percent: float,
    vat_rate: float,
) -> Receipt:
    """Розраховує кошик зі стандартними політиками; усі параметри явні."""
    processor = make_cart_processor(
        accept=accept_positive_qty,
        category_discount=make_category_discount(category_rates),
        apply_coupon=make_percent_coupon(coupon_percent),
        apply_tax=make_vat(vat_rate),
    )
    return processor(items)


class OrderItem(TypedDict):
    """Позиція замовлення з базового завдання."""

    price: float
    qty: int


class Order(TypedDict, total=False):
    """Замовлення з базового завдання; поле total з'являється в результаті."""

    id: int
    items: list[OrderItem]
    paid: bool
    total: float


FilterFn = Callable[[float], bool]
DiscountFn = Callable[[float], float]
OrdersProcessor = Callable[[Iterable[Order]], dict[str, object]]


def order_subtotal(order: Order) -> float:
    """Сума замовлення без знижки і податку."""
    return sum(it["price"] * it["qty"] for it in order["items"])


def with_total(order: Order, total: float) -> Order:
    """Повертає НОВЕ замовлення з полем total (вхідне не змінюється)."""
    return {**order, "total": total}


def make_processor(
    *,
    accept: FilterFn,
    apply_discount: DiscountFn,
    apply_tax: TaxFn,
) -> OrdersProcessor:
    """Функція вищого порядку для замовлень: політики передаються як Callable."""

    def process(orders: Iterable[Order]) -> dict[str, object]:
        """Відбирає оплачені замовлення і рахує нові записи з total."""
        paid = [o for o in orders if o["paid"]]
        accepted = [o for o in paid if accept(order_subtotal(o))]
        qualified = [
            with_total(o, apply_tax(apply_discount(order_subtotal(o))))
            for o in accepted
        ]
        revenue = sum(o["total"] for o in qualified)
        return {"count": len(qualified), "revenue": revenue, "orders": qualified}

    return process


def process_orders_pure(
    orders: Iterable[Order],
    *,
    min_total: float,
    discount: float,
    tax_rate: float,
) -> dict[str, object]:
    """Чиста версія стартового process_orders: усі параметри передаються явно."""
    processor = make_processor(
        accept=lambda s: s >= min_total,
        apply_discount=lambda s: s * (1 - discount),
        apply_tax=make_vat(tax_rate),
    )
    return processor(orders)


def stamp_total(total: float, now: NowFn) -> tuple[float, float]:
    """Додає до суми час розрахунку; джерело часу передається ззовні."""
    return total, now()
