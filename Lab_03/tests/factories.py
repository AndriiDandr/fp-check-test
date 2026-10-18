"""Фабрики тестових даних (deepcopy не працює з MappingProxyType)."""

from model import StockRecord, make_record


def build_record() -> StockRecord:
    """Будує новий запис, рівний фікстурі record."""
    return make_record(
        sku="LAP-01",
        name="Laptop",
        price=1000.0,
        category="electronics",
        quantity=4,
        min_quantity=5,
        tags=("new",),
        supplier={"name": "TechImport", "city": "Kyiv"},
    )


def build_records() -> tuple[StockRecord, ...]:
    """Будує новий кортеж, рівний фікстурі records."""
    return (
        build_record(),
        make_record(
            sku="BOO-02",
            name="Book",
            price=200.0,
            category="books",
            quantity=10,
            min_quantity=3,
            tags=("bestseller",),
        ),
        make_record(
            sku="TSH-03",
            name="T-shirt",
            price=50.0,
            category="clothes",
            quantity=1,
            min_quantity=4,
        ),
    )
