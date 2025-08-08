<div align="center">

# 🤖 AI Git

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Pytest](https://img.shields.io/badge/pytest-✓-brightgreen)](https://docs.pytest.org)
[![Pyright](https://img.shields.io/badge/pyright-✓-green)](https://github.com/microsoft/pyright)
[![Ruff](https://img.shields.io/badge/ruff-✓-blue?logo=ruff)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Build Status](https://img.shields.io/github/actions/workflow/status/ashkonf/aig/ci.yml?branch=main)](https://github.com/ashkonf/aig/actions/workflows/ci.yml?query=branch%3Amain)
[![codecov](https://codecov.io/github/ashkonf/aig/graph/badge.svg?token=7Y596J8IYZ)](https://codecov.io/github/ashkonf/)

**`aig` is a command-line tool that brings the power of Google, OpenAI, and Anthropic to your Git workflow.** It acts as a transparent wrapper around `git`, helping you write better commit messages, understand your commit history, and streamline your development process.

</div>

## 🗺️ Table of Contents

- [🤔 Why `aig`](#-why-aig)
- [✨ Features](#-features)
- [🚀 Installation](#-installation)
- [⚙️ Configuration](#️-configuration)
- [👨‍💻 Usage](#-usage)
- [🛠️ Development](#-development)
- [📄 License](#-license)
- [🤝 Contributing](#-contributing)
- [🙏 Acknowledgements](#-acknowledgements)
- [🗺️ Roadmap](#-roadmap)

---

## 🤔 Why `aig`?

`aig` enhances your existing Git workflow with AI-powered features without requiring you to learn a new set of commands.

-   **Seamless Integration**: Acts as a drop-in replacement for `git`. You can even alias `git` to `aig` for a fully integrated experience.
-   **AI-Powered Commits**: Generate clear, conventional commit messages from your staged changes automatically. Backdated commits are easily supported too.
-   **Code Insights**: Get quick summaries of your commit history (`aig log`), understand the "why" behind code changes (`aig blame`), and get a code review on your work (`aig review`).

## ✨ Features

-   ✍️ **`aig commit`**: Generates a concise and conventional commit message from your staged changes.
-   📦 **`aig stash`**: Generates a stash message from your unstaged changes.
-   📜 **`aig log`**: Summarizes the last 10 commits in natural language.
-   🕵️ **`aig blame <file> <line>`**: Explains why a specific line of code was changed.
-   👨‍💻 **`aig review`**: Provides a code review on your staged changes.
-   🔧 **`aig config`**: Manages configuration settings, like branch prefixes.
-   ✅ **`aig test`**: Runs pre-commit hooks on all files.
-   👉 **Git Passthrough**: Use `aig` as a drop-in replacement for `git`. Any command not native to `aig` is passed directly to `git`.

---

## 🚀 Installation

`aig` is a command-line tool that can be installed using `pipx`.

```bash
pipx install git+https://github.com/ashkonf/aig.git
```

## ⚙️ Configuration

`aig` supports Google, OpenAI, and Anthropic as AI providers. You can configure the tool to use your preferred provider by setting the appropriate environment variables.

### Model Provider

`aig` automatically selects the AI provider based on which API keys are available in your environment. You do **not** need to set a provider manually—just set the API key(s) for the provider(s) you want to use.

If you have multiple API keys set, `aig` will use the first available provider in this order: OpenAI, Anthropic, then Google.

### API Keys

`aig` requires an API key for your chosen provider.

-   **Google**:
    1.  Obtain a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
    2.  Set the `GEMINI_API_KEY` or `GOOGLE_API_KEY` environment variable.

-   **OpenAI**:
    1.  Obtain an API key from your [OpenAI Dashboard](https://platform.openai.com/api-keys).
    2.  Set the `OPENAI_API_KEY` environment variable.

-   **Anthropic**:
    1.  Obtain an API key from your [Anthropic Console](https://console.anthropic.com/settings/keys).
    2.  Set the `ANTHROPIC_API_KEY` environment variable.

You can add the environment variables to your shell's configuration file (e.g., `.zshrc`) or create a `.env` file in your project's root directory.

#### `.env` File Example

```
GEMINI_API_KEY="your-google-api-key-here"
```

If the API key is not found, `aig` will prompt you for it and save it to a `.env` file for future use.

### Model Name

You can specify a model by setting the `MODEL_NAME` environment variable. If not set, `aig` will use a default model for the selected provider:

-   **Google**: `gemini-1.5-pro-latest`
-   **OpenAI**: `gpt-4-turbo-2024-04-09`
-   **Anthropic**: `claude-3-opus-20240229`

Example:

```bash
export MODEL_NAME="gpt-3.5-turbo"
```

### Branch Prefix

You can configure a prefix for all new branches created with `aig checkout -b` or `aig branch`. This is useful for teams that follow a branch naming convention (e.g., `username/`). See the [`aig config`](#aig-config) section for more details.

---

## 👨‍💻 Usage

`aig` is designed to be a drop-in replacement for `git`. For a seamless experience, you can add an alias to your shell's configuration file (e.g., `.zshrc` or `.bashrc`):

```bash
alias git=aig
```

### `aig commit`

Generates a commit message based on your staged changes.

1.  Stage your changes with `git add`.
2.  Run the command:
    ```bash
    aig commit
    ```
3.  The tool will suggest a commit message. Review it and type 'y' to accept and commit. Use the `-y` flag to bypass the confirmation prompt. You can also use the `--date` flag to override the author date of the commit (e.g. `aig commit --date="2025-01-01 12:00:00"`).

The first time `aig commit` is run, it will install pre-commit hooks if they have not been installed already.

### `aig stash`

Generates a stash message based on your unstaged changes. Use the `-m` flag to provide your own message, or the `-y` flag to bypass the confirmation prompt.

1.  Make changes to your tracked files.
2.  Run the command:
    ```bash
    aig stash
    ```
3.  The tool will suggest a stash message. Review it and type 'y' to accept and stash. Use the `-y` flag to bypass the confirmation prompt.

### `aig log`

Summarizes the last 10 commits into a human-readable list of changes.

```bash
aig log
```

### `aig blame <file> <line>`

Explains *why* a specific line of code was last modified by analyzing the `git blame` output for that line.

```bash
aig blame main.py 115
```

### `aig review`

Provides a code review on your staged changes.

1.  Run the command:
    ```bash
    aig review
    ```


### `aig config`

Sets configuration options for `aig`.

To set a branch prefix:
```bash
aig config --branch-prefix "ashkonf"
```
Now, when you run `aig checkout -b new-feature` or `aig branch new-feature`, the branch will be named `ashkonf/new-feature`.

To unset the branch prefix:
```bash
aig config --branch-prefix ""
```

### `aig test`

Runs all configured pre-commit hooks on your entire repository.

```bash
aig test
```

### Git Passthrough

Any command that is not a special `aig` command (like `commit`, `log`, etc.) will be passed through to `git`. For example, `aig status` is equivalent to `git status`.

---

## 🛠️ Development

To set up the development environment, follow these steps:

1.  Clone the repository and navigate into the directory.
2.  Install the project in editable mode with development dependencies:
    ```bash
    pipx install -e .[dev]
    ```
3.  The project uses the following development tools:
    -   `pytest` for running tests.
    -   `pyright` for static type checking.
    -   `ruff` for linting and formatting.
    -   `pre-commit` to enforce standards before each commit.

To run the test suite:
```bash
uv run pytest
```

To run pre-commit hooks on all files:
```bash
aig test
```

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! To get started:

1.  **Fork the repository** and create your branch from `main`.
2.  **Install development dependencies**:
    ```bash
    pipx install -e .[dev]
    ```
3.  **Run tests and pre-commit hooks** before submitting a PR:
    ```bash
    uv run pytest
    pre-commit run --all-files
    ```
4.  **Open a pull request** with a clear description of your changes.

Please ensure your code is well-tested and follows the existing style. For major changes, open an issue first to discuss your ideas.

Thank you for helping improve `aig`!

## 🙏 Acknowledgements

This project was inspired by [aicommits](https://github.com/Nutlope/aicommits).

## 🗺️ Roadmap

* A GitHub PR submission wrapper that automatically generates the title and overview.
* AI-powered command autocomplete.
* Configurable system prompts.
