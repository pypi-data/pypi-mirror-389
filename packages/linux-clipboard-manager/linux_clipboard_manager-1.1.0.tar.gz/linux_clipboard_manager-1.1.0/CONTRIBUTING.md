# Contributing to Smart Clipboard Manager

Thank you for your interest in contributing to Smart Clipboard Manager! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Bugs

- Use the [GitHub Issues](https://github.com/your-username/smart-clipboard-manager/issues) page
- Provide detailed information about the bug
- Include steps to reproduce the issue
- Specify your operating system and Python version
- Add screenshots if applicable

### Suggesting Features

- Open an issue with the "enhancement" label
- Describe the feature in detail
- Explain why the feature would be useful
- Consider if it fits the project's scope

### Code Contributions

1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/smart-clipboard-manager.git
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

4. **Test your changes**
   ```bash
   pytest tests/
   ```

5. **Commit your changes**
   ```bash
   git commit -m "Add your feature description"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Provide a clear description of changes
   - Reference any related issues
   - Include screenshots for UI changes

## 🛠️ Development Setup

### Prerequisites

- Python 3.7 or higher
- Git
- pip

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/smart-clipboard-manager.git
   cd smart-clipboard-manager
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install in development mode**
   ```bash
   pip install -e .
   ```

### Running the Application

```bash
# Run the main application
python main.py

# Run with GUI only
python main.py --show-ui
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_storage.py
```

## 📝 Code Style

Follow these guidelines for consistent code style:

### Python Code

- Use 4 spaces for indentation
- Maximum line length: 88 characters
- Use docstrings for all functions and classes
- Follow PEP 8 style guide

### Example Function

```python
def example_function(param1: str, param2: int) -> bool:
    """
    Example function with proper documentation.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: If parameters are invalid
    """
    if not param1:
        raise ValueError("param1 cannot be empty")
    
    return param2 > 0
```

### Commit Messages

Use clear and descriptive commit messages:

```
feat: Add auto-refresh functionality
fix: Resolve SQL query error in search method
docs: Update installation instructions
test: Add tests for clipboard storage
refactor: Improve code organization
```

## 🧪 Testing

### Writing Tests

- Write tests for all new functionality
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies

### Example Test

```python
def test_clipboard_storage_save_and_retrieve():
    """Test saving and retrieving clipboard items."""
    storage = ClipboardStorage(":memory:")
    
    # Save an item
    clip_id = storage.save_clip("test content", "text")
    assert clip_id is not None
    
    # Retrieve the item
    history = storage.get_history()
    assert len(history) == 1
    assert history[0]["content"] == "test content"
```

## 📚 Documentation

### Updating Documentation

- Keep README.md up to date
- Document new features in the appropriate sections
- Update API documentation for new functions
- Include examples for complex features

### Code Documentation

- Use docstrings for all public functions and classes
- Include type hints where appropriate
- Document complex algorithms with inline comments

## 🏗️ Project Structure

```
smart-clipboard-manager/
├── src/                    # Source code
├── tests/                  # Test suite
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── requirements.txt        # Dependencies
├── setup.py               # Package configuration
├── main.py                # Entry point
├── README.md              # Project documentation
├── CONTRIBUTING.md        # Contributing guidelines
└── LICENSE                # License file
```

## 🚀 Release Process

### Version Bumping

1. Update version in setup.py
2. Update changelog in README.md
3. Create a git tag
4. Create a GitHub release

### Publishing to PyPI

```bash
# Build the package
python setup.py sdist bdist_wheel

# Upload to PyPI
twine upload dist/*
```

## 🤔 Getting Help

- Create an issue for questions or problems
- Join our discussions on GitHub
- Check existing issues and documentation
- Reach out to maintainers

## 📋 Review Process

### Pull Request Review

- All PRs require at least one review
- Automated tests must pass
- Code must follow style guidelines
- Documentation must be updated

### Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] PR description is detailed

## 🎉 Recognition

Contributors will be recognized in:

- README.md contributors section
- Release notes
- Project documentation

Thank you for contributing to Smart Clipboard Manager! 🙏
