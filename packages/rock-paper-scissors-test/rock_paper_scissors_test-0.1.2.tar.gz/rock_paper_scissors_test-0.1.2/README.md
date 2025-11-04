# Rock Paper Scissors

<p align="center">
    <a href="https://pypi.org/project/rock_paper_scissors_test/">
        <img alt="PyPI" src="https://img.shields.io/pypi/v/rock_paper_scissors_test?color=blue">
    </a>
    <a href="https://pypi.org/project/rock_paper_scissors_test/">
        <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/rock_paper_scissors_test">
    </a><a href="https://github.com/filmingstudio/rock_paper_scissors/blob/main/LICENSE">
        <img alt="License" src="https://img.shields.io/badge/License--yellow.svg">
    </a>
</p>

A game of RPS.

---

## Features
- **Feature A:** Describe the primary capability of your project.
- **Feature B:** Mention another important aspect.
- **Developer Experience:** Developed with ruff, mypy, pre-commit, and commitizen for high-quality code.

---

## Installation

### From PyPI (Recommended)

```bash
pip install rock_paper_scissors_test
```

### From Source

You can install Rock Paper Scissors by cloning the repository directly or using pre-built wheel files.

**Prerequisites:** This project requires [uv](https://github.com/astral-sh/uv) for dependency management.

#### Option 1: Clone and Build

1. Clone the repository:
   ```bash
   git clone https://github.com/filmingstudio/rock_paper_scissors.git
   cd rock_paper_scissors
   ```

2. Install the project and its dependencies:
   ```bash
   uv sync
   ```

#### Option 2: Install from Pre-built Wheels

Pre-built wheel files are attached to each GitHub release. You can download and install them directly:

1. Go to the [GitHub releases page](https://github.com/filmingstudio/rock_paper_scissors/releases)
2. Download the `.whl` file from the latest release
3. Install using pip:
   ```bash
   pip install path/to/downloaded/rock_paper_scissors-*.whl
   ```

---

## Usage

```
Usage examples wiil be added later.
```

---

## Development

This project uses modern Python development tools such as:

- **[uv](https://github.com/astral-sh/uv)** for dependency management
- **[ruff](https://github.com/astral-sh/ruff)** for linting and formatting  
- **[mypy](https://mypy.readthedocs.io/)** for type checking
- **[pre-commit](https://pre-commit.com/)** for git hooks
- **[commitizen](https://commitizen-tools.github.io/commitizen/)** for conventional commits

### Setting up for development:

1. Clone the repository:
   ```bash
   git clone https://github.com/filmingstudio/rock_paper_scissors.git
   cd rock_paper_scissors
   ```

2. Setup developement environment using Makefile:
   ```bash
   make setup
   ```
   
3. Start developing!

---

## Dependencies

All project dependencies are managed via [`pyproject.toml`](pyproject.toml) and use Python 3.10+.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Contributing

Contributions, bug reports, and feature requests are welcome!
Please open an issue or submit a pull request on [GitHub](https://github.com/filmingstudio/rock_paper_scissors).
