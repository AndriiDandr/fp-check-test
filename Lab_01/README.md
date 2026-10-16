# Лабораторна робота №1. Основи функціонального програмування у Python

**Виконав:** Данилюк Андрій Андрійович, група ФЕП-23с
**Перевірив:** Свелеба Сергій Андрійович
**Варіант:** 4 — «Кошик покупця»

## Опис варіанта

**Тема:** Кошик покупця.
**Вхідні дані:** товари — назва, ціна, кількість, категорія.
**Основне завдання:** обчислити subtotal, категоріальну знижку, купон і ПДВ.
**Функціональні вимоги:** правила знижки/податку передаються через `typing.Callable`;
програма повертає новий кошик (нові записи позицій і підсумки), вхідні дані не змінюються.

## Що зроблено

- Чисте ядро `core.py`: чисті функції предметної області без I/O, без глобального стану
  і без мутацій вхідних списків/словників — кожна функція повертає нові об'єкти.
- Політики фільтрації, категоріальної знижки, купона і ПДВ передаються через `typing.Callable`.
- Функція вищого порядку `make_cart_processor` і фабрики політик повертають налаштовані обробники.
- `print`, читання файлу `cart.json` і отримання часу винесені в оболонку `app.py`.
- pytest-тести на референтну прозорість, відсутність мутацій і правильність Callable-політик.
- Базове завдання (стартовий `process_orders`) теж переписано у функціональному стилі.

## Структура програми

```
Lab_01/
  README.md            опис варіанта, структура, команди запуску
  core.py              чисте ядро (без I/O, глобалів і мутацій)
  app.py               оболонка I/O: читання cart.json, час, print
  cart.json            приклад кошика
  tests/test_core.py   тести чистого ядра (кошик, варіант 4)
  tests/test_orders.py мінімальні тести з умови (замовлення)
  tests/test_app.py    тести оболонки I/O
  requirements.txt     pytest, mypy, black, ruff
  pyproject.toml       налаштування ruff / mypy / pytest
  Lab_01.docx          звіт
```

### Чисті функції (`core.py`)

| Функція | Що робить |
|---|---|
| `line_total(item)` | ціна × кількість |
| `cart_subtotal(items)` | сума всіх позицій (`reduce`) |
| `price_item(item, rate)` | **новий** запис позиції з `line_total`, `discount_rate`, `discounted_total` |
| `with_qty`, `with_price`, `without_category`, `scale_prices` | повертають нові об'єкти / списки (`map`, `filter`) |
| `make_category_discount(rates)` | фабрика політики знижки за категорією (`Callable[[Item], float]`) |
| `make_percent_coupon(p)`, `make_fixed_coupon(v, min)` | фабрики купонів (`Callable[[float], float]`) |
| `make_vat(rate)` | фабрика політики ПДВ (`Callable[[float], float]`) |
| `make_cart_processor(accept=, category_discount=, apply_coupon=, apply_tax=)` | функція вищого порядку: повертає налаштований обробник кошика |
| `process_cart_pure(items, *, category_rates, coupon_percent, vat_rate)` | чистий розрахунок з явними параметрами |
| `order_subtotal`, `with_total`, `make_processor`, `process_orders_pure` | базове завдання: замовлення |
| `compose(f, g)`, `make_multiplier(k)`, `identity` | додаткові вправи |
| `stamp_total(total, now)` | час передається ззовні через `Callable[[], float]` |

## Команди запуску

```bash
pip install -r requirements.txt
python app.py
python app.py my_cart.json
```

## Тестування та перевірки

```bash
python -m pytest -v
python -m mypy
python -m black --check .
python -m ruff check .
```

Результат: 21 тест пройдено, mypy (strict) — без помилок, black і ruff — чисто.
