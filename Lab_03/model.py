"""Незмінна модель складу: товар, запис складу, рух товару, read-only метадані."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Literal, NamedTuple

Category = Literal["electronics", "books", "clothes", "food", "misc"]


def make_meta(**kwargs: str) -> Mapping[str, str]:
    """Створює read-only метадані з КОПІЇ переданих значень."""
    return MappingProxyType(dict(kwargs))


def freeze(obj: object) -> object:
    """Глибоко заморожує вкладені dict/set/list у MappingProxyType/frozenset/tuple."""
    if isinstance(obj, Mapping):
        return MappingProxyType({k: freeze(v) for k, v in obj.items()})
    if isinstance(obj, set | frozenset):
        return frozenset(freeze(x) for x in obj)
    if isinstance(obj, list | tuple):
        return tuple(freeze(x) for x in obj)
    return obj


class Movement(NamedTuple):
    """Рух товару: зміна кількості та причина."""

    delta: int
    reason: str


@dataclass(frozen=True, slots=True)
class Product:
    """Товар: незмінні назва, ціна, категорія та теги (frozenset)."""

    sku: str
    name: str
    price: float
    category: Category
    tags: frozenset[str] = frozenset()

    def with_price(self, price: float) -> "Product":
        """Повертає новий товар з іншою ціною."""
        return replace(self, price=price)

    def with_tag(self, tag: str) -> "Product":
        """Повертає новий товар з доданим тегом."""
        return replace(self, tags=self.tags | frozenset({tag}))

    def without_tag(self, tag: str) -> "Product":
        """Повертає новий товар без указаного тегу."""
        return replace(self, tags=self.tags - frozenset({tag}))


@dataclass(frozen=True, slots=True)
class StockRecord:
    """Запис складу: товар, залишок, історія рухів (tuple), постачальник (read-only)."""

    product: Product
    quantity: int
    min_quantity: int
    movements: tuple[Movement, ...] = ()
    supplier: Mapping[str, str] = field(default_factory=make_meta, hash=False)

    def stock_value(self) -> float:
        """Вартість залишку: ціна × кількість."""
        return self.product.price * self.quantity

    def needs_reorder(self) -> bool:
        """Чи впав залишок нижче мінімального."""
        return self.quantity < self.min_quantity

    def with_movement(self, movement: Movement) -> "StockRecord":
        """Повертає новий запис із застосованим рухом товару."""
        return replace(
            self,
            quantity=self.quantity + movement.delta,
            movements=self.movements + (movement,),
        )

    def with_product(self, product: Product) -> "StockRecord":
        """Повертає новий запис з оновленим товаром."""
        return replace(self, product=product)


def make_record(
    *,
    sku: str,
    name: str,
    price: float,
    category: Category,
    quantity: int,
    min_quantity: int,
    tags: Iterable[str] = (),
    supplier: Mapping[str, str] | None = None,
) -> StockRecord:
    """Будує незмінний запис складу зі звичайних значень (list/dict копіюються)."""
    return StockRecord(
        product=Product(sku, name, price, category, frozenset(tags)),
        quantity=quantity,
        min_quantity=min_quantity,
        supplier=make_meta(**dict(supplier or {})),
    )
