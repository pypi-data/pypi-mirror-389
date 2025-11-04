# HttpChain

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Declarative HTTP workflow engine** for building complex API request chains with dependency management and data extraction.

Perfect for **OSINT workflows**, **web scraping pipelines**, **API automation**, and **multi-step data collection** tasks.

## 🚀 Quick Start

```bash
# Install directly from GitHub
pip install git+https://github.com/jatin-dot-py/httpchain.git

# Or clone and install locally
git clone https://github.com/jatin-dot-py/httpchain.git
cd httpchain
pip install -e .
```

```python
import asyncio
import json
from httpchain import HttpChainExecutor

# Define your workflow
workflow = {
    "version": 1,
    "name": "User Profile Checker",
    "chain_variables": ["username"],
    "steps": [
        {
            "name": "get_profile",
            "request": {
                "request_method": "GET",
                "request_url": "https://api.github.com/users/{{username}}",
                "extractors": [
                    {
                        "extractor_key": "user_id",
                        "extractor_type": "jsonpatharray",
                        "jsonpatharray_extractor": ["json_body", "id"]
                    },
                    {
                        "extractor_key": "followers",
                        "extractor_type": "jsonpatharray", 
                        "jsonpatharray_extractor": ["json_body", "followers"]
                    }
                ]
            }
        }
    ]
}

async def main():
    executor = HttpChainExecutor()
    executor.load_json(workflow)
    result = await executor.execute(username="octocat")
    
    print(f"User ID: {result.variable_state.user_id}")
    print(f"Followers: {result.variable_state.followers}")

asyncio.run(main())
```

## ✨ Key Features

- **🔗 Declarative Workflows**: Define complex HTTP request chains in JSON
- **📊 Automatic Dependency Resolution**: Steps execute when their dependencies are ready
- **🎯 Smart Data Extraction**: Extract data using JSONPath, Regex, or boolean checks
- **🔄 Variable Substitution**: Use extracted data in subsequent requests
- **⚡ Parallel Execution**: Independent steps run concurrently
- **🛡️ Built-in Retries**: Configurable retry logic and error handling
- **🎭 Header Randomization**: Randomize User-Agent and headers for stealth
- **📝 Conditional Logic**: Skip steps based on extracted data conditions

## 🎯 Perfect For

- **OSINT Investigations**: Multi-platform account lookups and data correlation
- **API Automation**: Complex workflows spanning multiple services  
- **Web Scraping**: Extract and correlate data across multiple pages
- **Data Pipelines**: Transform and enrich data through API chains
- **Security Research**: Automated reconnaissance and data gathering

## 📖 Core Concepts

### Workflow Structure

```json
{
  "version": 1,
  "name": "My Workflow",
  "chain_variables": ["input1", "input2"],
  "steps": [...]
}
```

### Step Dependencies

Steps wait for required variables before executing:

```json
{
  "name": "step2",
  "depends_on_variables": ["token_from_step1"],
  "request": {
    "request_headers": {"Authorization": "Bearer {{token_from_step1}}"}
  }
}
```

### Data Extraction

Extract data from responses using multiple methods:

```json
{
  "extractors": [
    {
      "extractor_key": "user_id",
      "extractor_type": "jsonpatharray", 
      "jsonpatharray_extractor": ["json_body", "data", "id"]
    },
    {
      "extractor_key": "csrf_token",
      "extractor_type": "regex",
      "regex_extractor": {
        "path": ["html_body"],
        "pattern": "csrf_token=([a-f0-9]+)"
      }
    }
  ]
}
```

### Conditional Execution

Run steps only when conditions are met:

```json
{
  "condition": {
    "operator": "and",
    "checks": [
      {
        "variable_name": "user_exists",
        "operator": "equals",
        "value": true
      }
    ]
  }
}
```

## 🛠️ Advanced Features

### Parallel Execution
Steps with no shared dependencies run in parallel automatically.

### Error Handling
Built-in retries, timeouts, and graceful failure handling.

### Header Randomization
```json
{
  "randomize_headers": true
}
```

### Multiple Extraction Types
- **JSONPath**: Navigate JSON responses
- **Regex**: Extract from text/HTML with patterns
- **Declarative**: Boolean checks and conditions

## 📚 Examples

Check out the `/examples` directory for complete workflows:

- **X.com Account Checker**: Multi-step authentication and profile extraction
- **Multi-Platform OSINT**: Parallel account verification across platforms  
- **Domain RDAP Lookup**: Fallback chains for domain information
- **Instagram Profile Data**: Complex data extraction workflows

## 🔧 Installation & Setup

```bash
# Install from GitHub
pip install git+https://github.com/jatin-dot-py/httpchain.git

# With examples dependencies
pip install "git+https://github.com/jatin-dot-py/httpchain.git[examples]"

# Development setup
git clone https://github.com/jatin-dot-py/httpchain.git
cd httpchain
pip install -e ".[examples]"
```

## 📋 Requirements

- Python 3.10+
- httpx
- beautifulsoup4
- jsonpath-ng

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines and submit pull requests.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Documentation**: [Full API Reference](https://github.com/jatin-dot-py/httpchain#readme)
- **Examples**: [Example Workflows](/examples)
- **Issues**: [Bug Reports & Feature Requests](https://github.com/jatin-dot-py/httpchain/issues)

---

**Built for developers who need to orchestrate complex HTTP workflows with precision and reliability.**