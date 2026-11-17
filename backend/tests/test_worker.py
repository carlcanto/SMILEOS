import asyncio

from app.shared.config import Settings
from app.worker import run


def test_el_worker_se_detiene_de_forma_ordenada(unreachable_settings: Settings) -> None:
    async def scenario() -> None:
        stop = asyncio.Event()
        task = asyncio.create_task(run(unreachable_settings, stop))
        await asyncio.sleep(0.2)
        assert not task.done(), "un ciclo fallido no debe tumbar el worker"
        stop.set()
        await asyncio.wait_for(task, timeout=2)

    asyncio.run(scenario())
