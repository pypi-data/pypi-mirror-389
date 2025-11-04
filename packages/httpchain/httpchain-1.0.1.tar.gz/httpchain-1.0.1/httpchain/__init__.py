# httpchain/__init__.py

from .v1.schema import Step, HTTPResponse, HTTPRequest, HttpChain, DeclarativeCheck, Extractor, RegexExtractor, ExtractorType, DeclarativeOperator, ConditionOperator, ConditionalLogic
from .v1.header_randomizer import HeaderRandomizer, get_random_headers

class HttpChainExecutor:
    def __init__(self):
        self._version_executor = None
    
    def load_json(self, http_chain_dict: dict):
        version = http_chain_dict.get("version", 0)
        if version == 1:
            from .v1.executor import HttpChainExecutor as V1Executor
            self._version_executor = V1Executor()
            self._version_executor.load_json(http_chain_dict)
        else:
            raise ValueError(f"Unsupported config version: {version}. Supported versions: 1")
    
    async def execute(self, **kwargs):
        return await self._version_executor.execute(**kwargs)
    
    def load_chain(self, chain):
        return self._version_executor.load_chain(chain)