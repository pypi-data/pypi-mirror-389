# Technical Design: inquire

**Intelligent inquiry with structured results**

---

## 1. Overview

**What:** Python library combining BAML's structured extraction with deep research capabilities.

**How it works:**
1. Define schemas in BAML files (with custom prompts)
2. BAML auto-generates type-safe Pydantic models
3. Call `research()` to execute deep research + structured extraction
4. Get back fully-typed Pydantic objects

**Key benefits:**
- ✅ BAML-first (single source of truth, no sync issues)
- ✅ Type-safe (full IDE autocomplete and validation)
- ✅ Extensible (multiple BAML functions per schema)
- ✅ Simple API (one function call does everything)

---

## 2. Architecture

```
User BAML Files (.baml)
         ↓
   BAML CLI (auto-generates)
         ↓
  Python Types (Pydantic)
         ↓
    inquire.research()
         ↓
  [Deep Research] → [BAML Extraction] → Typed Result
```

**Components:**
- **BamlManager** - Runs `baml init` and `baml-cli generate`
- **Researcher** - Orchestrates research + extraction pipeline
- **Config** - API keys, model settings

**External dependencies:**
- `open-deep-research` - Research execution
- `baml-py` - BAML runtime and extraction
- `pydantic` - Used by generated types

---

## 3. BAML Schema Definition

### 3.1 Create BAML File

**Example:** `baml_schemas/baml_src/company.baml`

```baml
class CompanyInfo {
  name string @description("Company's legal name")
  description string @description("What the company does")
  founders string[] @description("List of founder names")
  funding string? @description("Total funding raised (optional)")
}

function ExtractCompanyInfo(research_output: string) -> CompanyInfo {
  client GPT4
  prompt #"
    Extract company information from the research:

    {{ research_output }}

    {{ ctx.output_format }}
  "#
}
```

**BAML basics:**
- `string`, `int`, `float`, `bool` - Basic types
- `string[]` - Arrays
- `string?` - Optional (nullable)
- `@description("...")` - Field descriptions
- `function` - Define extraction prompts

### 3.2 Auto-Generated Python Types

BAML CLI automatically generates (`baml_schemas/baml_client/types.py`):

```python
from pydantic import BaseModel, Field

class CompanyInfo(BaseModel):
    name: str = Field(description="Company's legal name")
    description: str = Field(description="What the company does")
    founders: list[str] = Field(description="List of founder names")
    funding: str | None = Field(default=None, description="Total funding raised")

```

**✅ Full type safety, IDE autocomplete, runtime validation**

### 3.3 Multiple Functions Per Schema

Define multiple extraction strategies for the same schema:

```baml
// Financial analyst perspective
function ExtractCompanyFinancials(research_output: string) -> CompanyInfo {
  client GPT4
  prompt #"
    You are a financial analyst. Focus on financial metrics and revenue models.

    {{ research_output }}
    {{ ctx.output_format }}
  "#
}

// Technical perspective
function ExtractCompanyTech(research_output: string) -> CompanyInfo {
  client GPT4
  prompt #"
    You are a technology analyst. Focus on tech stack and innovations.

    {{ research_output }}
    {{ ctx.output_format }}
  "#
}
```

---

## 4. API Design

### 4.1 Primary API

```python
async def research(
    research_instructions: str,
    schema: type,
    baml_function: Callable,
    config: dict[str, Any] | None = None
) -> Any
```

**Parameters:**
- `research_instructions` - What to research (can include context/focus areas inline)
- `schema` - BAML-generated type (from `baml_client.types`)
- `baml_function` - BAML function callable (from `baml_client.b`) - **not a string!**
- `config` - Optional config overrides (API keys, model settings)

**Returns:** Instance of `schema` with researched data

### 4.2 Usage Examples

**Basic usage:**
```python
from inquire import research
from baml_client.types import CompanyInfo
from baml_client import b  # Import BAML function registry

result = await research(
    research_instructions="Research Stripe with focus on financial metrics",
    schema=CompanyInfo,
    baml_function=b.ExtractCompanyFinancials  # Use callable, not string!
)

print(result.name)  # Type: str
print(result.founders)  # Type: list[str]
```

**Why callable-only (not strings)?**
- ✅ IDE autocomplete for available functions
- ✅ Type checking at dev time (catch typos immediately)
- ✅ Refactoring-safe (rename detection)
- ✅ Import errors if function doesn't exist (fail fast)

**Including context in research instructions:**
```python
# Context included inline in instructions
result = await research(
    research_instructions="""
    Research Stripe. Focus areas:
    - Financial metrics and revenue models
    - Recent funding rounds
    - Market positioning vs competitors

    Pay special attention to their international expansion strategy.
    """,
    schema=CompanyInfo,
    baml_function=b.ExtractCompanyFinancials
)
```

### 4.3 Researcher Class (Advanced)

For multiple research calls with shared config:

```python
from inquire import Researcher
from baml_client.types import CompanyInfo
from baml_client import b

researcher = Researcher(
    baml_dir="./baml_schemas",
    config={"research_model": "gpt-4.1"}
)

for company in ["Stripe", "Anthropic"]:
    result = await researcher.research(
        research_instructions=f"Research {company}",
        schema=CompanyInfo,
        baml_function=b.ExtractCompanyInfo
    )
    print(result.name)
```

---

## 5. Project Structure

```
inquire/
├── pyproject.toml
├── src/inquire/
│   ├── __init__.py       # Exports: research, Researcher
│   ├── core.py           # Researcher class
│   ├── baml_manager.py   # BAML CLI wrapper
│   ├── config.py         # Configuration
│   └── exceptions.py
├── baml_schemas/         # BAML project
│   ├── baml_src/         # Your .baml files (version controlled)
│   └── baml_client/      # Auto-generated Python (gitignored)
├── examples/
└── tests/
```

**What to version control:**
- ✅ `baml_src/*.baml` - Your schemas and functions
- ❌ `baml_client/*` - Auto-generated code

---

## 6. Dependencies

```toml
[project]
name = "inquire"
requires-python = ">=3.11"

dependencies = [
    "baml-py>=0.x",              # BAML runtime
    "open-deep-research>=0.x",   # Research execution
    "pydantic>=2.0",             # Used by generated types
]
```

**External tools:**
- BAML CLI: `npm install -g @boundaryml/baml` (for development)

---

## 7. Implementation

**Phase 1: Core (MVP)**
1. BamlManager - CLI wrapper (init, generate, verify)
2. Researcher - Orchestration (research + extraction)
3. Config - API keys, model settings
4. Support callable baml_function (from `baml_client.b`)

**Phase 2: Polish**
1. Error handling (extraction failures)
2. Examples for all patterns
3. Tests (unit + integration)
4. Documentation

---

**END OF DOCUMENT**
