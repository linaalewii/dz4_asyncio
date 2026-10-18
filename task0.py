"""
Задание 0. Разминка-ловушка «Почему не быстрее?»

Замеры (20 URL):
  slow  : 18.50s   (await внутри цикла for)
  fixed : 4.91s   (asyncio.gather)

Почему async не дал ускорения:
  В slow_main внутри цикла for стоит `await fetch(...)`. await дожидается
  результата «здесь и сейчас», поэтому следующий запрос стартует только
  после завершения предыдущего. Все 20 запросов идут по очереди, время
  складывается, как в синхронном коде. Слово async само по себе ничего
  не ускоряет, нужно запустить задачи вместе.

Как починено:
  Все корутины запускаются сразу через asyncio.gather, и ожидания
  накладываются друг на друга. Общее время близко к самому долгому
  одиночному запросу, а не к сумме всех.
  Во всех AsyncClient указан follow_redirects=True: picsum отвечает
  редиректом 302, а httpx по умолчанию за редиректами не идёт.
"""

import asyncio
import time
import httpx
import requests

# 20 разных картинок (у каждой свой номер в адресе)
URLS = [f"https://picsum.photos/seed/{i}/800/600" for i in range(20)]


def timed(label, fn, *args):
    """Запускает fn(*args) и печатает, сколько секунд она работала."""
    start = time.perf_counter()
    fn(*args)
    print(f"{label}: {time.perf_counter() - start:.2f}s")


async def fetch(client: httpx.AsyncClient, url: str) -> int:
    resp = await client.get(url)
    return resp.status_code


async def slow_main():
    """Ловушка: await в цикле, запросы идут по очереди."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        for url in URLS:
            await fetch(client, url)


async def fixed_main():
    """Починка: все запросы запускаются одновременно через gather."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        await asyncio.gather(*(fetch(client, url) for url in URLS))


if __name__ == "__main__":
    timed("slow ", lambda: asyncio.run(slow_main()))
    timed("fixed", lambda: asyncio.run(fixed_main()))