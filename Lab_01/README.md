# Лабораторна робота №1. Основи функціонального програмування у Python

**Виконав:** Данилюк Андрій Андрійович, група ФЕП-23
**Перевірив:** Свелеба Сергій Андрійович
**Варіант 4 — «Кошик покупця»**

Товари кошика мають поля: назва, ціна, кількість, категорія. Програма обчислює
subtotal, категоріальну знижку, знижку за купоном і ПДВ та повертає **новий** кошик
(розраховані позиції + підсумки), не змінюючи вхідні дані.

## Структура

```
Lab_01/
  README.md          опис, як запускати
  .github/workflows  (у корені репозиторію) GitHub Actions: ruff, black, mypy, pytest
  core.py            чисте ядро (без I/O, глобалів і мутацій)
  app.py             оболонка побічних ефектів: читання cart.json, час, print
  cart.json          приклад кошика
  conftest.py        фікстури sample_cart і sample_orders
  tests/test_core.py pytest-тести чистого ядра (кошик, варіант 4)
  tests/test_orders.py мінімальні тести з умови (базове завдання, замовлення)
  tests/test_app.py  pytest-тести оболонки I/O
  requirements.txt   pytest, mypy, black, ruff
  pyproject.toml     налаштування black / ruff / mypy / pytest
  Lab_01.docx        звіт
```

## Чисте ядро (`core.py`)

| Функція | Що робить |
|---|---|
| `line_total(item)` | ціна × кількість |
| `cart_subtotal(items)` | сума всіх позицій |
| `price_item(item, rate)` | **новий** запис позиції з `line_total`, `discount_rate`, `discounted_total` |
| `with_qty`, `without_category`, `scale_prices` | повертають нові об'єкти / списки замість мутацій |
| `make_category_discount(rates)` | фабрика політики знижки за категорією (`Callable[[Item], float]`) |
| `make_percent_coupon(p)`, `make_fixed_coupon(v, min)` | фабрики купонів (`Callable[[float], float]`) |
| `make_vat(rate)` | фабрика політики ПДВ (`Callable[[float], float]`) |
| `make_cart_processor(accept=, category_discount=, apply_coupon=, apply_tax=)` | функція вищого порядку: повертає налаштований обробник кошика |
| `process_cart_pure(items, *, category_rates, coupon_percent, vat_rate)` | готовий чистий розрахунок з явними параметрами |
| `compose(f, g)`, `make_multiplier(k)`, `identity` | додаткові вправи |
| `stamp_total(total, now)` | час передається ззовні через `Callable[[], float]` (інжекція залежностей) |

Усі політики (фільтр позицій, категоріальна знижка, купон, податок) передаються як
`typing.Callable`, тож їх легко замінити, не змінюючи ядро.

## Запуск

```bash
pip install -r requirements.txt
python app.py              # використовує cart.json
python app.py my_cart.json # свій кошик
```

## Перевірки

```bash
python -m pytest -v
python -m mypy
python -m black --check .
python -m ruff check .
```

Результат: 21 тест пройдено (покриття ~99%), mypy (strict) — без помилок, black і ruff — чисто.
