# httpchain/schema.py

from __future__ import annotations

from dataclasses import dataclass, field
from tkinter import N
from typing import Literal, List, Optional, Any, Dict, Union
from enum import Enum
from bs4 import BeautifulSoup
from types import SimpleNamespace

CANNOT_BE_DETERMINED = object()


class DeclarativeOperator(str, Enum):
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    CONTAINS_PATTERN = "contains_pattern"
    NOT_CONTAINS = "not_contains"
    NOT_CONTAINS_PATTERN = "not_contains_pattern"
    IS_GREATER_THAN = "is_greater_than"
    IS_LESS_THAN = "is_less_than"


@dataclass
class DeclarativeCheck:
    path: List[str]
    operator: DeclarativeOperator
    value: Optional[Any] = None
    variable_name: Optional[str] = None  # To be used only when using this check as a conditional in step.

    def to_docs(self) -> str:
        return """
## DeclarativeCheck

Performs boolean checks on response data using specified paths and operators. Used both for extracting boolean values and for conditional step execution.

### Structure
```python
DeclarativeCheck(
    path=["json_body", "data", "user"],
    operator="exists",
    value=None,
    variable_name="user_exists"
)
```

### Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `path` | `List[str]` | Navigation path to the value in response | `["json_body", "ldhName"]` for JSON, `["text_body"]` for text |
| `operator` | `DeclarativeOperator` | Comparison operation to perform | `"exists"`, `"equals"`, `"contains_pattern"` |
| `value` | `Any` | Expected value for comparison (not used with exists/not_exists) | `"active"`, `200`, `"^\\\\d+$"` for regex |
| `variable_name` | `str` | Variable name when used in step conditions | `"authoritative_success"`, `"user_exists"` |

### Operators

| Operator | Description | Usage Example |
|----------|-------------|---------------|
| `exists` | Check if path exists and is not null | Check if API returned user data |
| `not_exists` | Check if path doesn't exist or is null | Check if error field is missing |
| `equals` | Value equals exact match | `value: "success"` |
| `not_equals` | Value doesn't equal | `value: null` |
| `contains` | String/array contains value | `value: "banned"` in text |
| `contains_pattern` | Regex pattern match | `value: "^\\\\d+$"` for digits only |
| `not_contains` | String/array doesn't contain | `value: "error"` |
| `not_contains_pattern` | Regex pattern doesn't match | Inverse pattern matching |
| `is_greater_than` | Numeric comparison | `value: 0` for positive numbers |
| `is_less_than` | Numeric comparison | `value: 100` for under limit |

### Real Examples

**Check if account exists (from x.com_checker.json):**
```json
{
  "path": ["json_body", "data", "user"],
  "operator": "exists"
}
```

**Check for account ban message (from multi_checker.json):**
```json
{
  "path": ["text_body"],
  "operator": "contains_pattern", 
  "value": "This account may have been banned or the username is incorrect"
}
```

**Conditional step execution (from domain_lookup.json):**
```json
{
  "variable_name": "authoritative_success",
  "operator": "equals",
  "value": false
}
```
        """.strip()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DeclarativeCheck:
        """Creates a DeclarativeCheck instance from a dictionary."""
        return cls(
            path=data.get("path", []),
            operator=data.get("operator"),
            value=data.get("value"),
            variable_name=data.get("variable_name")
        )


@dataclass
class RegexExtractor:
    path: List[str]
    pattern: str
    find_all: bool = False

    def to_docs(self) -> str:
        return """
## RegexExtractor

Extracts data from text responses using regular expression patterns. Navigates to response location via path, then applies regex to extract specific values.

### Structure
```python
RegexExtractor(
    path=["html_body"],
    pattern="gt=([0-9]+);",
    find_all=False
)
```

### Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `path` | `List[str]` | Where to find the text content | `["html_body"]`, `["text_body"]` |
| `pattern` | `str` | Regular expression with capture groups | `"gt=([0-9]+);"`, `"data-user-id=\\"(\\\\d+)\\""`|
| `find_all` | `bool` | Extract all matches or just the first | `false` for single value, `true` for list |

### Pattern Rules

- **Single capture group**: Returns the captured string
- **Multiple capture groups**: Returns tuple of captured strings  
- **Named groups**: Returns dictionary with group names as keys
- **No capture groups**: Returns the entire match

### Real Examples

**Extract guest token from X.com (from x.com_checker.json):**
```json
{
  "path": ["html_body"],
  "pattern": "gt=([0-9]+);",
  "find_all": false
}
```
Extracts: `"1234567890"` from `"gt=1234567890;path=/"`

**Extract user ID from HTML:**
```json
{
  "path": ["html_body"], 
  "pattern": "data-user-id=\\"(\\\\d+)\\"",
  "find_all": false
}
```
Extracts: `"12345"` from `<div data-user-id="12345">`

**Find all email addresses:**
```json
{
  "path": ["text_body"],
  "pattern": "([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\\\.[a-zA-Z]{2,})",
  "find_all": true
}
```
Returns: `["user@example.com", "admin@site.org"]`
        """.strip()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RegexExtractor:
        return cls(
            pattern=data.get("pattern"),
            find_all=data.get("find_all", False),
            path=data.get("path")
        )


class ExtractorType(str, Enum):
    JSONPATHARRAY = "jsonpatharray",
    REGEX = "regex"
    DECLARATIVE_CHECK = "declarative_check"


@dataclass
class Extractor:
    extractor_key: str
    extractor_type: ExtractorType

    declarative_check_extractor: Optional[DeclarativeCheck] = None
    jsonpatharray_extractor: Optional[List[str]] = None
    regex_extractor: Optional[RegexExtractor] = None

    def to_docs(self) -> str:
        return """
## Extractor

Main data extraction mechanism that pulls specific values from HTTP responses and stores them as variables for use in subsequent workflow steps.

### Structure
```python
Extractor(
    extractor_key="user_id",
    extractor_type="jsonpatharray",
    jsonpatharray_extractor=["json_body", "data", "user", "id"]
)
```

### Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `extractor_key` | `str` | Variable name to store extracted value | `"auth_token"`, `"user_id"`, `"guest_token"` |
| `extractor_type` | `ExtractorType` | Method of extraction | `"jsonpatharray"`, `"regex"`, `"declarative_check"` |
| `jsonpatharray_extractor` | `List[str]` | Path for JSON navigation | `["json_body", "user", "profile", "name"]` |
| `regex_extractor` | `RegexExtractor` | Regex extraction configuration | See RegexExtractor above |
| `declarative_check_extractor` | `DeclarativeCheck` | Boolean check configuration | See DeclarativeCheck above |

### Extraction Types

**1. JSON Path Array (`jsonpatharray`)**
Navigates JSON responses using dot notation as array.
```json
{
  "extractor_key": "followers_count",
  "extractor_type": "jsonpatharray",
  "jsonpatharray_extractor": ["json_body", "data", "user", "result", "legacy", "followers_count"]
}
```

**2. Regex (`regex`)**  
Extracts using regular expressions from text content.
```json
{
  "extractor_key": "guest_token", 
  "extractor_type": "regex",
  "regex_extractor": {
    "path": ["html_body"],
    "pattern": "gt=([0-9]+);",
    "find_all": false
  }
}
```

**3. Declarative Check (`declarative_check`)**
Boolean extraction based on conditions.
```json
{
  "extractor_key": "account_exists",
  "extractor_type": "declarative_check", 
  "declarative_check_extractor": {
    "path": ["json_body", "data", "user"],
    "operator": "exists"
  }
}
```

### Real Examples from HttpChain

**Extract X.com user followers (from x.com_checker.json):**
```json
{
  "extractor_key": "x_account_followers_count",
  "extractor_type": "jsonpatharray",
  "jsonpatharray_extractor": ["json_body", "data", "user", "result", "legacy", "followers_count"]
}
```

**Check Reddit account ban (from multi_checker.json):**  
```json
{
  "extractor_key": "reddit_account_does_not_exist",
  "extractor_type": "declarative_check",
  "declarative_check_extractor": {
    "path": ["text_body"],
    "operator": "contains_pattern",
    "value": "This account may have been banned or the username is incorrect"
  }
}
```

### Variable Flow
1. Extractor runs after HTTP request completes
2. Extracted value stored with `extractor_key` name
3. Variable becomes available to subsequent steps via `{{variable_name}}` syntax
4. Multiple extractors in one request create multiple variables
        """.strip()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Extractor:
        """Creates an Extractor instance from a dictionary."""
        declarative_check_data = data.get("declarative_check_extractor")
        return cls(
            extractor_key=data.get("extractor_key"),
            extractor_type=data.get("extractor_type"),
            declarative_check_extractor=DeclarativeCheck.from_dict(
                declarative_check_data) if declarative_check_data else None,
            jsonpatharray_extractor=data.get("jsonpatharray_extractor"),
            regex_extractor=RegexExtractor.from_dict(data.get("regex_extractor")) if data.get(
                "regex_extractor") else None
        )


@dataclass
class HTTPRequest:
    request_name: str
    request_url: str
    request_method: Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
    request_headers: Optional[Dict[str, str]] = None
    request_cookies: Optional[Dict[str, str]] = None
    request_data: Optional[Union[Dict[str, Any], str]] = None
    request_json: Optional[Dict[str, Any]] = None
    request_params: Optional[Dict[str, str]] = None
    request_connect_timeout: float = 10.0
    request_read_timeout: float = 30.0
    request_follow_redirects: bool = True
    request_retries: int = 0
    request_retry_delay: float = 1.0
    extractors: Optional[List[Extractor]] = field(default_factory=list)

    _response: "HTTPResponse" = field(init=False, repr=False, default=None)

    def to_docs(self) -> str:
        return """
## HTTPRequest

Complete HTTP request configuration including URL, headers, body, timeouts, retries, and data extractors. Supports variable substitution using {{variable_name}} syntax.

### Structure
```python
HTTPRequest(
    request_name="get_user_profile",
    request_url="https://api.example.com/users/{{user_id}}",
    request_method="GET",
    request_headers={"Authorization": "Bearer {{auth_token}}"},
    extractors=[...]
)
```

### Fields

| Field | Type | Default | Description | Example |
|-------|------|---------|-------------|---------|
| `request_name` | `str` | - | Request identifier for logging | `"get_guest_token"`, `"check_profile"` |
| `request_url` | `str` | - | Full URL with variable substitution | `"https://api.x.com/users/{{username}}"` |
| `request_method` | `str` | - | HTTP method | `"GET"`, `"POST"`, `"PUT"` |
| `request_headers` | `Dict[str, str]` | `None` | HTTP headers with variable support | `{"x-guest-token": "{{guest_token}}"}` |
| `request_cookies` | `Dict[str, str]` | `None` | HTTP cookies | `{"session": "{{session_id}}"}` |
| `request_data` | `Union[Dict, str]` | `None` | Form data or raw body | `{"username": "{{user}}"}` |
| `request_json` | `Dict[str, Any]` | `None` | JSON request body | `{"query": "{{search_term}}"}` |
| `request_params` | `Dict[str, str]` | `None` | URL query parameters | `{"page": "1", "user": "{{username}}"}` |
| `request_connect_timeout` | `float` | `10.0` | Connection timeout in seconds | `5.0` for fast APIs |
| `request_read_timeout` | `float` | `30.0` | Read timeout in seconds | `60.0` for slow APIs |
| `request_follow_redirects` | `bool` | `True` | Follow HTTP redirects | `false` to stop at redirects |
| `request_retries` | `int` | `0` | Number of retry attempts | `3` for unreliable APIs |
| `request_retry_delay` | `float` | `1.0` | Delay between retries | `2.5` seconds between attempts |
| `extractors` | `List[Extractor]` | `[]` | Data extractors for response | See Extractor documentation |

### Variable Substitution

Variables from previous steps or chain input are substituted using `{{variable_name}}` syntax:

- **URLs**: `"https://api.github.com/users/{{github_username}}/repos"`
- **Headers**: `{"Authorization": "Bearer {{auth_token}}"}`  
- **Body**: `{"user_id": "{{user_id}}", "action": "update"}`
- **Params**: `{"screen_name": "{{username}}", "count": "10"}`

### Real Examples

**X.com guest token request (from x.com_checker.json):**
```json
{
  "request_method": "GET",
  "request_url": "https://x.com/login",
  "request_headers": {
    "user-agent": "Mozilla/5.0...",
    "x-twitter-active-user": "yes"
  },
  "request_retries": 1,
  "extractors": [
    {
      "extractor_key": "guest_token",
      "extractor_type": "regex",
      "regex_extractor": {
        "path": ["html_body"],
        "pattern": "gt=([0-9]+);",
        "find_all": false
      }
    }
  ]
}
```

**X.com profile check with variable substitution:**
```json
{
  "request_method": "GET",
  "request_url": "https://api.x.com/graphql/Sfq_BSQ7VVpC3u9ycqwKYg/UserByScreenName",
  "request_headers": {
    "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
    "x-guest-token": "{{guest_token}}"
  },
  "request_params": {
    "variables": "{\\"screen_name\\":\\"{{username}}\\",\\"withGrokTranslatedBio\\":false}"
  }
}
```

**Reddit account check (from multi_checker.json):**
```json
{
  "request_method": "GET", 
  "request_url": "https://reddit.com/user/{{username}}",
  "request_headers": {
    "User-Agent": "Mozilla/5.0...",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
  },
  "request_retries": 1
}
```

### Response Processing
1. Request executes with variable substitution
2. Response parsed into multiple formats (JSON, HTML, text)
3. Extractors run to pull data from response
4. Extracted variables become available to subsequent steps
        """.strip()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HTTPRequest:
        """Creates an HTTPRequest instance from a dictionary."""
        extractors_data = data.get("extractors", [])
        return cls(
            request_name=data.get("request_name"),
            request_url=data.get("request_url"),
            request_method=data.get("request_method", "GET"),
            request_headers=data.get("request_headers"),
            request_cookies=data.get("request_cookies"),
            request_data=data.get("request_data"),
            request_json=data.get("request_json"),
            request_params=data.get("request_params"),
            request_connect_timeout=data.get("request_connect_timeout", 10.0),
            request_read_timeout=data.get("request_read_timeout", 30.0),
            request_follow_redirects=data.get("request_follow_redirects", True),
            request_retries=data.get("request_retries", 0),
            request_retry_delay=data.get("request_retry_delay", 1.0),
            extractors=[Extractor.from_dict(e) for e in extractors_data] if extractors_data else []
        )

    def _format_recursive(self, item: Any, variables: Dict[str, Any]) -> Any:
        if isinstance(item, str):
            for key, value in variables.items():
                item = item.replace(f"{{{{{key}}}}}", str(value))
            return item

        if isinstance(item, dict):
            for key in list(item.keys()):
                original_value = item[key]
                formatted_value = self._format_recursive(original_value, variables)
                formatted_key = self._format_recursive(key, variables)
                if formatted_key != key:
                    del item[key]
                    item[formatted_key] = formatted_value
                else:
                    item[key] = formatted_value
            return item

        if isinstance(item, list):
            for i, value in enumerate(item):
                item[i] = self._format_recursive(value, variables)
            return item

        return item

    def format_request(self, variables: Dict[str, Any]):
        if not variables:
            return
        self.request_url = self._format_recursive(self.request_url, variables)
        self.request_headers = self._format_recursive(self.request_headers, variables)
        self.request_cookies = self._format_recursive(self.request_cookies, variables)
        self.request_data = self._format_recursive(self.request_data, variables)
        self.request_json = self._format_recursive(self.request_json, variables)
        self.request_params = self._format_recursive(self.request_params, variables)


@dataclass
class HTTPResponse:
    status_code: int
    response_url: str
    response_headers: Dict[str, str]
    response_time: float
    response_cookies: Dict[str, str]
    failed: bool = False
    failure_reason: Optional[str] = None
    json_body: Optional[Dict[str, Any]] = None
    text_body: Optional[str] = None
    html_body: Optional[str] = None
    json_ld_data: list[dict] = field(default_factory=list)
    application_json_data: list[dict] = field(default_factory=list)
    meta_tags_data: dict = field(default_factory=dict)

    _soup: "BeautifulSoup" = field(default_factory=type(None))

    def to_docs(self) -> str:
        return """
## HTTPResponse

Container for all HTTP response data with automatic content parsing. Created automatically after each request executes and made available to extractors.

### Structure
```python
HTTPResponse(
    status_code=200,
    response_url="https://api.example.com/users/123",
    response_headers={"content-type": "application/json"},
    response_time=0.245,
    json_body={"id": 123, "name": "John"},
    text_body="{"id": 123, "name": "John"}",
    html_body=None
)
```

### Fields

| Field | Type | Description | Usage in Extractors |
|-------|------|-------------|---------------------|
| `status_code` | `int` | HTTP status code | Check success with declarative_check |
| `response_url` | `str` | Final URL after redirects | Extract domain or path info |
| `response_headers` | `Dict[str, str]` | Response headers | Access via `["response_headers", "content-type"]` |
| `response_time` | `float` | Request duration in seconds | Performance monitoring |
| `response_cookies` | `Dict[str, str]` | Set cookies from response | Extract session tokens |
| `failed` | `bool` | Whether request failed | Check request success |
| `failure_reason` | `str` | Error message if failed | Log failure details |
| `json_body` | `Dict[str, Any]` | Parsed JSON response | **Primary extraction target** |
| `text_body` | `str` | Plain text content | Regex and pattern extraction |
| `html_body` | `str` | Raw HTML content | HTML parsing and regex |
| `json_ld_data` | `List[Dict]` | Structured data from JSON-LD | SEO and metadata extraction |
| `application_json_data` | `List[Dict]` | JSON from script tags | Embedded app data |
| `meta_tags_data` | `Dict` | HTML meta tags | Page metadata |

### Content Parsing

HttpChain automatically parses responses into multiple formats:

**JSON Responses** (content-type: application/json):
- `json_body`: Parsed JSON object
- `text_body`: Raw JSON string

**HTML Responses** (content-type: text/html):
- `html_body`: Raw HTML source
- `text_body`: Extracted plain text  
- `json_ld_data`: Structured data from `<script type="application/ld+json">`
- `application_json_data`: Data from `<script type="application/json">`
- `meta_tags_data`: All meta tag properties

**Text Responses**:
- `text_body`: Plain text content

### Extractor Usage Patterns

**JSON Path Extraction** (most common):
```python
# Extract user ID: response.json_body.data.user.id
["json_body", "data", "user", "id"]

# Extract array length: response.json_body.items.length  
["json_body", "items", "length"]

# Extract nested value: response.json_body.result.legacy.followers_count
["json_body", "result", "legacy", "followers_count"]
```

**Text Pattern Extraction**:
```python
# Search in plain text
["text_body"]  # Use with regex extractor

# Search in HTML source
["html_body"]  # Use with regex extractor  
```

**Metadata Extraction**:
```python
# Get content type
["response_headers", "content-type"]

# Get specific meta tag
["meta_tags_data", "og:title"]

# Get structured data
["json_ld_data", "0", "name"]
```

### Real Examples

**X.com API Response** (json_body):
```json
{
  "data": {
    "user": {
      "result": {
        "legacy": {
          "followers_count": 12345,
          "screen_name": "username"
        }
      }
    }
  }
}
```
Extract followers: `["json_body", "data", "user", "result", "legacy", "followers_count"]`

**Reddit Ban Check** (text_body):
```html
<html>
  <body>This account may have been banned or the username is incorrect</body>
</html>
```
Check ban: Path `["text_body"]` with contains_pattern operator

**X.com Guest Token** (html_body):
```html
<script>document.cookie="gt=1234567890;path=/"</script>
```
Extract token: Path `["html_body"]` with regex `gt=([0-9]+);`

### Response Processing Flow
1. HTTP request completes
2. Response automatically parsed into multiple formats
3. Extractors run against parsed content
4. Variables created and stored for subsequent steps
5. BeautifulSoup object cleaned up to save memory
        """.strip()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HTTPResponse:
        """Creates an HTTPResponse instance from a dictionary."""
        return cls(
            status_code=data.get("status_code"),
            response_url=data.get("response_url"),
            response_headers=data.get("response_headers", {}),
            response_time=data.get("response_time"),
            response_cookies=data.get("response_cookies", {}),
            failed=data.get("failed", False),
            failure_reason=data.get("failure_reason"),
            json_body=data.get("json_body"),
            html_body=data.get("html_body"),
            text_body=data.get("text_body")
        )


class ConditionOperator(str, Enum):
    AND = "and"
    OR = "or"


@dataclass
class ConditionalLogic:
    operator: ConditionOperator
    checks: List[DeclarativeCheck]

    def to_docs(self) -> str:
        return """
## ConditionalLogic

Combines multiple DeclarativeCheck conditions using AND/OR logic to control step execution. Steps only run when all conditions are satisfied.

### Structure
```python
ConditionalLogic(
    operator="and",
    checks=[
        DeclarativeCheck(variable_name="auth_token", operator="not_equals", value=None),
        DeclarativeCheck(variable_name="user_verified", operator="equals", value=True)
    ]
)
```

### Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `operator` | `ConditionOperator` | Logic to combine checks | `"and"` (all must pass), `"or"` (any must pass) |
| `checks` | `List[DeclarativeCheck]` | Individual condition checks | List of variable validations |

### Operators

| Operator | Behavior | Use Case |
|----------|----------|----------|
| `and` | All checks must pass | Step needs multiple requirements met |
| `or` | Any check can pass | Step runs if any condition is true |

### Condition Checks vs Extractors

**Important**: ConditionalLogic checks use existing variables via `variable_name`, not response paths.
```json
{
  "variable_name": "guest_token",
  "operator": "contains_pattern", 
  "value": "^\\\\d+$"
}
```

This checks if the `guest_token` variable (from a previous extractor) matches the digit pattern.

### Real Examples

**Domain lookup fallback** (from domain_lookup.json):
```json
{
  "operator": "or",
  "checks": [
    {
      "variable_name": "registry_url",
      "operator": "equals",
      "value": null
    },
    {
      "variable_name": "authoritative_success", 
      "operator": "equals",
      "value": false
    }
  ]
}
```
**Logic**: Run fallback if no registry URL OR if authoritative lookup failed.

**X.com profile check** (from x.com_checker.json):
```json
{
  "operator": "and",
  "checks": [
    {
      "variable_name": "guest_token",
      "operator": "contains_pattern",
      "value": "^\\\\d+$"
    }
  ]
}
```
**Logic**: Only check profile if guest token is valid (digits only).

**Registry URL validation** (from domain_lookup.json):
```json
{
  "operator": "and", 
  "checks": [
    {
      "variable_name": "registry_url",
      "operator": "not_equals",
      "value": null
    }
  ]
}
```
**Logic**: Only try authoritative lookup if registry URL exists.

### Step Execution Flow
1. Step waits for all `depends_on_variables` to be available
2. If `condition` is specified, all checks are evaluated
3. Step executes only if condition passes (or no condition specified)
4. If condition fails, step is skipped and marked as finished

### Variable Dependencies
- Conditions check variables created by previous steps
- Variables must exist before condition can be evaluated
- Use `depends_on_variables` to ensure required variables are available
- Typical pattern: Step A creates variable → Step B checks variable in condition
        """.strip()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional[ConditionalLogic]:
        if not data:
            return None
        checks_data = data.get("checks", [])
        return cls(
            operator=data.get("operator", "and"),
            checks=[DeclarativeCheck.from_dict(c) for c in checks_data]
        )


@dataclass
class Step:
    name: str
    request: HTTPRequest
    depends_on_variables: List[str] = field(default_factory=list)
    condition: Optional[ConditionalLogic] = None
    randomize_headers: bool = False

    _executor: "HttpChainExecutor" = field(init=False, repr=False, default=None, compare=False, hash=False)

    def to_docs(self) -> str:
        return """
## Step

Individual workflow step containing one HTTP request with dependency management and conditional execution. Steps are the building blocks of HttpChain workflows.

### Structure
```python
Step(
    name="get_user_profile",
    request=HTTPRequest(...),
    depends_on_variables=["auth_token", "user_id"],
    condition=ConditionalLogic(...)
)
```

### Fields

| Field | Type | Default | Description | Example |
|-------|------|---------|-------------|---------|
| `name` | `str` | - | Unique step identifier for logging | `"get_guest_token"`, `"check_x_profile"` |
| `request` | `HTTPRequest` | - | HTTP request configuration | See HTTPRequest documentation |
| `depends_on_variables` | `List[str]` | `[]` | Variables this step needs before executing | `["username", "guest_token"]` |
| `condition` | `ConditionalLogic` | `None` | Optional execution conditions | See ConditionalLogic documentation |
| `randomize_headers` | `bool` | `False` | Generate random browser-like headers | `true` to randomize headers |

### Execution Order

Steps execute based on dependency resolution, not the order they appear in the JSON:

1. **Dependency Waiting**: Step waits until all `depends_on_variables` are available
2. **Condition Checking**: If condition specified, it must pass
3. **Request Execution**: HTTP request runs with variable substitution  
4. **Variable Extraction**: Response data extracted into new variables
5. **Completion**: Step marked as finished, variables available to other steps

### Variable Flow
```
Input Variables (chain_variables)
         ↓
    Step 1 (no dependencies)
         ↓ (creates variables via extractors)
    Step 2 (depends on Step 1 variables)  
         ↓ (creates more variables)
    Step 3 (depends on Step 2 variables)
```

### Real Examples

**X.com guest token step** (from x.com_checker.json):
```json
{
  "name": "get_guest_token",
  "request": {
    "request_method": "GET",
    "request_url": "https://x.com/login",
    "extractors": [
      {
        "extractor_key": "guest_token",
        "extractor_type": "regex",
        "regex_extractor": {
          "path": ["html_body"],
          "pattern": "gt=([0-9]+);",
          "find_all": false
        }
      }
    ]
  }
}
```
**Flow**: No dependencies → Executes immediately → Creates `guest_token` variable

**X.com profile check step**:
```json
{
  "name": "check x profile",
  "depends_on_variables": ["username", "guest_token"],
  "condition": {
    "operator": "and",
    "checks": [
      {
        "variable_name": "guest_token", 
        "operator": "contains_pattern",
        "value": "^\\\\d+$"
      }
    ]
  },
  "request": {
    "request_method": "GET",
    "request_url": "https://api.x.com/graphql/Sfq_BSQ7VVpC3u9ycqwKYg/UserByScreenName",
    "request_headers": {
      "x-guest-token": "{{guest_token}}"
    },
    "request_params": {
      "variables": "{\\"screen_name\\":\\"{{username}}\\",\\"withGrokTranslatedBio\\":false}"
    }
  }
}
```
**Flow**: Waits for `username` + `guest_token` → Checks token is valid → Executes API call

**Domain lookup fallback** (from domain_lookup.json):  
```json
{
  "name": "try_fallback_1",
  "depends_on_variables": ["domain", "authoritative_success"],
  "condition": {
    "operator": "or",
    "checks": [
      {
        "variable_name": "registry_url",
        "operator": "equals", 
        "value": null
      },
      {
        "variable_name": "authoritative_success",
        "operator": "equals",
        "value": false
      }
    ]
  },
  "request": {
    "request_method": "GET",
    "request_url": "https://rdap.godaddy.com/v1/domain/{{domain}}"
  }
}
```
**Flow**: Waits for `domain` + `authoritative_success` → Checks if fallback needed → Executes GoDaddy lookup

### Parallel vs Sequential Execution

**Parallel**: Steps with no shared dependencies run simultaneously
```json
[
  {"name": "check_reddit", "depends_on_variables": ["username"]},
  {"name": "check_medium", "depends_on_variables": ["username"]}  
]
```

**Sequential**: Steps depend on previous step variables
```json
[
  {"name": "login", "depends_on_variables": ["username", "password"]},
  {"name": "get_profile", "depends_on_variables": ["auth_token"]}
]
```

### Error Handling

- **Request Failure**: Extractors still run, may extract error information
- **Condition Failure**: Step skipped, no request made  
- **Dependency Deadlock**: Engine detects and halts workflow
- **Variable Missing**: Step waits indefinitely until timeout
        """.strip()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Step:
        """Creates a Step instance from a dictionary."""
        request_data = data.get("request", {})
        return cls(
            name=data.get("name"),
            request=HTTPRequest.from_dict(request_data),
            depends_on_variables=data.get("depends_on_variables", []),
            condition=ConditionalLogic.from_dict(data.get("condition")) if data.get("condition") else None,
            randomize_headers=data.get("randomize_headers", False)
        )


@dataclass
class HttpChain:
    name: str
    chain_variables: list[str]
    steps: List[Step]

    _variable_state: dict = field(init=False, repr=False, default=None, compare=False, hash=False)

    @property
    def variable_state(self) -> SimpleNamespace:
        return SimpleNamespace(**self._variable_state)

    @property
    def variable_state_dict(self) -> dict:
        return self._variable_state

    def to_docs(self) -> str:
        return """
## HttpChain

Complete workflow definition containing multiple HTTP request steps with automatic dependency resolution and variable management. This is the main container for your entire API workflow.

### Structure
```python
HttpChain(
    version=1, # Version of the schema
    name="User Account Verification",
    chain_variables=["username", "api_key"],
    steps=[step1, step2, step3]
)
```

### Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `name` | `str` | Workflow description for logging | `"X.com account checker"`, `"Domain RDAP lookup"` |
| `chain_variables` | `List[str]` | Input variables required to start workflow | `["username"]`, `["domain", "registry_url"]` |
| `steps` | `List[Step]` | Workflow steps with dependency relationships | See Step documentation |
| `variable_state` | `SimpleNamespace` | Variable state as a namespace object | - |
| `variable_state_dict` | `dict` | Variable state as a dictionary | - |

### Workflow Execution

1. **Validation**: Engine validates all dependencies can be satisfied
2. **Initialization**: `chain_variables` values provided via `execute()` method
3. **Dependency Resolution**: Steps execute when their variables become available  
4. **Variable Propagation**: Each step's extractors create variables for later steps
5. **Completion**: All steps finish, final variable state available

### Variable Management

**Input Variables** (`chain_variables`):
- Must be provided when executing the workflow
- Available to all steps immediately
- Defined at chain level

**Extracted Variables**:
- Created by step extractors during execution  
- Available to subsequent steps via dependency system
- Stored in chain's variable state. Use `variable_state` or `variable_state_dict` to access.

### Real Examples

**X.com Account Checker** (from x.com_checker.json):
```json
{
  "version": 1,
  "name": "X.com account checker",
  "chain_variables": ["username"],
  "steps": [
    {
      "name": "get_guest_token",
      "request": {
        "request_method": "GET", 
        "request_url": "https://x.com/login",
        "extractors": [
          {
            "extractor_key": "guest_token",
            "extractor_type": "regex",
            "regex_extractor": {
              "path": ["html_body"],
              "pattern": "gt=([0-9]+);",
              "find_all": false
            }
          }
        ]
      }
    },
    {
      "name": "check x profile",
      "depends_on_variables": ["username", "guest_token"],
      "condition": {
        "operator": "and",
        "checks": [
          {
            "variable_name": "guest_token",
            "operator": "contains_pattern", 
            "value": "^\\\\d+$"
          }
        ]
      },
      "request": {
        "request_method": "GET",
        "request_url": "https://api.x.com/graphql/Sfq_BSQ7VVpC3u9ycqwKYg/UserByScreenName",
        "request_headers": {
          "x-guest-token": "{{guest_token}}"
        },
        "request_params": {
          "variables": "{\\"screen_name\\":\\"{{username}}\\",\\"withGrokTranslatedBio\\":false}"
        },
        "extractors": [
          {
            "extractor_key": "x_account_exists",
            "extractor_type": "declarative_check",
            "declarative_check_extractor": {
              "path": ["json_body", "data", "user"],
              "operator": "exists"
            }
          },
          {
            "extractor_key": "x_account_followers_count", 
            "extractor_type": "jsonpatharray",
            "jsonpatharray_extractor": ["json_body", "data", "user", "result", "legacy", "followers_count"]
          }
        ]
      }
    }
  ]
}
```

**Execution Flow**:
1. Input: `username="realdonaldtrump"`
2. Step 1: Get guest token from X.com login page  
3. Step 2: Use token + username to check profile via API
4. Output: Account existence, follower count, and other profile data

**Multi-Platform Account Checker** (from multi_checker.json):
```json
{
  "version": 1,
  "name": "Multi account checker",
  "chain_variables": ["username"],
  "steps": [
    {
      "name": "check_reddit",
      "depends_on_variables": ["username"],
      "request": {
        "request_method": "GET",
        "request_url": "https://reddit.com/user/{{username}}",
        "extractors": [
          {
            "extractor_key": "reddit_account_does_not_exist",
            "extractor_type": "declarative_check", 
            "declarative_check_extractor": {
              "path": ["text_body"],
              "operator": "contains_pattern",
              "value": "This account may have been banned or the username is incorrect"
            }
          }
        ]
      }
    },
    {
      "name": "check_medium.com",
      "depends_on_variables": ["username"],
      "request": {
        "request_method": "GET",
        "request_url": "https://medium.com/@{{username}}",
        "extractors": [
          {
            "extractor_key": "medium_account_does_not_exist",
            "extractor_type": "declarative_check",
            "declarative_check_extractor": {
              "path": ["text_body"],
              "operator": "contains_pattern", 
              "value": "Maybe these stories will take you somewhere new"
            }
          }
        ]
      }
    }
  ]
}
```

**Execution Flow**:
1. Input: `username="NahamSec"`  
2. Step 1 & 2: Check Reddit and Medium **in parallel** (both depend only on username)
3. Output: Account existence status on both platforms

### Usage Pattern
```python
import asyncio
from httpchain import HttpChainExecutor

async def main():
    # Load workflow
    executor = HttpChainExecutor()
    executor.load_json(workflow_json)

    # Execute with input variables
    result = await executor.execute(username="testuser")

    # Access final variable state
    variables = result._variable_state
    print(f"Account exists: {variables.get('account_exists')}")

asyncio.run(main())
```

### Validation Rules

On creation, HttpChain validates:
- No duplicate variable names between chain_variables and extractor keys
- All step dependencies can be satisfied by available variables  
- No circular dependencies between steps

**Error Examples**:
```python
# ERROR: Duplicate variable name
chain_variables = ["user_id"]
extractors = [{"extractor_key": "user_id", ...}]  # Conflicts!

# ERROR: Unfulfilled dependency  
step.depends_on_variables = ["auth_token"]  # But no step creates auth_token

# ERROR: Circular dependency
step1.depends_on_variables = ["var_b"]
step2.depends_on_variables = ["var_a"] 
step1.extractors = [{"extractor_key": "var_a", ...}]
step2.extractors = [{"extractor_key": "var_b", ...}]
```
        """.strip()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HttpChain:
        """Creates an HttpChain instance from a dictionary."""
        steps_data = data.get("steps", [])
        return cls(
            name=data.get("name"),
            chain_variables=data.get("chain_variables"),
            steps=[Step.from_dict(s) for s in steps_data]
        )

    def __post_init__(self):
        seen_variables = set[str](self.chain_variables)
        conflicts = []
        for step in self.steps:
            for extractor in step.request.extractors:
                if extractor.extractor_key in seen_variables:
                    conflicts.append(
                        f"Chain has reused extractor key name {extractor.extractor_key} at step {step.name}")
                else:
                    seen_variables.add(extractor.extractor_key)

        for step in self.steps:
            for var in step.depends_on_variables:
                if var not in seen_variables and var not in self.chain_variables:
                    conflicts.append(
                        f"Unfulfilled requirement: {var}. Variable not produced at any level or in chain_variables.")

        if conflicts:
            raise ValueError(", ".join(conflicts))