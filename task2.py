"""
Задание 2. Реальный I/O и обработка ошибок

Результат запуска (22 URL: 20 нормальных + 2 битых):
  успешно : 20
  ошибок  : 2 (no-such-site.invalid -> ConnectError, httpbin.org/delay/10 -> ReadTimeout)
  время   : 23.93s

Что реализовано:
  - таймаут на каждый запрос (timeout=5 секунд в client.get);
  - не более 3 попыток, пауза между ними удваивается: 1 с -> 2 с -> (4 с ...);
  - ошибки 4xx (кроме 429) не повторяются: повтор их не исправит;
  - на последней попытке ошибка пробрасывается дальше, а не прячется;
  - asyncio.gather(..., return_exceptions=True): падение одного URL не
    роняет остальные, robust_main возвращает (результаты, ошибки).
"""

import asyncio
import time
import httpx
import requests

# 20 разных картинок (у каждой свой номер в адресе)
URLS = [f"https://picsum.photos/seed/{i}/800/600" for i in range(20)]

# Битые адреса для проверки
BAD_URLS = [
    "https://no-such-site.invalid",  # домена не существует, упадёт сразу
    "https://httpbin.org/delay/10",  # отвечает 10 секунд, сработает таймаут
]


def timed(label, fn, *args):
    """Запускает fn(*args) и печатает, сколько секунд она работала."""
    start = time.perf_counter()
    fn(*args)
    print(f"{label}: {time.perf_counter() - start:.2f}s")


async def robust_fetch(
    client: httpx.AsyncClient,
    url: str,
    retries: int = 3,
    timeout: float = 5.0,
) -> int:
    delay = 1  # первая пауза 1 секунда
    for attempt in range(1, retries + 1):
        try:
            resp = await client.get(url, timeout=timeout)
            resp.raise_for_status()  # без этого 4xx/5xx не станут исключением
            return resp.status_code
        except httpx.HTTPError as exc:
            # 4xx (кроме 429) повторять бессмысленно
            if (
                isinstance(exc, httpx.HTTPStatusError)
                and 400 <= exc.response.status_code < 500
                and exc.response.status_code != 429
            ):
                raise
            # последняя попытка: не прячем ошибку
            if attempt == retries:
                raise
            await asyncio.sleep(delay)  # именно asyncio.sleep, не time.sleep
            delay *= 2  # экспоненциальный backoff: 1 -> 2 -> 4


async def robust_main():
    urls = URLS + BAD_URLS
    async with httpx.AsyncClient(follow_redirects=True) as client:
        outcomes = await asyncio.gather(
            *(robust_fetch(client, url) for url in urls),
            return_exceptions=True,  # исключения приходят в списке результатов
        )

    results, errors = [], []
    for url, outcome in zip(urls, outcomes):
        if isinstance(outcome, Exception):
            errors.append((url, outcome))
        else:
            results.append(outcome)
    return results, errors


if __name__ == "__main__":
    start = time.perf_counter()
    results, errors = asyncio.run(robust_main())
    elapsed = time.perf_counter() - start

    print(f"Успешно: {len(results)}, ошибок: {len(errors)}, время: {elapsed:.2f}s")
    for url, err in errors:
        print(f"  {url} -> {type(err).__name__}: {err}")