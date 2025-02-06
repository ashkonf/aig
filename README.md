<div align="center">

# 🤖 GitAI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Pytest](https://img.shields.io/badge/pytest-✓-brightgreen)](https://docs.pytest.org)
[![Pyright](https://img.shields.io/badge/pyright-✓-green)](https://github.com/microsoft/pyright)
[![Ruff](https://img.shields.io/badge/ruff-✓-blue?logo=ruff)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Build Status](https://img.shields.io/github/actions/workflow/status/ashkonf/gai/ci.yml?branch=main)](https://github.com/ashkonf/gai/actions/workflows/ci.yml?query=branch%3Amain)
[![codecov](https://codecov.io/github/ashkonf/gai/graph/badge.svg?token=7Y596J8IYZ)](https://codecov.io/github/ashkonf/)

`gai` is a command-line tool that uses Google's Gemini 2.5 Pro to provide AI assistance for common Git operations. It helps you
write better commit messages, understand your commit history, and find out why code was changed. `gai` also acts as a transparent wrapper around `git`, so you can use it for all your daily git commands.

</div>

## 🗺️ Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
  - [API Key](#api-key)
  - [Branch Prefix](#branch-prefix)
- [Usage](#usage)
  - [`gai commit`](#gai-commit)
  - [`gai stash`](#gai-stash)
  - [`gai log`](#gai-log)
  - [`gai blame <file> <line>`](#gai-blame-file-line)
  - [`gai review`](#gai-review)
  - [`gai config`](#gai-config)
  - [`gai test`](#gai-test)
  - [Git Passthrough](#git-passthrough)
- [Development](#development)
- [License](#license)
- [Contributing](#contributing)


## ✨ Features

- ✍️ **`gai commit`**: Generates a concise and conventional commit message from your staged changes.
- 📦 **`gai stash`**: Generates a stash message from your unstaged changes.
- 📜 **`gai log`**: Summarizes the last 10 commits in natural language.
- 🕵️ **`gai blame <file> <line>`**: Explains why a specific line of code was changed.
- 👨‍💻 **`gai review`**: Provides a code review on your staged changes.
- ✨ **`gai submit`**: Creates a pull request with an AI-generated title and description.
- 🔧 **`gai config`**: Manages configuration settings, like branch prefixes.
- ✅ **`gai test`**: Runs pre-commit hooks on all files.
- 👉 **Git Passthrough**: Use `gai` as a drop-in replacement for `git`. Any command not native to `gai` is passed directly to `git`.

## 🚀 Installation

`gai` is a command-line tool that can be installed using `pipx`. If you don't have `pipx` installed, you can install it with `pip`:
```bash
pip install --user pipx
```

1.  Clone the repository:
    ```bash
    git clone https://github.com/ashkonf/gai.git
    cd gai
    ```

2.  Install the package:
    ```bash
    pipx install .
    ```

## ⚙️ Configuration

### API Key

`gai` requires a Google Gemini API key.

1.  Obtain a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
2.  Set the API key as an environment variable. You can use either `GEMINI_API_KEY` or `GOOGLE_API_KEY`.
    ```bash
    export GEMINI_API_KEY="your-api-key-here"
    ```
3.  Alternatively, you can create a `.env` file in the project root and add your key there:
    ```
    GEMINI_API_KEY="your-api-key-here"
    ```
4. If the API key is not found, `gai` will prompt you for it and save it to a `.env` file for future use.

### Branch Prefix

You can configure a prefix for all new branches created with `gai checkout -b` or `gai branch`. This is useful for teams that follow a branch naming convention (e.g. `username/`). See the [`gai config`](#gai-config) section for more details.

## 👨‍💻 Usage

### `gai commit`

Generates a commit message based on your staged changes.

1.  Stage your changes with `git add`.
2.  Run the command:
    ```bash
    gai commit
    ```
3.  The tool will suggest a commit message. Review it and type 'y' to accept and commit. Use the `-y` flag to bypass the confirmation prompt. You can also use the `--date` flag to override the author date of the commit (e.g. `gai commit --date="2025-01-01 12:00:00"`).

The first time `gai commit` is run, it will install pre-commit hooks if they have not been installed already.

### `gai stash`

Generates a stash message based on your unstaged changes.

1.  Make changes to your tracked files.
2.  Run the command:
    ```bash
    gai stash
    ```
3.  The tool will suggest a stash message. Review it and type 'y' to accept and stash. Use the `-y` flag to bypass the confirmation prompt.


### `gai log`

Summarizes the last 10 commits into a human-readable list of changes.

```bash
gai log
```

### `gai blame <file> <line>`

Explains *why* a specific line of code was last modified by analyzing the `git blame` output for that line.

```bash
gai blame main.py 115
```

### `gai review`

Provides a code review on your staged changes.

1.  Run the command:
    ```bash
    gai review
    ```

### `gai submit`

Creates a pull request with an AI-generated title and body. This command requires the `gh` command-line tool to be installed.

1.  Push your changes to a remote branch.
2.  Run the command:
    ```bash
    gai submit
    ```
3. The tool will suggest a title and body. Review them and type 'y' to accept and create the pull request. Use the `-y` flag to bypass the confirmation prompt.

### `gai config`

Sets configuration options for `gai`.

To set a branch prefix:
```bash
gai config --branch-prefix "ashkonf"
```
Now, when you run `gai checkout -b new-feature` or `gai branch new-feature`, the branch will be named `ashkonf/new-feature`.

To unset the branch prefix:
```bash
gai config --branch-prefix ""
```

### `gai test`

Runs all configured pre-commit hooks on your entire repository.

```bash
gai test
```

### Git Passthrough

`gai` can be used as a drop-in replacement for `git`. Any command that is not a special `gai` command (like `commit`, `log`, etc.) will be passed through to `git`.

For example, `gai status` is equivalent to `git status`.

## 🛠️ Development

To set up the development environment, follow these steps:

1. Clone the repository and navigate into the directory.
2. Install the project in editable mode with development dependencies:
   ```bash
   pipx install -e .[dev]
   ```
3. The project uses the following development tools:
    - `pytest` for running tests.
    - `pyright` for static type checking.
    - `ruff` for linting and formatting.
    - `pre-commit` to enforce standards before each commit.

To run the test suite:
```bash
uv run pytest
```

To run pre-commit hooks on all files:
```bash
gai test
```

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! To get started:

1. **Fork the repository** and create your branch from `main`.
2. **Install development dependencies**:
    ```bash
    pipx install -e .[dev]
    ```
3. **Run tests and pre-commit hooks** before submitting a PR:
    ```bash
    uv run pytest
    pre-commit run --all-files
    ```
4. **Open a pull request** with a clear description of your changes.

Please ensure your code is well-tested and follows the existing style. For major changes, open an issue first to discuss your ideas.

Thank you for helping improve `gai`!
