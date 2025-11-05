# inquire-py

**Intelligent inquiry with structured results**

Combine BAML's structured extraction with deep research capabilities to get type-safe, structured data from research queries.

## Quick Start

### 1. Install Dependencies

```bash
# Install inquire-py
pip install inquire-py

# Install BAML CLI (required for code generation)
npm install -g @boundaryml/baml
```

> **Note**: The package is installed as `inquire-py` but imported as `inquire` in Python.

### 2. Set Up API Keys

Export environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export TAVILY_API_KEY="tvly-..."
```

Get API keys:
- OpenAI: https://platform.openai.com/api-keys
- Tavily: https://tavily.com/ (for web search)

### 3. Create Your Schema

In your project directory, create `company.baml`:

```baml
class CompanyInfo {
  name string @description("Company's legal name")
  description string @description("What the company does")
  founders string[] @description("List of founder names")
  funding string | null @description("Total funding raised")
}

function ExtractCompanyInfo(research_output: string) -> CompanyInfo {
  client CustomGPT4o
  prompt #"
    Extract company information from the research output below.

    Research Output:
    {{ research_output }}

    {{ ctx.output_format }}
  "#
}
```

### 4. Initialize BAML Project

Run the initialization command:

```bash
inquire init
```

This automatically:
- ✅ Creates `baml_schemas/` directory structure
- ✅ Runs `baml init` to set up the project
- ✅ Moves your `.baml` files to `baml_schemas/baml_src/`
- ✅ Generates Python types from your schemas
- ✅ Cleans up original files to avoid duplication

You can also specify a custom directory:
```bash
inquire init --dir /path/to/schemas
```

### 5. Write Your Python Code

Create `research_companies.py`:

```python
import asyncio
from inquire import research
from baml_client.types import CompanyInfo
from baml_client import b

async def main():
    result = await research(
        research_instructions="Research Stripe: founders, funding, and what they do",
        schema=CompanyInfo,
        baml_function=b.ExtractCompanyInfo
    )

    # Result is type-safe with full IDE autocomplete
    print(f"Company: {result.name}")
    print(f"Description: {result.description}")
    print(f"Founders: {', '.join(result.founders)}")
    print(f"Funding: {result.funding}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 6. Run It

```bash
python research_companies.py
```

**Project structure after `inquire init`:**
```
my_project/
├── baml_schemas/
│   ├── baml_src/
│   │   ├── company.baml           # Your schema (moved here)
│   │   ├── clients.baml           # Auto-generated LLM configs
│   │   └── generators.baml        # Auto-generated settings
│   └── baml_client/               # Generated Python types
│       ├── __init__.py
│       ├── types.py
│       └── ...
└── research_companies.py          # Your Python code
```

> **Note**: The original `.baml` files in your project root are automatically moved to `baml_schemas/baml_src/` to keep your project clean and avoid duplication.

## How It Works

1. **Research Phase**: `inquire` uses Tavily to search the web and OpenAI to synthesize findings
2. **Extraction Phase**: Your BAML function extracts structured data from the research
3. **Type Safety**: Returns a Pydantic model with full validation and IDE support
4. **Auto-Management**: BAML initialization and code generation happen automatically via `BamlManager`

## Features

- ✅ **BAML-first** - Single source of truth, no sync issues
- ✅ **Type-safe** - Full IDE autocomplete and validation
- ✅ **Extensible** - Multiple BAML functions per schema
- ✅ **Simple API** - One function call does everything
- ✅ **Async by default** - Built for modern Python async/await
- ✅ **Configurable** - Customize models, search depth, and more

## Advanced Usage

### Multiple BAML Functions

Create different extraction functions for different use cases:

```baml
// baml_schemas/baml_src/research.baml

function ExtractBasicInfo(research_output: string) -> CompanyInfo {
  client CustomGPT4oMini  // Faster, cheaper
  prompt #"Extract basic company info from: {{ research_output }}"#
}

function ExtractDetailedAnalysis(research_output: string) -> CompanyInfo {
  client CustomGPT4o  // More detailed
  prompt #"
    You are a business analyst. Provide detailed analysis.
    {{ research_output }}
    {{ ctx.output_format }}
  "#
}
```

Then use different functions based on your needs:

```python
# Quick extraction
basic = await research(
    "Research Stripe",
    schema=CompanyInfo,
    baml_function=b.ExtractBasicInfo
)

# Detailed analysis
detailed = await research(
    "Research Stripe",
    schema=CompanyInfo,
    baml_function=b.ExtractDetailedAnalysis
)
```

### Custom Configuration

```python
from inquire import Researcher, ResearchConfig

config = ResearchConfig(
    research_model="gpt-4o",           # Model for research synthesis
    extraction_model="gpt-4o-mini",    # Model for BAML extraction
    max_search_queries=10,             # Number of web searches
    max_iterations=5,                  # Research depth
    search_api="tavily",               # Search provider
)

researcher = Researcher(config=config)

result = await researcher.research(
    research_instructions="Research OpenAI's latest models",
    schema=ModelInfo,
    baml_function=b.ExtractModelInfo
)
```

### Reusing Researcher Instance

For multiple queries, reuse the `Researcher` instance:

```python
researcher = Researcher()

# First query
company1 = await researcher.research(
    "Research Stripe",
    schema=CompanyInfo,
    baml_function=b.ExtractCompanyInfo
)

# Second query (BAML already initialized)
company2 = await researcher.research(
    "Research Shopify",
    schema=CompanyInfo,
    baml_function=b.ExtractCompanyInfo
)
```

## Project Structure

A typical project using `inquire-py`:

```
my_research_project/
├── baml_schemas/
│   ├── baml_src/
│   │   ├── clients.baml       # LLM configurations
│   │   ├── generators.baml    # Code generation settings
│   │   └── research.baml      # Your schemas and functions
│   └── baml_client/           # Generated (don't edit manually)
│       ├── __init__.py
│       ├── types.py
│       └── ...
├── .env                       # API keys
├── research_companies.py      # Your Python code
└── requirements.txt
```

Add to `.gitignore`:
```
baml_schemas/baml_client/
.env
```

## Requirements

- Python 3.11+
- Node.js (for BAML CLI)
- OpenAI API key
- Tavily API key

## Development

### Running Tests

```bash
make test
```

### Creating a Release

```bash
# Automated release (recommended)
make release VERSION=0.2.0

# Or use the script directly
./scripts/release.sh 0.2.0
```

This will:
1. Update version in `pyproject.toml`
2. Create a git commit and tag
3. Push to GitHub
4. Trigger automated publishing to PyPI via GitHub Actions

See [.github/workflows/README.md](.github/workflows/README.md) for more details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test`
5. Submit a pull request

## Credits

This project builds on the excellent work of:

- **[Open Deep Research](https://github.com/langchain-ai/open_deep_research)** - Deep research capabilities powered by LangGraph and LangChain. The research and synthesis implementation in `inquire` is inspired by their approach to automated research workflows.

- **[BAML](https://github.com/BoundaryML/baml)** - Boundary ML's BAML framework provides the type-safe structured extraction layer. BAML's schema-first approach enables full type safety from definition to runtime.

Special thanks to the maintainers and contributors of these projects for creating such powerful open source tools.

## License

MIT
