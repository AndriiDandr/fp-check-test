"""Тести оболонки I/O: читання кошика, формування чека, запуск."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import accept_non_food, load_cart, main, render_report, run
from core import Item, process_cart_pure

STAMP = 1_700_000_000.0


@pytest.fixture
def sample_cart() -> list[Item]:
    """Тестовий кошик: три звичайні товари і один з нульовою кількістю."""
    return [
        {"name": "Phone", "price": 1000.0, "qty": 1, "category": "electronics"},
        {"name": "Book", "price": 200.0, "qty": 2, "category": "books"},
        {"name": "Bread", "price": 30.0, "qty": 5, "category": "food"},
        {"name": "Ghost", "price": 99.0, "qty": 0, "category": "books"},
    ]


def test_load_cart(tmp_path: Path, sample_cart: list[Item]) -> None:
    """Кошик читається з JSON-файлу без змін."""
    path = tmp_path / "cart.json"
    path.write_text(json.dumps(sample_cart), encoding="utf-8")
    assert load_cart(path) == sample_cart


def test_render_report_is_pure(sample_cart: list[Item]) -> None:
    """Звіт будується з результату і містить підсумкову суму."""
    receipt = process_cart_pure(
        sample_cart, category_rates={}, coupon_percent=0, vat_rate=0.0
    )
    text = render_report(receipt, STAMP)
    assert text == render_report(receipt, STAMP)
    assert "Phone" in text
    assert "1550.00" in text


def test_accept_non_food(sample_cart: list[Item]) -> None:
    """Альтернативний фільтр відкидає їжу і нульову кількість."""
    assert [it["name"] for it in sample_cart if accept_non_food(it)] == [
        "Phone",
        "Book",
    ]


def test_run_prints_report(
    sample_cart: list[Item], capsys: pytest.CaptureFixture[str]
) -> None:
    """Оболонка друкує обидва чеки."""
    run(sample_cart, category_rates={"books": 0.1}, coupon_percent=10, vat_rate=0.2)
    out = capsys.readouterr().out
    assert out.count("До сплати:") == 2


def test_main_reads_file(
    tmp_path: Path,
    sample_cart: list[Item],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Точка входу читає кошик зі шляху, переданого аргументом."""
    path = tmp_path / "cart.json"
    path.write_text(json.dumps(sample_cart), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["app.py", str(path)])
    main()
    assert "Phone" in capsys.readouterr().out
