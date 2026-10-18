"""Тести незмінності: немутація, read-only, хешованість, коректність нових копій."""

from collections.abc import Callable
from dataclasses import FrozenInstanceError
from types import MappingProxyType
from typing import Any

import pytest

from core import (
    add_tag,
    apply_price_rule,
    change_price,
    index_by_sku,
    make_category_discount,
    remove_tag,
    reorder_cost,
    restock,
    ship,
    supplier_name,
    to_reorder,
    top_valuable,
    total_value,
    update_supplier,
    with_tag,
)
from model import Movement, Product, StockRecord, freeze, make_meta


def test_model_uses_immutable_collections(record: StockRecord) -> None:
    """Модель зберігає колекції у tuple, frozenset і MappingProxyType."""
    assert isinstance(record.movements, tuple)
    assert isinstance(record.product.tags, frozenset)
    assert isinstance(record.supplier, MappingProxyType)


def test_frozen_dataclass_rejects_assignment(record: StockRecord) -> None:
    """Frozen dataclass забороняє змінювати поля."""
    target: Any = record
    with pytest.raises(FrozenInstanceError):
        target.quantity = 100
    with pytest.raises(FrozenInstanceError):
        target.product.price = 1.0


def test_slots_forbid_new_attributes(record: StockRecord) -> None:
    """slots=True не дозволяє додавати нові атрибути."""
    target: Any = record
    with pytest.raises((AttributeError, TypeError)):
        target.extra = 1


def test_no_mutation_when_restocking(
    record: StockRecord, fresh_record: Callable[[], StockRecord]
) -> None:
    """Поповнення повертає НОВИЙ запис, оригінал не змінюється."""
    snapshot = fresh_record()
    new_record = restock(record, 6)
    assert record == snapshot
    assert new_record is not record
    assert new_record.quantity == 10
    assert new_record.movements == (Movement(6, "restock"),)
    assert record.movements == ()
    assert new_record.stock_value() == record.stock_value() + 6000.0


def test_ship_and_validation(record: StockRecord) -> None:
    """Відвантаження зменшує залишок, некоректні значення відхиляються."""
    shipped = ship(record, 3)
    assert shipped.quantity == 1
    assert shipped.movements[-1] == Movement(-3, "ship")
    assert record.quantity == 4
    with pytest.raises(ValueError):
        ship(record, 10)
    with pytest.raises(ValueError):
        restock(record, 0)


def test_change_price_creates_new_product(record: StockRecord) -> None:
    """Зміна ціни створює новий Product, решта полів спільна."""
    updated = change_price(record, 900.0)
    assert updated.product.price == 900.0
    assert record.product.price == 1000.0
    assert updated.product is not record.product
    assert updated.supplier is record.supplier
    with pytest.raises(ValueError):
        change_price(record, -1.0)


def test_tags_are_updated_with_frozenset_operations(record: StockRecord) -> None:
    """Теги оновлюються операціями frozenset."""
    tagged = add_tag(record, "promo")
    assert tagged.product.tags == frozenset({"new", "promo"})
    assert record.product.tags == frozenset({"new"})
    assert remove_tag(tagged, "new").product.tags == frozenset({"promo"})
    assert add_tag(tagged, "promo") == tagged


def test_mappingproxy_is_read_only(record: StockRecord) -> None:
    """Метадані постачальника доступні лише для читання."""
    meta: Any = record.supplier
    with pytest.raises(TypeError):
        meta["name"] = "changed"


def test_make_meta_copies_source() -> None:
    """make_meta копіює джерело, тож зміни dict не видно в proxy."""
    source = {"name": "TechImport"}
    meta = make_meta(**source)
    source["name"] = "changed"
    assert meta["name"] == "TechImport"


def test_update_supplier_returns_new_meta(record: StockRecord) -> None:
    """Оновлення постачальника створює нову read-only мапу."""
    updated = update_supplier(record, city="Lviv")
    assert updated.supplier["city"] == "Lviv"
    assert record.supplier["city"] == "Kyiv"
    assert supplier_name(updated.supplier) == "TechImport"
    assert supplier_name(make_meta()) == "unknown"


def test_hashability(
    record: StockRecord, fresh_record: Callable[[], StockRecord]
) -> None:
    """Product і StockRecord хешовані та придатні як ключі dict/set."""
    same = restock(ship(record, 2), 2)
    products = {record.product, change_price(record, 1.0).product}
    assert len(products) == 2
    assert hash(record) == hash(fresh_record())
    assert {record: "ok"}[fresh_record()] == "ok"
    assert same != record
    assert len({record, restock(record, 1)}) == 2


def test_mappingproxy_itself_is_not_hashable(record: StockRecord) -> None:
    """Саме поле MappingProxyType не хешується — тому hash=False."""
    with pytest.raises(TypeError):
        hash(record.supplier)


def test_index_by_id_and_tags() -> None:
    """Product індексується за ключем (sku, frozenset тегів)."""
    product = Product("A1", "Item", 10.0, "misc", frozenset({"x", "y"}))
    index = {(product.sku, product.tags): product}
    assert index[("A1", frozenset({"y", "x"}))] is product


def test_freeze_deep_structure() -> None:
    """Функція freeze глибоко заморожує вкладені структури."""
    frozen = freeze({"a": [1, {"b": {2, 3}}], "c": {"d": [4]}})
    assert isinstance(frozen, MappingProxyType)
    assert frozen["a"] == (1, MappingProxyType({"b": frozenset({2, 3})}))
    assert isinstance(frozen["c"], MappingProxyType)
    target: Any = frozen
    with pytest.raises(TypeError):
        target["a"] = ()


def test_inventory_functions_return_tuples(
    records: tuple[StockRecord, ...],
    fresh_records: Callable[[], tuple[StockRecord, ...]],
) -> None:
    """Бізнес-функції повертають tuple і не змінюють вхід."""
    snapshot = fresh_records()
    assert total_value(records) == pytest.approx(4000.0 + 2000.0 + 50.0)
    assert [r.product.sku for r in to_reorder(records)] == ["LAP-01", "TSH-03"]
    assert [r.product.sku for r in top_valuable(records, 2)] == ["LAP-01", "BOO-02"]
    assert [r.product.sku for r in with_tag(records, "bestseller")] == ["BOO-02"]
    assert isinstance(to_reorder(records), tuple)
    assert records == snapshot


def test_index_by_sku_is_read_only(records: tuple[StockRecord, ...]) -> None:
    """Індекс за SKU доступний лише для читання."""
    index = index_by_sku(records)
    assert index["BOO-02"] is records[1]
    target: Any = index
    with pytest.raises(TypeError):
        target["X"] = records[0]


def test_price_rule_returns_new_records(records: tuple[StockRecord, ...]) -> None:
    """Правило знижок повертає нові записи."""
    discounted = apply_price_rule(records, make_category_discount({"books": 0.1}))
    assert discounted[1].product.price == pytest.approx(180.0)
    assert records[1].product.price == 200.0
    assert discounted[0] == records[0]
    assert discounted is not records


def test_reorder_cost_is_cached(
    record: StockRecord, fresh_record: Callable[[], StockRecord]
) -> None:
    """reorder_cost кешується через lru_cache."""
    reorder_cost.cache_clear()
    first = reorder_cost(record)
    second = reorder_cost(fresh_record())
    info = reorder_cost.cache_info()
    assert first == second == 6000.0
    assert info.hits == 1
    assert info.misses == 1


def test_no_mutation_when_adding_tag(
    record: StockRecord, fresh_record: Callable[[], StockRecord]
) -> None:
    """Додавання тегу не змінює оригінал і повертає новий об'єкт."""
    original = record
    control = fresh_record()
    new_record = add_tag(record, "vip")
    assert record is original
    assert record == control
    assert new_record is not record
    assert "vip" in new_record.product.tags
