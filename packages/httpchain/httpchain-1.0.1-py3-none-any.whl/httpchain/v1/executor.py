# httpchain/executor.py

import asyncio
import logging
from .schema import HttpChain
from .variable_manager import VariableManager
from .step_executor import StepExecutor

logger = logging.getLogger("httpchain")


class HttpChainExecutor:
    def __init__(self, chain: HttpChain = None):
        self.chain: HttpChain = chain
        self.variable_manager = VariableManager()
        self.stop_event = asyncio.Event()

    def _log_chain_start_message(self):
        logger.info(f"Starting chain: {self.chain.name}")

    async def _initialize(self, **kwargs):
        if not self.chain:
            raise ValueError("Chain not initialized")

        self._log_chain_start_message()
        await self._load_initial(**kwargs)

        for step in self.chain.steps:
            executor = StepExecutor(step, self.variable_manager, self.stop_event)
            step._executor = executor

    async def execute(self, **kwargs) -> HttpChain:
        await self._initialize(**kwargs)
        tasks = [asyncio.create_task(step._executor.execute()) for step in self.chain.steps]

        while True:
            await asyncio.sleep(.5)
            all_finished = all(step._executor.is_finished for step in self.chain.steps)
            if all_finished:
                break

            any_executing = any(step._executor.is_executing for step in self.chain.steps)
            if not any_executing and not all_finished:
                waiting_steps = [step.name for step in self.chain.steps if not step._executor.is_finished]
                logger.error(f"Deadlock detected! Steps waiting indefinitely: {waiting_steps}")
                logger.info("Signaling all waiting steps to exit.")
                self.stop_event.set()
                break

        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(f"Chain '{self.chain.name}' finished execution.")
        self.chain._variable_state = await self.variable_manager.dump_variables()
        logger.debug(f"Final variable state: {self.chain._variable_state}")
        for step in self.chain.steps:
            step._executor = None
        return self.chain

    async def _load_initial(self, **kwargs):
        await self.variable_manager.write_variables(**kwargs)

    def load_chain(self, http_chain: HttpChain):
        self.chain = http_chain

    def load_json(self, http_chain_dict: dict):
        self.chain = HttpChain.from_dict(http_chain_dict)