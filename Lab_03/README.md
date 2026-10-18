# Лабораторна робота №3. Нездатні до змін структури даних (immutability) у Python

**Виконав:** Данилюк Андрій Андрійович, група ФЕП-23с
**Перевірив:** Свелеба Сергій Андрійович
**Варіант:** 4 — «Склад товарів»

## Опис варіанта

**Предметна область:** склад товарів.
**Незмінна модель:** `Product`, `StockRecord`, теги (`frozenset`), метадані постачальника (`MappingProxyType`).
**Pure-оновлення:** поповнення залишку, відвантаження, зміна ціни, додавання/видалення тегу, оновлення постачальника.
**Що перевірити:** кожна операція повертає новий `StockRecord`, старий не змінюється.

## Цілі

- застосувати `tuple`, `frozenset`, `@dataclass(frozen=True, slots=True)`, `NamedTuple`, `MappingProxyType`;
- замінити мутації на pure updates (`dataclasses.replace`, конкатенація `tuple`, операції `frozenset`);
- виміряти ефект переходу на незмінні структури (`pytest --durations=5`, вимірювання `perf_counter`).

## Що зроблено

| Файл | Призначення |
|---|---|
| `model.py` | `Movement` (`NamedTuple`), `Category` (`Literal`), `Product` і `StockRecord` (`frozen=True, slots=True`) з методами pure-оновлення `with_price`, `with_tag`, `without_tag`, `with_movement`, `with_product` (`dataclasses.replace`), `make_meta` (копія + `MappingProxyType`), `freeze` — глибоке заморожування |
| `core.py` | pure-оновлення `restock`, `ship`, `change_price`, `add_tag`, `remove_tag`, `update_supplier`; бізнес-функції `total_value`, `to_reorder`, `top_valuable`, `with_tag`, `index_by_sku`; правило знижок `make_category_discount` + `apply_price_rule`; `reorder_cost` з `lru_cache` |
| `mutable_model.py` | «стара» мутабельна версія (dict/list/set) — лише для порівняння часу |
| `app.py` | оболонка I/O: читає `warehouse.json`, виконує оновлення, друкує таблиці |
| `tests/test_immutability.py` | `test_no_mutation_*`, `test_hashability`, `test_mappingproxy_is_read_only`, `FrozenInstanceError`, `freeze`, `lru_cache` |
| `tests/test_properties.py` | property-based тести (Hypothesis): чистота `restock`/`change_price`, ідемпотентність `add_tag` і `freeze`, `hash` узгоджений з `==` |
| `tests/test_performance.py` | порівняння часу до/після (`perf_counter`, без плагінів): мутабельна і незмінна модель, `reorder_cost` з кешем і без |

**Хешованість.** `Product` хешований повністю. `StockRecord` теж хешований: поле `supplier`
(`MappingProxyType`) саме по собі не хешується, тому воно виключене з хешу через
`field(hash=False)`, але бере участь у порівнянні `==`. Це перевіряють тести, а `StockRecord`
використовується як ключ `lru_cache`.

## Структура програми

```
Lab_03/
  README.md
  model.py
  core.py
  mutable_model.py
  app.py
  warehouse.json
  tests/conftest.py
  tests/test_immutability.py
  tests/test_properties.py
  tests/test_performance.py
  requirements.txt
  pyproject.toml
  mypy.ini
  report/Lab_03.docx
```

## Команди запуску

```bash
pip install -r requirements.txt
python app.py
python -m pytest
python -m pytest --durations=5
python -m pytest -q -s tests/test_performance.py
python -m mypy
python -m black --check .
python -m ruff check .
```

## Вимірювання

`tests/test_performance.py` (найкращий з 5 запусків, 2000 операцій «поповнення + зміна ціни + тег»):

| Тест | Час |
|---|---|
| до: мутабельна модель (`dict`/`list`/`set`, in-place) | ≈ 0.6 мс |
| після: незмінна модель (`frozen dataclass`, `tuple`, `frozenset`) | ≈ 19 мс |
| 10 000 викликів `reorder_cost` без кешу | ≈ 3.2 мс |
| 10 000 викликів `reorder_cost` з `lru_cache` | ≈ 2.4 мс |

`pytest --durations=5`: найдовші — тести вимірювання часу (до 0.15 с), решта < 0.005 с;
увесь набір із 29 тестів проходить менш ніж за 1 с.

## Висновок

Незмінна модель усунула цілий клас помилок: оновлення не можуть випадково зіпсувати чужі дані,
тести стабільні (той самий вхід — той самий результат), записи хешовані й придатні як ключі
`dict`/`set` і для `lru_cache`. Ціна — накладні витрати на створення копій: на 2000 послідовних
оновлень незмінна версія приблизно в 30 разів повільніша, головно через конкатенацію кортежу
історії рухів (кожне оновлення копіює весь `tuple`). Для типових обсягів складу це мілісекунди,
тож виграш у надійності переважає; для дуже довгих історій варто зберігати їх окремо або
використовувати персистентні структури.
