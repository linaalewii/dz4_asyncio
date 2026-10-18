
# ДЗ №4. Асинхронное программирование в Python

Сквозной сюжет: асинхронный загрузчик URL (20 картинок с picsum.photos).

| Файл | Задание |
|------|---------|
| `task0.py` | Разминка-ловушка: почему `await` в цикле не ускоряет, и как это починить |
| `task1.py` | Синхронно (`requests`) vs асинхронно (`httpx` + `asyncio.gather`) |
| `task2.py` | Таймауты, ретраи с экспоненциальным backoff, устойчивость к битым URL |
| `task3.py` | (*) Вынос CPU-bound вычислений в `ProcessPoolExecutor` |
| `theory.md` | Ответы на теоретическую часть |

Объяснения и замеры времени лежат в docstring в начале каждого файла.

## Запуск

Нужен Python 3.11+.

```bash
python -m venv .venv
.venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate
pip install requests httpx
python task0.py
```
