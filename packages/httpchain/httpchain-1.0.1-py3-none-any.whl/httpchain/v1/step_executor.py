# httpchain/step_executor.py

import asyncio
import logging

from .variable_manager import VariableManager
from .extractor_engine import ExtractionEngine
from .request_executor import RequestExecutor
from .schema import HTTPRequest, HTTPResponse, CANNOT_BE_DETERMINED, ConditionOperator, ConditionalLogic
from .header_randomizer import get_random_headers

logger = logging.getLogger("httpchain")


class StepExecutor:
    def __init__(self, step, variable_manager, stop_event):
        self.step = step
        self.variable_manager: VariableManager = variable_manager
        self.stop_event = stop_event

        self._is_executing: bool = False
        self._is_finished: bool = False
        self._has_failed: bool = False

    @property
    def is_executing(self):
        return self._is_executing

    @property
    def is_finished(self) -> bool:
        return self._is_finished

    @property
    def has_failed(self) -> bool:
        return self._has_failed

    async def can_start(self) -> bool:
        if not self.step.depends_on_variables:
            return True
        return await self.variable_manager.has_variables(self.step.depends_on_variables)

    async def execute(self):
        logger.info(f"[{self.step.name}] Waiting for dependencies: {self.step.depends_on_variables}")

        while not await self.can_start():
            if self.stop_event.is_set():
                logger.warning(f"[{self.step.name}] Halting due to stop event (deadlock detected).")
                self._is_finished = True
                return
            await asyncio.sleep(0.1)

        if not await self._conditions_satisfied():
            logger.info(f"[{self.step.name}] Conditions not satisfied, skipping execution.")
            self._is_finished = True
            return

        logger.info(f"[{self.step.name}] Dependencies met. Starting execution.")
        self._is_executing = True

        http_request = await self._prepare_request()
        http_response = await RequestExecutor.execute(http_request)
        self.step.request._response = http_response

        if http_response.failed:
            logger.error(f"[{self.step.name}] Request failed: {http_response.failure_reason}")
            self._has_failed = True
            # DON'T return early - continue to run extractors

        if not http_response.failed:
            logger.info(f"[{self.step.name}] Request successful (Status: {http_response.status_code})")

        # ALWAYS run extractors, whether request succeeded or failed
        await self._extract_content(http_response)
        http_response._soup = None

        self._is_executing = False
        self._is_finished = True
        logger.info(f"[{self.step.name}] Finished.")

    async def _prepare_request(self) -> HTTPRequest:
        request: HTTPRequest = self.step.request
        variables = await self.variable_manager.read_variables(self.step.depends_on_variables or [])
        logger.debug(f"[{self.step.name}] Formatting request with variables: {variables}")
        request.format_request(variables)
        
        # Inject random headers if flag is set
        if self.step.randomize_headers:
            logger.debug(f"[{self.step.name}] Generating random headers")
            random_headers = get_random_headers(base_headers=request.request_headers)
            request.request_headers = random_headers
            logger.debug(f"[{self.step.name}] Injected headers: {list[str](random_headers.keys())}")
        
        return request

    async def _conditions_satisfied(self):
        if not self.step.condition:
            return True

        condition_to_evaluate: ConditionalLogic = self.step.condition
        checks = condition_to_evaluate.checks
        operator = condition_to_evaluate.operator

        evaluated_outputs = []
        for check in checks:
            variable_name = check.variable_name
            variable_value = await self.variable_manager.read_variable(variable_name)
            check_defined_value = check.value
            check_operator = check.operator
            evaluated_output = ExtractionEngine._do_declarative_check(op=check_operator, value_to_check=variable_value,
                                                                      val=check_defined_value)
            if evaluated_output == CANNOT_BE_DETERMINED:
                logger.warning(
                    f"[{self.step.name}] Something is really wrong!! Step condition check returned a invalid output. Skipping execution")
                return False

            evaluated_outputs.append(evaluated_output)

        if operator == ConditionOperator.AND:
            return all(evaluated_outputs)

        elif operator == ConditionOperator.OR:
            return any(evaluated_outputs)

        return False

    async def _extract_content(self, response: HTTPResponse):
        extractors = self.step.request.extractors
        if not extractors:
            return

        logger.info(f"[{self.step.name}] Running {len(extractors)} extractor(s)...")
        for extractor in extractors:
            extracted_value = ExtractionEngine.extract(extractor, response)

            if extracted_value is CANNOT_BE_DETERMINED:
                logger.warning(f"[{self.step.name}] Extractor '{extractor.extractor_key}' failed: CANNOT_BE_DETERMINED")
                continue

            await self.variable_manager.write_variable(extractor.extractor_key, extracted_value)
