# Aidex

A template placeholder Python package.

## Installation

```bash
pip install aidex
```

## Usage

```python
import aidex

# Say hello
print(aidex.hello("World"))
# Output: Hello, World!

# Get version
print(aidex.get_version())
# Output: 0.1.0
```

## Development

### Setup

1. Clone the repository
2. Install in development mode:

```bash
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
isort .
```

### Type Checking

```bash
mypy aidex
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.