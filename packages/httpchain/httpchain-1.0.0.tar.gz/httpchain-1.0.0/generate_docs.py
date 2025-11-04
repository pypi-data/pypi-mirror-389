from httpchain import Step, HttpChain, HTTPRequest, HTTPResponse, Extractor, DeclarativeCheck, RegexExtractor, ExtractorType, DeclarativeOperator, ConditionOperator, ConditionalLogic

def generate_complete_documentation() -> str:
    """Generate complete HttpChain documentation in logical order."""

    # Create dummy instances to get documentation
    http_chain = HttpChain("", [], [])
    step = Step("", HTTPRequest("", "", "GET"), [])
    http_request = HTTPRequest("", "", "GET")
    http_response = HTTPResponse(200, "", {}, 0.0, {})
    extractor = Extractor("", ExtractorType.JSONPATHARRAY)
    declarative_check = DeclarativeCheck([], DeclarativeOperator.EXISTS)
    regex_extractor = RegexExtractor([], "")
    conditional_logic = ConditionalLogic(ConditionOperator.AND, [])

    # Arrange in logical order
    sections = [
        "# HttpChain Documentation\n",
        "Complete reference for HttpChain - a declarative HTTP workflow engine.\n",

        http_chain.to_docs(),
        "\n---\n",
        step.to_docs(),
        "\n---\n",
        http_request.to_docs(),
        "\n---\n",
        http_response.to_docs(),
        "\n---\n",
        extractor.to_docs(),
        "\n---\n",
        declarative_check.to_docs(),
        "\n---\n",
        regex_extractor.to_docs(),
        "\n---\n",
        conditional_logic.to_docs(),
        "\n---\n",

        "# Quick Start\n",
        """
```python
import asyncio
from httpchain import HttpChainExecutor

async def main():
    executor = HttpChainExecutor()
    executor.load_json(workflow_json)
    result = await executor.execute(username="testuser")
    print(result.variable_state_dict)

asyncio.run(main())
```
        """.strip()
    ]

    return "\n".join(sections)


complete_docs = generate_complete_documentation()

with open("docs.md", "w", encoding="utf-8") as f:
    f.write(complete_docs)

print("Complete documentation generated!")