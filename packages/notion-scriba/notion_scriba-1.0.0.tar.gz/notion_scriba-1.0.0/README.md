# 🏛️ Notion Scriba

**AI-powered documentation generator with multi-LLM support and Notion integration**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## ✨ Features

- 🤖 **Multi-LLM Support** - Choose from OpenAI, Claude, Gemini, DeepSeek, or local models (Ollama)
- 🔍 **Automatic Code Analysis** - Extracts classes, functions, APIs from your codebase
- 📝 **Enterprise Templates** - 4 professional doc templates for different audiences
- 🌍 **Bilingual Generation** - Simultaneous Italian + English documentation
- 🔒 **Safe Updates** - Automatic backup before overwriting Notion pages
- 🔀 **Merge Mode** - Preserves existing content when updating
- 💰 **Cost Flexibility** - From premium (GPT-4) to ultra-cheap (DeepSeek) to free (Ollama)

---

## 🚀 Quick Start

### Installation

```bash
# Basic installation (OpenAI + DeepSeek support)
pip install notion-scriba

# With Anthropic Claude support
pip install notion-scriba[anthropic]

# With Google Gemini support
pip install notion-scriba[google]

# With all providers
pip install notion-scriba[all]

# From source
git clone https://github.com/dbaldoni/notion-scriba
cd notion-scriba
pip install -e .
```

### Configuration

**Option 1: Interactive Setup (Recommended)** 🎯

```bash
# Run the setup wizard
scriba-setup

# Follow the prompts to:
# 1. Enter your Notion integration token
# 2. Choose Pages or Database mode
# 3. Enter your page/database IDs
# 4. Validate connection
# 5. Save configuration
```

**Option 2: Manual Setup** 📝

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Add your credentials:
```bash
# Notion configuration
NOTION_TOKEN=secret_your-token-here
NOTION_PAGE_ID=your-page-id     # For single page mode
NOTION_DB=your-database-id      # For database mode

# Choose your LLM provider
LLM_PROVIDER=openai  # or: anthropic, google, deepseek, ollama
OPENAI_API_KEY=sk-your-key-here
```

3. See detailed setup guide: [docs/notion_setup.md](docs/notion_setup.md)

---

### Basic Usage

```bash
# Generate documentation for a component
scriba --component myapp --template technical-deep-dive

# Use different LLM provider
scriba --provider anthropic --model claude-3-5-sonnet-20241022 \
  --component myapp

# Cost-effective option with DeepSeek
scriba --provider deepseek --component myapp

# Completely free with local Ollama
scriba --provider ollama --model llama3.1 --component myapp

# Interactive mode with file autocomplete
scriba -i

# Quick mode with custom prompt
scriba --quick "Generate API documentation for authentication module"
```

---

## 🤖 Supported LLM Providers

| Provider | Models | Pricing | Best For |
|----------|--------|---------|----------|
| **OpenAI** | GPT-4o, GPT-4-turbo, GPT-3.5 | $5-15/1M tokens | Premium quality |
| **Anthropic** | Claude 3.5 Sonnet, Opus, Haiku | $3-15/1M tokens | Long context |
| **Google** | Gemini 1.5 Pro, Flash | Free tier, then $1-7/1M | Cost-effective |
| **DeepSeek** | DeepSeek Chat, Coder | $0.14-0.28/1M tokens | Ultra cheap |
| **Ollama** | Llama 3.1, Mistral, CodeLlama | FREE (local) | Privacy & offline |

### Provider Setup

<details>
<summary><b>OpenAI (GPT-4, GPT-4o)</b></summary>

```bash
# Get API key from: https://platform.openai.com/api-keys
export OPENAI_API_KEY="sk-your-key-here"
scriba --provider openai --model gpt-4o --component myapp
```
</details>

<details>
<summary><b>Anthropic (Claude)</b></summary>

```bash
# Install: pip install notion-scriba[anthropic]
# Get API key from: https://console.anthropic.com/
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
scriba --provider anthropic --model claude-3-5-sonnet-20241022 --component myapp
```
</details>

<details>
<summary><b>Google (Gemini)</b></summary>

```bash
# Install: pip install notion-scriba[google]
# Get API key from: https://makersuite.google.com/app/apikey
export GOOGLE_API_KEY="your-key-here"
scriba --provider google --model gemini-1.5-pro --component myapp
```
</details>

<details>
<summary><b>DeepSeek (Cost-Effective)</b></summary>

```bash
# Get API key from: https://platform.deepseek.com/
export DEEPSEEK_API_KEY="your-key-here"
scriba --provider deepseek --model deepseek-chat --component myapp
```
</details>

<details>
<summary><b>Ollama (Local & Free)</b></summary>

```bash
# Install Ollama from: https://ollama.ai
# Pull model: ollama pull llama3.1
# Start Ollama: ollama serve

scriba --provider ollama --model llama3.1 --component myapp
```
</details>

---

## 📚 Documentation Templates

### 1. **Investment Grade** 📊
*For investors, C-level executives, board members*
- Business impact and ROI
- Market positioning
- Competitive advantages
- Risk assessment

### 2. **Technical Deep Dive** 🔧
*For senior developers, architects, technical leads*
- Architecture diagrams
- Implementation details
- Performance characteristics
- Integration patterns

### 3. **Business Value** 💼
*For product managers, business analysts, stakeholders*
- Use cases and workflows
- User benefits
- Cost savings
- Success metrics

### 4. **API Documentation** 🔌
*For integration engineers, external developers*
- Endpoint reference
- Authentication flow
- Code examples
- Error handling

---

## 🎯 CLI Reference

```bash
scriba [OPTIONS]

Options:
  # Component & Template
  --component TEXT          Component to document (e.g., authentication, api, dashboard)
  --template CHOICE         Template: investment-grade, technical-deep-dive, 
                           business-value, api-documentation

  # LLM Configuration
  --provider CHOICE         LLM provider: openai, anthropic, google, deepseek, ollama
  --model TEXT             Model name (default: provider-specific)
  --api-key TEXT           API key (or use environment variable)
  --temperature FLOAT      Generation temperature 0.0-1.0 (default: 0.3)
  --max-tokens INT         Maximum tokens to generate (default: 4000)

  # Workflow Options
  --interactive, -i        Interactive mode with file autocomplete
  --quick TEXT             Quick mode with direct prompt
  --no-refine              Skip interactive prompt refinement
  --auto-code-analysis     Enable automatic code analysis
  --no-code-analysis       Disable code analysis

  # Information
  --list-providers         Show available LLM providers
  --help                   Show this help message
```

## 📜 License

Notion Scriba is released under the GNU General Public License v3.0 (GPLv3).
You are free to use, modify, and distribute this software, but any
distributed modified versions must also be licensed under GPLv3.

See the full license in the `LICENSE` file.


---

## 🏗️ Architecture

```
notion-scriba/
├── src/notion_scriba/
│   ├── llm/                    # Multi-LLM abstraction layer
│   │   ├── base.py            # Abstract base class
│   │   ├── factory.py         # Provider factory
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   ├── google_provider.py
│   │   ├── deepseek_provider.py
│   │   └── ollama_provider.py
│   ├── code_analyzer.py       # Source code analysis
│   ├── doc_generator.py       # Documentation generation
│   ├── notion_client.py       # Notion API integration
│   ├── templates.py           # Documentation templates
│   ├── interactive_mode.py    # Interactive file selector
│   ├── setup_wizard.py        # Configuration wizard
│   └── cli.py                 # Command-line interface
├── tests/                     # Test suite
├── docs/                      # Documentation
└── examples/                  # Usage examples
```

---

## 🔧 Advanced Usage

### Custom Templates

```python
from notion_scriba import DocGenerator

generator = DocGenerator(provider="openai", model="gpt-4o")

custom_prompt = """
Generate documentation for {component} that includes:
1. Executive summary
2. Technical specifications
3. Usage examples
4. Performance benchmarks
"""

result = generator.generate(
    component="authentication",
    prompt=custom_prompt,
    temperature=0.4
)
```

### Programmatic Usage

```python
from notion_scriba.llm import LLMProviderFactory, LLMConfig

# Initialize provider
config = LLMConfig(
    api_key="your-key",
    model="gpt-4o",
    temperature=0.3,
    max_tokens=4000
)
provider = LLMProviderFactory.create("openai", config)

# Generate documentation
response = provider.generate(
    prompt="Write technical documentation for...",
    system_prompt="You are an expert technical writer..."
)

print(response)
```

---

## 🧪 Development

```bash
# Clone repository
git clone https://github.com/dbaldoni/notion-scriba
cd notion-scriba

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=notion_scriba

# Format code
black src/ tests/

# Lint
ruff check src/ tests/
```

---

## 🤝 Contributing

Contributions are welcome! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

This project is licensed under GPLv3. By contributing, you agree that your contributions will be licensed under the same license.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

##  Support

- 📚 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/dbaldoni/notion-scriba/issues)
- 💬 [Discussions](https://github.com/dbaldoni/notion-scriba/discussions)

---

<p align="center">
  <strong>🏛️ Notion Scriba</strong><br>
  <em>"Verba volant, scripta manent"</em><br>
  Made with ❤️ by <a href="https://github.com/dbaldoni">Davide Baldoni</a>
</p>
