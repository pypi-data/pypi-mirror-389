# ZETA CLI

**ZETA CLI — the most accessible AI terminal agent for learning and building.**

[![PyPI version](https://img.shields.io/pypi/v/zeta-cli.svg)](https://pypi.org/project/zeta-cli/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

ZETA CLI is an AI-powered terminal agent that makes coding accessible to everyone. Whether you're learning to code or building projects, ZETA helps you accomplish tasks through natural language interaction with multiple LLM providers.

## Motivation

Coding should be accessible to everyone, regardless of technical background. ZETA CLI bridges the gap between intent and implementation by providing an intelligent terminal agent that understands natural language and executes tasks safely. With support for multiple AI providers and built-in learning features, ZETA empowers users to learn coding concepts while building real projects.
  
## Installation

### From PyPI (Recommended)

```bash
pip install zeta-cli
```

### Using uv

```bash
uv tool install zeta-cli
```

### From Source

```bash
git clone https://github.com/SukinShetty/Zeta-CLI.git
cd Zeta-CLI
pip install -e .
```

## Quickstart

### 1. Choose Your Working Directory

**Important:** ZETA creates files in your current directory. Before running commands, navigate to a folder where you want your files created.

**Windows:**
```powershell
# Navigate to Desktop (recommended for beginners)
cd $env:USERPROFILE\Desktop

# Or navigate to Documents
cd $env:USERPROFILE\Documents

# Or create a new project folder
cd $env:USERPROFILE\Desktop
mkdir MyProjects
cd MyProjects
```

**Mac/Linux:**
```bash
# Navigate to Desktop
cd ~/Desktop

# Or navigate to Documents
cd ~/Documents

# Or create a new project folder
cd ~/Desktop
mkdir MyProjects
cd MyProjects
```

**Check your current directory:**
- Windows: `pwd` or `Get-Location`
- Mac/Linux: `pwd`

**Why this matters:** Files created by ZETA will appear in whatever folder you're currently in. Using Desktop or Documents makes it easy to find your files later.

### 2. Setup

Configure your preferred AI provider:

```bash
zeta setup
```

This interactive wizard helps you set up:
- Google Gemini (free tier available)
- OpenAI (GPT-4, GPT-3.5)
- Anthropic Claude
- Ollama (local models)

### 3. Run Your First Task

```bash
zeta run "say hello"
```

ZETA will process your request and execute the task.

### 4. Teaching Mode

Get detailed explanations of coding concepts:

```bash
zeta teach
```

Or enable teaching mode for specific tasks:

```bash
zeta run "create a calculator" --teach
```

### 5. View Learning Log

Track your coding journey:

```bash
zeta log
```

### Complete Example

```bash
# 1. Navigate to your project folder (IMPORTANT!)
cd ~/Desktop  # Mac/Linux
# or
cd $env:USERPROFILE\Desktop  # Windows

# 2. Setup (first time only)
zeta setup

# 3. Run a task (files will be created in current folder)
zeta run "create a simple to-do app"

# 4. Run with teaching mode
zeta run "build a REST API" --teach

# 5. Run with code review
zeta run "write a Python function" --critic

# 6. View your learning history
zeta log
```

**Finding Your Files:** After ZETA creates files, they'll be in the folder you navigated to in step 1. On Windows, check your Desktop. On Mac/Linux, check your Desktop folder.

## Supported Providers

ZETA CLI supports multiple LLM providers, giving you flexibility and choice:

| Provider | Model Examples | Setup Required |
|----------|---------------|----------------|
| **Google Gemini** | `gemini-1.5-flash`, `gemini-1.5-pro` | API key (free tier available) |
| **OpenAI** | `gpt-4o-mini`, `gpt-4`, `gpt-3.5-turbo` | API key |
| **Anthropic Claude** | `claude-3-5-sonnet-20241022` | API key |
| **Ollama** | Any local model (e.g., `llama3.2`, `mistral`) | Ollama installed locally |

Run `zeta setup` to configure your preferred provider. You can switch providers at any time by running the setup command again.

## Features

- **Multi-Provider Support**: Choose from Google Gemini, OpenAI, Anthropic Claude, or local Ollama
- **Smart Clarification**: Automatically detects vague requests and asks helpful questions
- **Teaching Mode**: Detailed explanations with plain English definitions
- **Code Review**: Optional critic mode for quality and security checks
- **Learning Log**: Automatic tracking of your coding journey
- **Safe Operations**: File operations require confirmation before execution

## Troubleshooting

### Files Not Being Created

If ZETA says it created files but you can't find them:

1. **Check your current directory:**
   ```powershell
   # Windows
   Get-Location
   
   # Mac/Linux
   pwd
   ```

2. **Navigate to a proper folder before running ZETA:**
   ```powershell
   # Windows - go to Desktop
   cd $env:USERPROFILE\Desktop
   
   # Mac/Linux - go to Desktop
   cd ~/Desktop
   ```

3. **Avoid system directories** like `C:\WINDOWS\system32` - these require administrator permissions.

4. **Find your files:** After running ZETA, check the folder you navigated to. Files will be created there.

### Command Not Found (Windows)

If `zeta` command is not found on Windows:

```powershell
# Use Python module instead
python -m zeta run "task"
```

### Provider Connection Issues

**Google Gemini / OpenAI / Anthropic:**
- Verify your API key is set correctly: `zeta setup`
- Check your internet connection
- Ensure you have available API quota

**Ollama:**
- Ensure Ollama is running: `ollama serve`
- Verify model is pulled: `ollama list`
- Check Ollama is accessible: `curl http://localhost:11434/api/tags`

### Configuration Not Persisting

If settings don't persist between sessions:

```bash
# Check configuration file
cat ~/.zeta_config.json

# Re-run setup
zeta setup
```

### Model Not Found

If you see "model not found" errors:

- **Google Gemini**: Use `gemini-1.5-flash` or `gemini-1.5-pro` (without `-latest` suffix)
- **OpenAI**: Use `gpt-4o-mini` or `gpt-4`
- **Ollama**: Pull the model first: `ollama pull llama3.2`

## Roadmap

### Plugins
Plugin system for custom tools and extensions, enabling community-contributed functionality.

### Cloud
Cloud-hosted ZETA instances for teams and organizations, with shared configurations and collaboration features.

### Pro
Advanced features including:
- Custom model fine-tuning
- Extended context windows
- Priority support
- Advanced analytics

### Enterprise
Enterprise-grade features:
- Self-hosted deployments
- SSO integration
- Audit logs
- Compliance certifications
- Dedicated support

### Store
Marketplace for:
- Pre-built project templates
- Custom tool integrations
- Provider configurations
- Learning modules

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Run tests: `pytest tests/ -v`
5. Commit: `git commit -m "Add your feature"`
6. Push: `git push origin feature/your-feature`
7. Open a Pull Request

## License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.

## Links

- **PyPI Package**: https://pypi.org/project/zeta-cli/
- **GitHub Repository**: https://github.com/SukinShetty/Zeta-CLI
- **Issues**: https://github.com/SukinShetty/Zeta-CLI/issues
- **Discussions**: https://github.com/SukinShetty/Zeta-CLI/discussions

## Acknowledgments

Built with:
- [LangChain](https://www.langchain.com/) and [LangGraph](https://github.com/langchain-ai/langgraph) for LLM orchestration
- [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- [Click](https://click.palletsprojects.com/) for CLI framework

---

**Copyright 2025 Sukin Shetty**
