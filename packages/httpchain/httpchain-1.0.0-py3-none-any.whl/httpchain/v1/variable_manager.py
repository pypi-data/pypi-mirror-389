# httpchain/variable_manager.py

import asyncio
import logging
from typing import Dict, Any, List

logger = logging.getLogger("httpchain")


class VariableManager:
    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def dump_variables(self) -> Dict[str, Any]:
        return self._store

    async def write_variable(self, name: str, value: Any):
        async with self._lock:
            self._store[name] = value
            logger.info(f"Wrote variable: '{name}'")
            logger.debug(f"Value for '{name}': {value}")

    async def write_variables(self, **kwargs):
        async with self._lock:
            self._store.update(kwargs)
            keys = list(kwargs.keys())
            logger.info(f"Wrote initial variables: {keys}")
            logger.debug(f"Initial values: {kwargs}")

    async def read_variable(self, name: str) -> Any:
        async with self._lock:
            return self._store.get(name)

    async def read_variables(self, names: List[str]) -> Dict[str, Any]:
        if not names:
            return {}
        async with self._lock:
            return {name: self._store.get(name) for name in names}

    async def has_variable(self, name: str) -> bool:
        async with self._lock:
            return name in self._store

    async def has_variables(self, names: List[str]) -> bool:
        if not names:
            return True
        async with self._lock:
            return all(name in self._store for name in names)