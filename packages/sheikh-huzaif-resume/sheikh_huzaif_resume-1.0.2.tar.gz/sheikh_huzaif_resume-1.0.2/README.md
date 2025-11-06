# Terminal Resume

A modern, interactive Python CLI tool that displays your professional resume in a beautifully formatted terminal interface.

## ✨ Features

- 🎨 **Beautiful Output** - Rich text formatting with colors, tables, and panels
- 🚀 **Fast & Lightweight** - Built with Typer for optimal performance
- 💼 **Professional Display** - Showcase work experience, projects, skills, and education
- 📱 **Contact Information** - Easy access to your contact details
- 🧪 **Well Tested** - Comprehensive test suite with pytest
- 📦 **Easy Distribution** - Install via pip
- 🎯 **Type Safe** - Full type hints for better IDE support

## 📦 Installation

### From PyPI (when published)

```bash
pip install sheikh-huzaif-resume
```

### From Source

```bash
git clone https://github.com/sheikhhuzaif/terminal-resume
cd terminal-resume
pip install -e .
```

### For Development

```bash
pip install -e ".[dev]"
# or
make install-dev
```

## 🚀 Quick Start

After installation, you can use the CLI:

```bash
# Show help
sheikh-huzaif-resume --help

# Show version
sheikh-huzaif-resume --version

# Display contact information
sheikh-huzaif-resume contact

# Show professional summary
sheikh-huzaif-resume summary

# View work experience
sheikh-huzaif-resume work-exp

# Browse projects
sheikh-huzaif-resume projects

# Display education
sheikh-huzaif-resume education

# List skills
sheikh-huzaif-resume skills

# Show tool info
sheikh-huzaif-resume info
```

## 📖 Commands

### `contact`

Display contact information including email, phone, LinkedIn, and GitHub.

```bash
sheikh-huzaif-resume contact
```

### `summary`

Show professional summary and career overview.

```bash
sheikh-huzaif-resume summary
```

### `work-exp`

View detailed work experience with companies, roles, and achievements.

```bash
sheikh-huzaif-resume work-exp
```

### `projects`

Browse personal projects with descriptions, technologies, and links.

```bash
sheikh-huzaif-resume projects
```

### `education`

Display educational background and qualifications.

```bash
sheikh-huzaif-resume education
```

### `skills`

List technical skills organized by categories (languages, frameworks, tools, etc.).

```bash
sheikh-huzaif-resume skills
```

### `info`

Display information about the CLI tool.

```bash
sheikh-huzaif-resume info
sheikh-huzaif-resume info --verbose
```

## 🏗️ Project Structure

```
terminal-resume/
├── src/
│   └── resume/
│       ├── __init__.py
│       ├── cli.py              # Main CLI entry point
│       ├── data.py             # Resume data store
│       ├── commands/           # Command implementations
│       │   ├── __init__.py
│       │   ├── contact.py
│       │   ├── summary.py
│       │   ├── work_exp.py
│       │   ├── projects.py
│       │   ├── education.py
│       │   ├── skills.py
│       │   └── info.py
│       └── utils/              # Utility functions
│           ├── __init__.py
│           └── helpers.py
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_helpers.py
│   └── test_commands.py
├── requirements/
│   ├── requirements.txt        # Production dependencies
│   └── requirements-dev.txt    # Development dependencies
├── setup.py                    # Setup configuration
├── pyproject.toml             # Modern Python project config
├── pytest.ini                 # Pytest configuration
├── Makefile                   # Convenient commands
├── LICENSE                    # MIT License
└── README.md
```

## 🛠️ Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/sheikhhuzaif/terminal-resume.git
cd terminal-resume

# Install development dependencies
make install-dev

# Or manually
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Or directly with pytest
pytest
pytest --cov=resume --cov-report=html
```

### Code Quality

```bash
# Format code with Black
make format

# Lint code
make lint

# Or run individually
black src/resume tests
flake8 src/resume tests
mypy src/resume
```

### Running Locally

```bash
# Run directly
python -m resume.cli

# Or after installation
sheikh-huzaif-resume

# Using make
make run
```

## 🔧 Adding New Commands

1. Create a new file in `src/resume/commands/`:

```python
# src/resume/commands/mycommand.py
import typer
from rich.console import Console

console = Console()

def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """
    Description of your command.
    """
    console.print("[green]Command executed successfully![/green]")
```

2. Register it in `src/resume/cli.py`:

```python
from .commands import contact, summary, mycommand

app.command(name="mycommand")(mycommand.main)
```

3. Add tests in `tests/test_commands.py`

## 📦 Building and Publishing

### Build Distribution

```bash
# Build wheel and source distribution
make build

# Or manually
python -m build
```

### Publish to PyPI

```bash
# Test on TestPyPI first
make publish-test

# Publish to PyPI
make publish

# Or manually with twine
python -m twine upload dist/*
```

## 🧰 Dependencies

### Core Dependencies
- **typer[all]==0.9.0** - CLI framework with great UX
- **rich==13.7.0** - Beautiful terminal formatting
- **questionary==2.0.1** - Interactive prompts
- **pyfiglet==1.0.2** - ASCII art text

### Development Dependencies
- **pytest==7.4.3** - Testing framework
- **pytest-cov==4.1.0** - Code coverage
- **black==23.12.1** - Code formatter
- **flake8==7.0.0** - Linter
- **mypy==1.8.0** - Type checker

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📧 Contact

Sheikh Huzaif - sheikhhuzaif007@gmail.com

Project Link: [https://github.com/sheikhhuzaif/terminal-resume](https://github.com/sheikhhuzaif/terminal-resume)
