"""
Задание 3*. Вынос CPU-bound-вычислений

Замеры (20 URL):
  скачивание                         : 5.45s
  heavy «в лоб» (прямо в event loop) : 5.10s   -> точки ticker ЗАМЕРЛИ
  heavy через ProcessPoolExecutor    : 4.12s   -> точки ticker БЕГУТ

Объяснение:
  Event loop работает в одном потоке и переключает задачи только в точках
  await (кооперативная многозадачность). heavy не содержит await и
  занимает процессор, поэтому, пока она считает, loop не может запустить
  ticker, и точки перестают печататься.
  run_in_executor + ProcessPoolExecutor отправляет вычисление в другой
  процесс (свой интерпретатор и свой GIL, другое ядро). Loop при этом
  свободен и продолжает выполнять ticker. ThreadPoolExecutor тут не
  подошёл бы: из-за GIL потоки не считают Python-код параллельно.
"""

import asyncio
import hashlib
import time
from concurrent.futures import ProcessPoolExecutor
import httpx
import requests

# 20 разных картинок (у каждой свой номер в адресе)
URLS = [f"https://picsum.photos/seed/{i}/800/600" for i in range(20)]


def timed(label, fn, *args):
    """Запускает fn(*args) и печатает, сколько секунд она работала."""
    start = time.perf_counter()
    fn(*args)
    print(f"{label}: {time.perf_counter() - start:.2f}s")


def heavy(body: bytes) -> str:
    # body * 1000 раздувает данные, чтобы хеш считался заметно долго
    return hashlib.sha256(body * 5000).hexdigest()


async def ticker():
    # «пульс» event loop: если точки перестали печататься, loop заблокирован
    while True:
        print(".", end="", flush=True)
        await asyncio.sleep(0.1)


async def cpu_main():
    # 1) ticker запускаем фоновой задачей
    ticker_task = asyncio.create_task(ticker())

    # скачиваем все ответы (на этом этапе точки бегут)
    t = time.perf_counter()
    async with httpx.AsyncClient(follow_redirects=True) as client:
        responses = await asyncio.gather(*(client.get(u) for u in URLS))
    bodies = [r.content for r in responses]
    print(f"\n[скачивание: {time.perf_counter() - t:.2f}s]")

    # 2) heavy «в лоб»: точки ЗАМРУТ
    print("[в лоб] точки должны замереть:")
    t = time.perf_counter()
    hashes_direct = [heavy(b) for b in bodies]
    print(f"\n[в лоб: {time.perf_counter() - t:.2f}s]")

    # даём ticker шанс напечатать точки после блокировки
    await asyncio.sleep(0.3)

    # 3) heavy через процессы: точки БЕГУТ
    print("[через процессы] точки должны бежать:")
    t = time.perf_counter()
    loop = asyncio.get_running_loop()
    with ProcessPoolExecutor() as pool:
        hashes_pool = await asyncio.gather(
            *(loop.run_in_executor(pool, heavy, b) for b in bodies)
        )
    print(f"\n[через процессы: {time.perf_counter() - t:.2f}s]")

    print("Хеши совпали:", hashes_direct == list(hashes_pool))

    # 4) отменяем ticker
    ticker_task.cancel()
    try:
        await ticker_task
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    # проверка обязательна: без неё ProcessPoolExecutor падает на Windows
    # и macOS, дочерние процессы заново импортируют этот файл
    timed("cpu ", lambda: asyncio.run(cpu_main()))