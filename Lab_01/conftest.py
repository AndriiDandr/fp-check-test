"""Спільні фікстури для тестів."""

import pytest

from core import Item, Order


@pytest.fixture
def sample_cart() -> list[Item]:
    """Тестовий кошик: три звичайні товари і один з нульовою кількістю."""
    return [
        {"name": "Phone", "price": 1000.0, "qty": 1, "category": "electronics"},
        {"name": "Book", "price": 200.0, "qty": 2, "category": "books"},
        {"name": "Bread", "price": 30.0, "qty": 5, "category": "food"},
        {"name": "Ghost", "price": 99.0, "qty": 0, "category": "books"},
    ]


@pytest.fixture
def sample_orders() -> list[Order]:
    """Тестові замовлення для базового завдання."""
    return [
        {"id": 1, "items": [{"price": 60.0, "qty": 2}], "paid": True},
        {"id": 2, "items": [{"price": 30.0, "qty": 1}], "paid": True},
        {"id": 3, "items": [{"price": 500.0, "qty": 1}], "paid": False},
        {
            "id": 4,
            "items": [{"price": 40.0, "qty": 1}, {"price": 25.0, "qty": 2}],
            "paid": True,
        },
    ]
