"""Property-based тести (Hypothesis): чистота оновлень і узгодженість hash з ==."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from core import add_tag, change_price, reorder_cost, restock
from model import Product, StockRecord, freeze, make_record

records_st = st.builds(
    make_record,
    sku=st.text(min_size=1, max_size=6),
    name=st.text(min_size=1, max_size=10),
    price=st.floats(min_value=0, max_value=1e5, allow_nan=False),
    category=st.sampled_from(["electronics", "books", "clothes", "food"]),
    quantity=st.integers(min_value=0, max_value=1000),
    min_quantity=st.integers(min_value=0, max_value=100),
    tags=st.frozensets(st.sampled_from(["new", "promo", "sale"])),
    supplier=st.dictionaries(
        st.sampled_from(["name", "city"]), st.text(max_size=8), max_size=2
    ),
)


def twin(record: StockRecord) -> StockRecord:
    """Незалежно збудована рівна копія запису."""
    return StockRecord(
        Product(
            record.product.sku,
            record.product.name,
            record.product.price,
            record.product.category,
            record.product.tags,
        ),
        record.quantity,
        record.min_quantity,
        record.movements,
        record.supplier,
    )


@given(records_st, st.integers(min_value=1, max_value=500))
def test_property_restock_is_pure(record: StockRecord, amount: int) -> None:
    """Поповнення не змінює оригінал і додає рівно amount одиниць."""
    before = twin(record)
    new = restock(record, amount)
    assert record == before
    assert new.quantity == record.quantity + amount
    assert new.movements == record.movements + new.movements[-1:]
    assert new.stock_value() == pytest.approx(
        record.stock_value() + amount * new.product.price
    )


@given(records_st, st.floats(min_value=0, max_value=1e5, allow_nan=False))
def test_property_change_price_keeps_everything_else(
    record: StockRecord, price: float
) -> None:
    """Зміна ціни змінює лише ціну, решта полів та оригінал лишаються."""
    new = change_price(record, price)
    assert new.product.price == price
    assert (new.product.sku, new.product.tags, new.quantity) == (
        record.product.sku,
        record.product.tags,
        record.quantity,
    )
    assert record == twin(record)


@given(records_st, st.sampled_from(["new", "promo", "vip"]))
def test_property_add_tag_is_idempotent(record: StockRecord, tag: str) -> None:
    """Повторне додавання того самого тегу не змінює результат."""
    once = add_tag(record, tag)
    assert add_tag(once, tag) == once
    assert tag in once.product.tags


@given(records_st)
def test_property_hash_consistent_with_eq(record: StockRecord) -> None:
    """Рівні записи мають однаковий hash і однаковий кешований результат."""
    copy = twin(record)
    assert copy == record
    assert hash(copy) == hash(record)
    assert reorder_cost(copy) == reorder_cost(record)


@given(
    st.recursive(
        st.integers() | st.text(max_size=3),
        lambda children: st.lists(children, max_size=3)
        | st.dictionaries(st.text(max_size=3), children, max_size=3),
        max_leaves=10,
    )
)
def test_property_freeze_is_idempotent(data: object) -> None:
    """Повторне заморожування нічого не змінює."""
    frozen = freeze(data)
    assert freeze(frozen) == frozen
