"""Pure-оновлення та бізнес-функції складу: кожна операція повертає новий об'єкт."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from functools import lru_cache, reduce
from types import MappingProxyType

from model import Movement, StockRecord, make_meta

PriceRule = Callable[[StockRecord], float]


def restock(record: StockRecord, amount: int) -> StockRecord:
    """Поповнення залишку: новий запис з більшою кількістю та рухом 'restock'."""
    if amount <= 0:
        raise ValueError("amount must be positive")
    return record.with_movement(Movement(amount, "restock"))


def ship(record: StockRecord, amount: int) -> StockRecord:
    """Відвантаження: новий запис з меншою кількістю та рухом 'ship'."""
    if amount <= 0 or amount > record.quantity:
        raise ValueError("invalid shipment amount")
    return record.with_movement(Movement(-amount, "ship"))


def change_price(record: StockRecord, new_price: float) -> StockRecord:
    """Зміна ціни: новий запис з новим Product."""
    if new_price < 0:
        raise ValueError("price must be non-negative")
    return record.with_product(record.product.with_price(new_price))


def add_tag(record: StockRecord, tag: str) -> StockRecord:
    """Додавання тегу через об'єднання frozenset."""
    return record.with_product(record.product.with_tag(tag))


def remove_tag(record: StockRecord, tag: str) -> StockRecord:
    """Видалення тегу через різницю frozenset."""
    return record.with_product(record.product.without_tag(tag))


def update_supplier(record: StockRecord, **changes: str) -> StockRecord:
    """Оновлення метаданих постачальника: нова read-only мапа."""
    return replace(record, supplier=make_meta(**{**record.supplier, **changes}))


def supplier_name(meta: Mapping[str, str]) -> str:
    """Назва постачальника з read-only метаданих."""
    return meta.get("name", "unknown")


def total_value(records: Sequence[StockRecord]) -> float:
    """Загальна вартість складу (reduce)."""
    return reduce(lambda acc, r: acc + r.stock_value(), records, 0.0)


def to_reorder(records: Sequence[StockRecord]) -> tuple[StockRecord, ...]:
    """Записи, що потребують дозамовлення (новий tuple)."""
    return tuple(filter(lambda r: r.needs_reorder(), records))


def top_valuable(records: Sequence[StockRecord], n: int = 3) -> tuple[StockRecord, ...]:
    """N записів з найбільшою вартістю залишку."""
    return tuple(sorted(records, key=lambda r: r.stock_value(), reverse=True)[:n])


def with_tag(records: Sequence[StockRecord], tag: str) -> tuple[StockRecord, ...]:
    """Записи, товар яких має вказаний тег."""
    return tuple(r for r in records if tag in r.product.tags)


def index_by_sku(records: Sequence[StockRecord]) -> Mapping[str, StockRecord]:
    """Read-only індекс записів за SKU."""
    return MappingProxyType({r.product.sku: r for r in records})


def make_category_discount(rates: Mapping[str, float]) -> PriceRule:
    """Фабрика правила знижок за категорією (ставки копіюються і заморожуються)."""
    frozen_rates = MappingProxyType(dict(rates))
    return lambda r: r.product.price * (1 - frozen_rates.get(r.product.category, 0.0))


def apply_price_rule(
    records: Sequence[StockRecord], rule: PriceRule
) -> tuple[StockRecord, ...]:
    """Застосовує правило ціни і повертає НОВИЙ кортеж записів."""
    return tuple(change_price(r, round(rule(r), 2)) for r in records)


@lru_cache(maxsize=256)
def reorder_cost(record: StockRecord) -> float:
    """Вартість дозамовлення до подвійного мінімуму (кешується, бо запис хешований)."""
    missing = max(record.min_quantity * 2 - record.quantity, 0)
    return round(missing * record.product.price, 2)
