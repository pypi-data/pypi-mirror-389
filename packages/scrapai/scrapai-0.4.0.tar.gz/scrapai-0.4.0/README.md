# ScrapAI - AI-Powered Web Scraping SDK

**Configuration-driven web scraping with intelligent AI assistance**

ScrapAI is an intelligent web scraping SDK that uses AI to automatically analyze URLs, discover APIs, and generate optimal scraping configurations. Instead of manually writing XPath selectors or API paths, you describe what you want to extract, and the AI agent creates the configuration for you.

---

## 🎯 What We're Trying to Achieve

### Vision
Transform web scraping from a manual, error-prone process into an intelligent, automated workflow where:
- **You describe** what data you need (e.g., "Get transaction count from this API")
- **AI analyzes** the URL structure, discovers APIs, tests extraction paths
- **AI generates** optimal scraping configurations automatically
- **System executes** configs reliably with fallback strategies

### Key Goals
1. **Zero Manual Configuration** - Describe requirements, get working configs
2. **Intelligent Resource Selection** - AI chooses best approach (API vs scraping)
3. **Self-Healing Configs** - Multiple resources with automatic fallback
4. **Production Ready** - Proper error handling, retries, proxy support
5. **Multi-Service AI Support** - Works with OpenAI, Ollama, Grok, Anthropic, etc.
6. **Configuration-Driven** - Follows bronze layer pattern (API-first, scraping fallback)

### Target Use Cases
- **Data Engineers**: Rapidly create scraping configs for data pipelines
- **Analysts**: Extract metrics from APIs/websites without coding
- **Developers**: Integrate scraping into applications with minimal setup
- **Automation**: Scheduled data collection with structured outputs

---

## ✅ What Has Been Achieved

### Core Features

**Current Feature Modules**:
- ✅ **AI Analyzer** (`ai_analyzer/`) - AI-powered configuration generation
  - Interactive AI agent with 15+ tools
  - Analyzes URLs, discovers APIs automatically
  - Tests extraction paths before creating configs
  - Iterative refinement until config works correctly
  - Creates reusable configuration files for repeated extractions

- ✅ **AI Scraper** (`ai_scraper/`) - Direct data extraction without configs
  - Similar to ScrapeGraphAI's SmartScraper functionality
  - Extracts structured data on-demand using natural language
  - Returns JSON immediately (real-time scraping)
  - Pre-processes HTML to clean text using BeautifulSoup
  - Perfect for one-off extractions and ad-hoc data needs

**Planned Feature Modules**:
- 🔜 **AI Validator** (`ai_validator/`) - Validation and quality assurance
- 🔜 **AI Optimizer** (`ai_optimizer/`) - Optimize existing configurations

- ✅ **Multi-Service AI Support**
  - OpenAI, Ollama, Grok, Anthropic, Google, Mistral
  - Automatic endpoint detection and model configuration
  - Unified API interface across services

- ✅ **Resource Priority System**
  - API endpoints (highest priority) with JSON path extraction
  - HTML scraping (XPath/BeautifulSoup) with fallback
  - Custom methods for complex logic
  - Automatic resource fallback (try first, if fails try second)

- ✅ **Execution Engine**
  - Multi-entity, multi-metric config structure
  - Browser rendering support (Playwright) for JS-heavy pages
  - CAPTCHA handling
  - Proxy rotation support
  - Parallel execution for multiple configs

- ✅ **Configuration Management**
  - Structured metadata (data types, formats, tags)
  - Config-specific utilities (`.scrapai/utils/{name}_utils.py`)
  - Schema validation with Pydantic
  - Version control support

- ✅ **Data Transformation Pipeline**
  - Dynamic action collection (base + config-specific)
  - Numeric extraction, unit conversion, filtering
  - Time-window calculations (last 24h, yesterday, etc.)
  - Deep JSON path extraction with `first.`, `last.`, `second` support

- ✅ **XML-Based AI Communication**
  - Structured XML format for unambiguous AI responses
  - Wrapper format: `<xml><scraper_config>...</scraper_config><status>done</status></xml>`
  - Tool calls, messages, and configs in XML
  - Robust parsing with error feedback

- ✅ **Intelligent Content Pre-Processing**
  - Auto-fetches and reduces content before AI analysis
  - Structure detection (LIST vs OBJECT for JSON)
  - API discovery with keyword matching
  - Content sample included in prompts to reduce AI calls

### Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                     ScrapAIClient                           │
│  Single entry point - manages all components                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Intelligent │ │ Execution    │ │ Config       │
│ Analyzer    │ │ Engine       │ │ Manager      │
│ (AI Agent)  │ │ (Crawler)    │ │ (I/O)        │
└──────┬──────┘ └──────┬───────┘ └──────┬───────┘
       │               │                 │
       │               │                 │
       ▼               ▼                 ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ AgentTools   │ │ Resource     │ │ Schema       │
│ (15 tools)   │ │ Processor    │ │ (Pydantic)   │
└──────────────┘ └──────────────┘ └──────────────┘
```

### Project Structure

```
scrap-ai/
├── scrapai/
│   ├── scrapai_client.py          # Main SDK entry point
│   ├── config/                    # Configuration management
│   │   ├── schema.py              # Pydantic models (ScraperConfig, etc.)
│   │   └── manager.py            # CRUD operations for configs
│   ├── ai_analyzer/               # Feature Module: AI-powered config generation
│   │   ├── analyzer.py             # IntelligentAnalyzer (main agent orchestrator)
│   │   ├── system_prompt.py       # System prompt builder
│   │   ├── xml_parser.py          # XML parsing & validation
│   │   └── api_finder.py          # API endpoint discovery
│   ├── ai_scraper/                # Feature Module: Direct data extraction
│   │   ├── scraper.py             # IntelligentScraper (smartscraper method)
│   │   ├── system_prompt.py       # Data extraction prompts
│   │   └── data_parser.py         # XML parser for extracted data
│   ├── ai_validator/              # Feature Module: Validation (future)
│   │   └── ...                    # To be implemented
│   ├── ai_agent/                  # Conversation & model interface
│   │   └── agent.py               # Agent class (history management, model calls)
│   ├── ai_tools/                  # Agent tools (used by AI during config creation)
│   │   ├── tools.py               # AgentTools (15 tools for AI agent)
│   │   ├── config_runner.py       # Run configs for testing
│   │   ├── url_tester.py          # Test URL accessibility
│   │   └── response_validator.py  # Validate extraction results
│   ├── ai_services/               # AI service abstraction
│   │   ├── config.py              # AIServiceConfig (unified interface)
│   │   └── registry.py             # Service registry (endpoints, models)
│   ├── crawler/                    # Execution engine
│   │   ├── execution_engine.py     # Orchestrates config execution
│   │   └── resource_processor.py  # Processes individual resources
│   ├── utils/                      # Core utilities
│   │   ├── http_client.py          # HTTP requests with retries
│   │   ├── html_extractor.py       # XPath, BeautifulSoup extraction
│   │   ├── data_transformer.py    # Data transformations (deep_access, etc.)
│   │   └── browser_client.py       # Playwright browser wrapper
│   └── code_generator.py          # Generate Python code from configs
├── examples/                       # Usage examples
│   ├── scenario_1_basic_scraping.py
│   ├── scenario_2_add_to_existing.py
│   ├── scenario_3_custom_utilities.py
│   └── ...
└── .scrapai/                       # Generated files (created at runtime)
    ├── configs/                    # JSON config files
    ├── utils/                      # Config-specific utilities
    └── proxies.json                # Proxy configuration
```

---

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

For browser rendering (optional, for JS-heavy pages):
```bash
pip install playwright playwright-stealth
playwright install chromium
```

### Basic Usage

#### Option 1: Direct Data Extraction (SmartScraper)

Extract data immediately without creating config files:

```python
from scrapai import ScrapAIClient
import asyncio

async def main():
# Initialize client
client = ScrapAIClient(
        service_name="ollama",  # or "openai", "grok", etc.
        service_key="your-api-key",  # Optional for local Ollama
        service_model="llama3.2",  # Model name
        enable_logging=True
    )
    
    # Extract data directly (real-time, no config saved)
    result = await client.smartscraper(
        url="https://etherscan.io/token/0xdac17f958d2ee523a2206206994597c13d831ec7",
        description="Get Max Total Supply, Holders, Price in ETH, Transfers in 24 hours and total",
        max_iterations=3
    )
    
    if result["success"]:
        print(f"Extracted in {result['metadata']['execution_time']:.2f}s")
        print(f"Data: {result['data']}")  # Direct JSON response
    
asyncio.run(main())
```

#### Option 2: Create Reusable Configuration

Create a config file for repeated extractions:

```python
from scrapai import ScrapAIClient
import asyncio

async def main():
    # Initialize client
    client = ScrapAIClient(
        service_name="ollama",
        service_key="your-api-key",
        service_model="qwen3:latest",
        enable_logging=True
    )
    
    # Create config using AI agent
    result = await client.add_config(
        url="https://api.github.com/repos/octocat/Hello-World",
        description="Get repository stars, forks, and watchers count",
        max_iterations=5
    )
    
    print(f"Config created: {result['config_name']}")
    
    # Execute config (can run repeatedly - no AI needed!)
    # Perfect for scheduled jobs, cron tasks, or automation pipelines
    execution = await client.execute_config(result['config_name'])
    print(f"Results: {execution['data']}")
    
    # Later, run the same config without AI:
    # execution = await client.execute_config("config_name")

asyncio.run(main())
```

**When to use each:**
- **`smartscraper()`**: One-off extractions, ad-hoc data needs, quick testing
- **`add_config()`**: Repeated extractions, scheduled jobs, production pipelines

### Output Format

**SmartScraper** (`smartscraper()`) returns extracted data directly:
```python
{
    "success": True,
    "data": {
        "max_total_supply": "1000000000",
        "holders": 12543,
        "price_eth": 0.0001,
        "transfers_24h": 450
    },
    "iterations": 2,
    "metadata": {
        "url": "https://...",
        "description": "...",
        "execution_time": 2.34
    }
}
```

**Config Execution** (`execute_config()`) returns structured data:
```python
[
    {
        "name": "entity_name",
        "metric": "metric_name",
        "value": "extracted_value",
        "date": "2024-01-15T10:30:00Z",
        "config_name": "config_name"
    },
    ...
]
```

**💡 Scheduled Jobs**: Once created, configurations can be executed anytime without AI - perfect for cron jobs, task schedulers, or automation pipelines. Just call `execute_config(config_name)` - no AI service needed! The configuration is saved and can be run repeatedly.

---

## 📖 How It Works

### Configuration-Driven Ingestion Pattern

ScrapAI follows the **bronze layer pattern** (similar to data engineering pipelines):

1. **Resource Priority Order**:
   - 🥇 **API + api_path** (preferred) - Direct JSON endpoint
   - 🥈 **HTML scraping** (xpath/path) - Web scraping fallback
   - 🥉 **Custom method** (extra_method) - Complex logic

2. **First Success Wins**: Resources tried in order until one succeeds

3. **Actions Pipeline**: After extraction, `actions_methods` normalize/transform data

4. **Multi-Entity Support**: One config can contain multiple entities, each with multiple metrics

### AI Agent Workflow

```
User: "Get transaction count from https://api.example.com/stats"
    ↓
[Pre-processing] Fetch content, analyze structure, discover APIs
    ↓
[Agent Loop] (up to 5 iterations)
    ├─ AI analyzes content sample (already provided)
    ├─ AI decides: API path or scraping?
    ├─ AI calls tools: test_api_path_on_json, test_xpath_on_html
    ├─ Tools return results
    ├─ AI creates config based on results
    └─ AI tests config → validates → marks DONE
    ↓
[Save] Config saved to .scrapai/configs/{name}.json
```

### Configuration Structure

```json
{
  "metadata": {
    "name": "transaction_count",
    "data_type": "single_value",
    "expected_format": "numeric",
    "capture_date": "2024-01-15T10:30:00Z"
  },
  "entities": {
    "main": [
      {
        "name": "transaction_count",
  "resources": [
    {
      "url": "https://api.example.com/stats",
      "resource_type": "api_json",
            "api_path": "last.count",  // If LIST: use "last.field" or "first.field"
            "actions_methods": ["extract_numeric_value"]
    },
    {
      "url": "https://example.com/stats",
      "resource_type": "html_static",
      "xpath": "//span[@class='count']",
            "actions_methods": ["extract_numeric_value"]
          }
        ]
      }
    ]
  }
}
```

---

## 🛠️ How to Add New Features

### Adding a New Feature Module (Like `ai_analyzer`, `ai_scraper`, etc.)

**Feature modules** are high-level capabilities that provide specific functionality. Currently we have:
- `ai_analyzer/` - Analyzes URLs and creates scraping configurations

Future modules could include:
- `ai_scraper/` - Direct scraping without configs
- `ai_validator/` - Validation and quality assurance
- `ai_optimizer/` - Optimizes existing configs

**Step 1: Create Feature Module Directory Structure**

```
scrapai/
├── ai_scraper/              # New feature module
│   ├── __init__.py           # Export main class
│   ├── scraper.py            # Main feature class (like IntelligentAnalyzer)
│   ├── prompts.py            # Feature-specific prompts
│   └── ...                   # Other feature-specific files
```

**Step 2: Create Main Feature Class**

Create `scrapai/ai_scraper/scraper.py`:
```python
"""
AI Scraper - Direct scraping without configuration files
"""
from typing import Dict, List, Any, Optional
from ..config.manager import ConfigManager
from ..ai_services.config import AIServiceConfig
from ..ai_agent.agent import Agent

class IntelligentScraper:
    """
    Direct scraping using AI without creating config files.
    Scrapes on-demand and returns results immediately.
    """
    
    def __init__(
        self,
        config_manager: ConfigManager,
        service_config: AIServiceConfig,
        proxies: Optional[Dict] = None,
        enable_logging: bool = True
    ):
        """Initialize intelligent scraper."""
        self.config_manager = config_manager
        self.service_config = service_config
        self.proxies = proxies
        self.enable_logging = enable_logging
        
        # Initialize Agent for AI calls
        self.agent = Agent(
            service_config=service_config,
            max_context_messages=25,
            enable_logging=enable_logging
        )
    
    async def scrape_direct(self, url: str, description: str) -> Dict[str, Any]:
        """
        Scrape URL directly without creating config.
        
        Args:
            url: Target URL
            description: What to extract
            
        Returns:
            Dict with extracted data
        """
        # Your scraping logic here
        # Use self.agent.call_model() for AI assistance
        pass
```

**Step 3: Create `__init__.py` for Module**

Create `scrapai/ai_scraper/__init__.py`:
```python
"""AI Scraper module for direct scraping"""
from .scraper import IntelligentScraper

__all__ = ["IntelligentScraper"]
```

**Step 4: Integrate with ScrapAIClient**

Update `scrapai/scrapai_client.py`:

```python
from .ai_scraper.scraper import IntelligentScraper  # Add import

class ScrapAIClient:
    def __init__(self, ...):
        # ... existing initialization ...
        
        # Initialize AI Analyzer (existing)
        self.analyzer = None
        if self.service_config:
            self.analyzer = IntelligentAnalyzer(...)
        
        # Initialize AI Scraper (new feature)
        self.scraper = None
        if self.service_config:
            self.scraper = IntelligentScraper(
                config_manager=self.config_manager,
                service_config=self.service_config,
                proxies=self.proxies,
                enable_logging=enable_logging
            )
    
    async def scrape_direct(self, url: str, description: str) -> Dict[str, Any]:
        """
        Scrape URL directly without creating config file.
        
        Args:
            url: Target URL
            description: What to extract
            
        Returns:
            Dict with extracted data
        """
        if not self.scraper:
            raise ValueError("AI service required for direct scraping")
        return await self.scraper.scrape_direct(url, description)
```

**Step 5: Feature Module Best Practices**

1. **Follow Existing Patterns**:
   - Use `Agent` class for AI model calls
   - Use `AgentTools` if you need tools
   - Follow same initialization pattern as `IntelligentAnalyzer`

2. **Shared Components**:
   - Use `ConfigManager` for config-related operations
   - Use `HTTPClient`, `HTMLExtractor`, `DataTransformer` from `utils/`
   - Use `AIServiceConfig` for AI service configuration

3. **Module Independence**:
   - Feature modules should be independent (can use each other, but not required)
   - Each module can have its own prompts, parsers, etc.
   - Module-specific logic stays in that module

4. **Documentation**:
   - Add module description in README
   - Document public methods
   - Add usage examples

**Example: Complete Feature Module Structure**

```
ai_scraper/
├── __init__.py              # Exports IntelligentScraper
├── scraper.py               # Main class (IntelligentScraper)
├── prompts.py               # Scraper-specific prompts
├── parser.py                # Parse AI responses for scraping
└── extractor.py            # Extraction helpers (if needed)
```

**Integration Example**:
```python
# In scrapai_client.py
from .ai_scraper import IntelligentScraper

class ScrapAIClient:
    def __init__(self, ...):
        # ... existing code ...
        
        # Feature: AI Analyzer (creates configs)
        self.analyzer = IntelligentAnalyzer(...) if self.service_config else None
        
        # Feature: AI Scraper (direct scraping)
        self.scraper = IntelligentScraper(...) if self.service_config else None
        
        # Feature: AI Validator (future)
        # self.validator = IntelligentValidator(...) if self.service_config else None
```

---

### Adding a New AI Tool

1. **Add method to `AgentTools` class** (`scrapai/ai_tools/tools.py`):
```python
async def my_new_tool(self, param1: str, param2: int) -> Dict[str, Any]:
    """
    Description of what the tool does.
    
    **Parameters**:
      - param1: Description
      - param2: Description
    
    **Returns**:
      Dict with result data
    """
    # Implementation
    return {"success": True, "data": result}
```

2. **Add tool description to system prompt** (`scrapai/ai_analyzer/system_prompt.py`):
   - Add entry in "AVAILABLE TOOLS" section
   - Include purpose, parameters, returns, usage

3. **Tool will be automatically available** to AI agent (collected via introspection)

### Adding a New Data Transformation Method

1. **Add method to `DataTransformer` class** (`scrapai/utils/data_transformer.py`):
```python
def my_transformation(self, value: Any) -> Any:
    """
    Transform data.
    
    Args:
        value: Input value
    
    Returns:
        Transformed value
    """
    # Implementation
    return transformed_value
```

2. **Method will be automatically available** as `actions_method` (collected at runtime)

3. **Use in configs** via `actions_methods: ["my_transformation"]`

### Adding a New AI Service

1. **Add service to registry** (`scrapai/ai_services/registry.py`):
```python
KNOWN_SERVICES = {
    # ... existing services ...
    "my_service": {
        "base_url": "https://api.myservice.com/v1",
        "default_model": "my-model",
        "api_key_header": "Authorization"
  }
}
```

2. **Service automatically available** via `ScrapAIClient(service_name="my_service", ...)`

### Adding a New Resource Type

1. **Add to `ResourceType` enum** (`scrapai/config/schema.py`):
```python
class ResourceType(str, Enum):
    # ... existing types ...
    MY_NEW_TYPE = "my_new_type"
```

2. **Add processing logic** (`scrapai/crawler/resource_processor.py`):
```python
async def process_resource(self, resource: ResourceConfig, ...):
    if resource.resource_type == ResourceType.MY_NEW_TYPE:
        # Your processing logic
        return value
```

### Adding Config-Specific Utilities

1. **Create file** `.scrapai/utils/{config_name}_utils.py`:
```python
def custom_method(value):
    """Custom logic for this config"""
    return processed_value
```

2. **Methods automatically loaded** when executing that config

3. **AI can create** these via `write_custom_method` tool

---

## 🏛️ Feature Module Architecture

### Understanding Feature Modules

**Feature modules** are self-contained, high-level capabilities that extend ScrapAI's functionality:

- **`ai_analyzer/`** - Creates reusable scraping configurations (saves to files)
- **`ai_scraper/`** - Direct data extraction without configs (returns JSON immediately) ✅
- **`ai_validator/`** - Validates and improves existing configs (planned)
- **`ai_optimizer/`** - Optimizes configs for performance (planned)

### Module Structure Pattern

Each feature module follows this pattern:

```
feature_name/
├── __init__.py              # Export main class
├── main_class.py            # Main feature class (like IntelligentAnalyzer)
├── prompts.py               # Feature-specific AI prompts (optional)
├── parser.py                # Response parsing (optional)
└── helpers.py               # Helper utilities (optional)
```

### Module Requirements

1. **Main Class**: Must have a main class that represents the feature
2. **Initialization**: Takes `config_manager`, `service_config`, `proxies`, `enable_logging`
3. **Agent Integration**: Uses `Agent` class for AI model calls
4. **Public API**: Exposes clear public methods for client use

### Module Lifecycle

1. **Initialization**: Created in `ScrapAIClient.__init__()` if AI service provided
2. **Usage**: Called via client methods (e.g., `client.add_config()` uses `analyzer`)
3. **Independence**: Modules can use each other but aren't required
4. **Shared Resources**: All modules share `ConfigManager`, `Agent`, utilities

### Example: Complete Feature Module

See `ai_analyzer/` as reference:
- **Main class**: `IntelligentAnalyzer` in `analyzer.py`
- **Prompts**: `SystemPrompt` in `system_prompt.py`
- **Parsing**: `XMLConfigParser` in `xml_parser.py`
- **Integration**: Used in `ScrapAIClient` via `self.analyzer`

This pattern can be replicated for `ai_scraper`, `ai_validator`, etc.

---

## 📋 TODO / Known Issues

### High Priority
- [ ] **Fix `run_config_test()` in AgentTools** - Currently placeholder, needs integration with ConfigRunner
- [ ] **Improve XML format compliance** - Some AI models still return plain text instead of XML
- [ ] **Better error handling** - More graceful degradation when AI doesn't follow format
- [ ] **Content reduction optimization** - Further optimize content samples sent to AI

### Medium Priority
- [ ] **Browser initialization in AgentTools** - Handle browser/context for rendered pages in tests
- [ ] **Schema field alignment** - Ensure `ResourceConfig` fields match processor expectations
- [ ] **Conversation log cleanup** - Remove duplicate log entries
- [ ] **Enhanced validation feedback** - Better error messages for AI when configs are invalid

### Low Priority / Nice to Have
- [ ] **Export configs to YAML** - Alternative format support
- [ ] **Config versioning** - Track config versions and changes
- [ ] **Batch URL processing** - Process multiple URLs in parallel
- [ ] **Config templates** - Pre-built templates for common scenarios
- [ ] **Metrics dashboard** - Visualize extraction results
- [ ] **Rate limiting** - Built-in rate limiting for API calls
- [ ] **Config testing suite** - Automated tests for all configs

### Documentation
- [ ] **API reference** - Complete API documentation
- [ ] **Video tutorials** - Walkthrough videos
- [ ] **Best practices guide** - Common patterns and anti-patterns
- [ ] **Troubleshooting guide** - Common issues and solutions

---

## 🏗️ Architecture Decisions

### Why Configuration-Driven?
- **Separation of concerns**: Configs define WHAT to extract, code handles HOW
- **Reusability**: Same extraction logic for different sources
- **Testability**: Easy to test individual configs
- **Maintainability**: Update configs without code changes

### Why XML for AI Communication?
- **Structured**: Unambiguous format for complex nested data
- **Validated**: Easy to parse and validate
- **Extensible**: Can add new tags without breaking existing parsers
- **AI-Friendly**: Most models handle XML better than JSON in prompts

### Why Multiple Resources per Metric?
- **Resilience**: If primary source fails, fallback kicks in
- **Redundancy**: Multiple ways to get same data
- **Testing**: Easy to test alternative extraction methods

### Why Dynamic Action Collection?
- **Flexibility**: Add new transformations without code changes
- **Discoverability**: AI can see all available methods
- **Modularity**: Base actions + config-specific actions

---

## 🔍 Key Concepts

### Resources vs Metrics
- **Resource**: One way to extract data (API endpoint, XPath selector, etc.)
- **Metric**: What data you want (e.g., "transaction_count")
- **Relationship**: One metric can have multiple resources (fallback chain)

### Entities
- **Entity**: Logical grouping of metrics (e.g., "main", "secondary")
- **Use case**: Organize related metrics together
- **Output**: Each entity+metric combination becomes one row in results

### Actions vs Pre-Actions
- **Pre-actions**: Applied BEFORE extraction (e.g., parse embedded JSON from script tag)
- **Actions**: Applied AFTER extraction (e.g., convert "1.5K" to 1500)
- **Order**: Pre-actions → Extract → Actions → Return value

### API Path Syntax
- **LIST response**: `"last.field"`, `"first.field"`, `"second.field"`
- **OBJECT response**: `"field"` (direct field access)
- **NESTED**: `"data.items.last.value"` (navigate through keys)
- **Special keywords**: `first`, `last`, `second`, `second_last`, `length`, `[index]`

---

## 📚 Examples

See `examples/` directory for:
- **scenario_1_basic_scraping.py** - Basic config creation and execution
- **scenario_7_smartscraper.py** - Direct data extraction without configs (SmartScraper)
- **scenario_2_add_to_existing.py** - Adding metrics to existing configs
- **scenario_3_custom_utilities.py** - Creating custom transformation methods
- **scenario_4_multi_service.py** - Using different AI services
- **scenario_5_run_configs.py** - Executing multiple configs
- **scenario_6.py** - Advanced patterns

---

## 🤝 Contributing

### Development Setup
1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Install Playwright (optional): `playwright install chromium`
4. Run examples: `python examples/scenario_1_basic_scraping.py`

### Code Style
- Follow existing patterns
- Add docstrings for all public methods
- Update system prompt when adding new tools
- Test with multiple AI services if possible

### Testing
- Test new features with `examples/`
- Verify XML format compliance
- Check error handling
- Test resource fallback scenarios

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- Inspired by bronze layer data engineering patterns
- Uses similar concepts to daap-esg project architecture
- Built with OpenAI-compatible API standard for multi-service support

---

## 👨‍💻 About the Author

**Zohaib Yousaf** - Full Stack Developer & Data Engineer

Passionate about building intelligent systems that automate complex workflows. ScrapAI combines expertise in web scraping, AI integration, and data engineering to make data extraction accessible to everyone.

- **GitHub**: [@zohaib3249](https://github.com/zohaib3249)
- **Email**: chzohaib136@gmail.com

---

**Version**: 0.2.0  
**Last Updated**: December 2024
