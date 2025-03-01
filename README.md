<div align="center">

# GitAI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Pytest](https://img.shields.io/badge/pytest-✓-brightgreen)](https://docs.pytest.org)
[![Pyright](https://img.shields.io/badge/pyright-✓-green)](https://github.com/microsoft/pyright)
[![Ruff](https://img.shields.io/badge/ruff-✓-blue?logo=ruff)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Build Status](https://img.shields.io/github/actions/workflow/status/ashkonf/gai/ci.yml?branch=main)](https://github.com/ashkonf/gai/actions/workflows/ci.yml?query=branch%3Amain)
[![codecov](https://codecov.io/github/ashkonf/gai/graph/badge.svg?token=7Y596J8IYZ)](https://codecov.io/github/ashkonf/)

`gai` is a command-line tool that uses Google's Gemini 2.5 Pro to provide AI assistance for common Git operations. It helps you 
write better commit messages, understand your commit history, and find out why code was changed.

</div>

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Development](#development)
- [Configuration](#configuration)
  - [Branch Prefix](#branch-prefix)
- [Usage](#usage)
  - [`gai commit`](#gai-commit)
  - [`gai log`](#gai-log)
  - [`gai blame <file> <line>`](#gai-blame-file-line)

## Features

- **`gai commit`**: Generates a concise and conventional commit message from your staged changes.
- **`gai log`**: Summarizes the last 10 commits in natural language.
- **`gai blame <file> <line>`**: Explains why a specific line of code was changed.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/gai-labs/gai-oss.git
    cd gai-oss
    ```

2.  Install the dependencies:
    ```bash
    pip install .
    ```

## Configuration

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

### Branch Prefix

You can configure a prefix for all new branches created with `gai checkout -b` or `gai branch`. This is useful for teams that follow a branch naming convention (e.g. `username/`).

```bash
git config --global gai.branch-prefix "feature/"
```

Now, when you run `gai checkout -b new-feature`, the branch will be named `feature/new-feature`.

## Usage

### `gai commit`

Generates a commit message based on your staged changes.

1.  Stage your changes with `git add`.
2.  Run the command:
    ```bash
    gai commit
    ```
3.  The tool will suggest a commit message. Review it and type 'y' to accept and commit.

The first time gai commit is run, it will install pre-commit hooks if they have not been installed already.

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

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

