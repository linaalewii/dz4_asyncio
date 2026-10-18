"""
Задание 1. Синхронно vs асинхронно

Замеры (20 URL):
  sync  : 67.95s   (requests, по очереди)
  async : 5.03s   (httpx.AsyncClient + asyncio.gather)

Объяснение:
  requests.get блокирует поток, и 20 ожиданий складываются; в async все
  запросы ждут одновременно, и общее время близко к самому долгому из них.
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


def sync_main():
    for url in URLS:
        requests.get(url)  # по очереди, время складывается


async def fetch(client: httpx.AsyncClient, url: str) -> int:
    resp = await client.get(url)
    return resp.status_code


async def fast_main():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        await asyncio.gather(*(fetch(client, url) for url in URLS))


if __name__ == "__main__":
    timed("sync ", sync_main)
    timed("async", lambda: asyncio.run(fast_main()))