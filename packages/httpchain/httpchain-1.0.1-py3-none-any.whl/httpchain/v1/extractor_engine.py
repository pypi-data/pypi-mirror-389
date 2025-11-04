# httpchain/extractor_engine.py

from typing import Any, List, Optional, Dict
import re

from .schema import Extractor, HTTPResponse, DeclarativeCheck, CANNOT_BE_DETERMINED, DeclarativeOperator, ExtractorType, RegexExtractor


class ExtractionEngine:
    @classmethod
    def extract(cls, extractor: Extractor, response: HTTPResponse) -> Any:
        try:
            if extractor.extractor_type == ExtractorType.JSONPATHARRAY:
                target_obj = cls._get_value_at_path(response, extractor.jsonpatharray_extractor)
                return target_obj
            elif extractor.extractor_type == ExtractorType.DECLARATIVE_CHECK:
                return cls._execute_declarative_check(extractor.declarative_check_extractor, response)
            elif extractor.extractor_type == ExtractorType.REGEX:
                return cls._extract_regex(extractor.regex_extractor, response)

        except Exception as e:
            return CANNOT_BE_DETERMINED

    @classmethod
    def _extract_regex(cls, regex_extractor: RegexExtractor, response: HTTPResponse):
        source_value = cls._get_value_at_path(response, regex_extractor.path)

        if isinstance(source_value, (dict, list)):
            return CANNOT_BE_DETERMINED

        if not isinstance(source_value, str):
            source_text = str(source_value)
        else:
            source_text = source_value

        try:
            compiled_pattern = re.compile(regex_extractor.pattern)
        except re.error:
            return CANNOT_BE_DETERMINED

        num_groups = compiled_pattern.groups

        if not regex_extractor.find_all:
            match = compiled_pattern.search(source_text)
            if not match:
                return None
            if num_groups == 1:
                return match.group(1)
            else:
                if compiled_pattern.groupindex:
                    return match.groupdict()
                else:
                    return match.groups()
        else:
            matches = list(compiled_pattern.finditer(source_text))
            if not matches:
                return []
            if num_groups == 1:
                return [m.group(1) for m in matches]
            else:
                if compiled_pattern.groupindex:
                    return [m.groupdict() for m in matches]
                else:
                    return [m.groups() for m in matches]


    @classmethod
    def _get_value_at_path(cls, response: HTTPResponse, path: List[str]) -> Any:
        if not path:
            return CANNOT_BE_DETERMINED
        current = response
        for key in path:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list):
                try:
                    index = int(key)
                    current = current[index]
                except (ValueError, IndexError, TypeError):
                    return None
            elif hasattr(current, key):
                current = getattr(current, key)
            else:
                return None

        return current

    @classmethod
    def _execute_declarative_check(cls, check: DeclarativeCheck, response: HTTPResponse) -> bool:
        value_to_check = cls._get_value_at_path(response, check.path)
        op = check.operator
        val = check.value

        return cls._do_declarative_check(op, value_to_check, val)

    @classmethod
    def _do_declarative_check(cls, op: DeclarativeOperator, value_to_check, val):
        """
        op: Operator
        value_to_check: value to check against the defined val
        val: defined val to check
        """
        if op == DeclarativeOperator.EXISTS:
            return value_to_check is not None
        if op == DeclarativeOperator.NOT_EXISTS:
            return value_to_check is None

        if value_to_check is CANNOT_BE_DETERMINED:
            return CANNOT_BE_DETERMINED

        if op == DeclarativeOperator.EQUALS:
            return value_to_check == val
        if op == DeclarativeOperator.NOT_EQUALS:
            return value_to_check != val
        if op == DeclarativeOperator.CONTAINS:
            return val in value_to_check
        if op == DeclarativeOperator.NOT_CONTAINS:
            return val not in value_to_check
        if op == DeclarativeOperator.IS_GREATER_THAN:
            return value_to_check > val
        if op == DeclarativeOperator.IS_LESS_THAN:
            return value_to_check < val
        if op == DeclarativeOperator.CONTAINS_PATTERN:
            return bool(re.search(val, value_to_check)) == True
        if op == DeclarativeOperator.NOT_CONTAINS_PATTERN:
            return bool(re.search(val, value_to_check)) == False

        return CANNOT_BE_DETERMINED
