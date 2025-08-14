# Contributing to Business Intelligence Platform

Thank you for your interest in contributing to the Business Intelligence Platform! This guide will help you get started with contributing to our AI-powered business analysis platform.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- Anthropic API key (for testing with actual AI models)
- Docker (optional, for containerized development)

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/business_intelligence_platform.git
   cd business_intelligence_platform
   ```

2. **Set up development environment**
   ```bash
   make setup-dev
   ```

3. **Install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run tests to verify setup**
   ```bash
   make test
   ```

## Contributing Guidelines

### Branch Naming Convention

Use descriptive branch names with prefixes:
- `feature/` - New features
- `bugfix/` - Bug fixes
- `hotfix/` - Critical fixes for production
- `refactor/` - Code refactoring
- `docs/` - Documentation updates
- `test/` - Test improvements

Examples:
- `feature/enhanced-financial-modeling`
- `bugfix/sequential-validation-error`
- `docs/api-documentation-update`

### Commit Message Convention

Follow conventional commits format:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Code style changes
- `refactor` - Code refactoring
- `test` - Test changes
- `chore` - Build/tooling changes

Examples:
```
feat(financial): add IRR calculation with Newton-Raphson method
fix(database): resolve connection timeout in production
docs(readme): update installation instructions
```

### Code Style

We use automated code formatting and linting:

```bash
# Format code
make format

# Check linting
make lint

# Type checking
make type-check
```

**Style Guidelines:**
- Line length: 100 characters
- Use type hints for function parameters and return values
- Follow PEP 8 conventions
- Use descriptive variable and function names
- Add docstrings for classes and functions

### Architecture Guidelines

When contributing to different components:

#### 1. Multi-Agent System
- Follow AG2/AutoGen patterns
- Maintain role-specific agent configurations
- Ensure tool integration compatibility

#### 2. Business Intelligence Tools
- Implement standardized tool interfaces
- Add comprehensive error handling
- Include input validation
- Write unit tests for all calculations

#### 3. Workflows
- Design for extensibility
- Implement proper state management
- Add progress tracking
- Include confidence scoring

#### 4. Database Layer
- Support both SQLite (dev) and PostgreSQL (prod)
- Use database abstraction patterns
- Implement proper migrations
- Add connection pooling for production

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run specific test categories
make test-unit
make test-integration

# Run with coverage
make test-coverage

# Run specific test file
python -m pytest tests/test_financial_tools.py -v
```

### Writing Tests

#### Test Structure
- Place tests in `tests/` directory
- Mirror source code structure
- Use descriptive test names

#### Test Categories
- **Unit Tests**: Test individual functions/classes
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows

#### Test Guidelines
```python
def test_feature_with_valid_input():
    """Test feature behavior with valid input."""
    # Arrange
    input_data = {"param": "value"}
    
    # Act  
    result = feature_function(input_data)
    
    # Assert
    assert result["status"] == "success"
    assert "expected_field" in result
```

#### Mocking
Use mocks for external dependencies:
```python
@patch('src.external_service.api_call')
def test_with_mocked_api(mock_api):
    mock_api.return_value = {"data": "test"}
    # Test implementation
```

### Test Coverage

Maintain **80%+ test coverage** for all new code:
- All business logic functions must have tests
- Error handling paths must be tested
- Integration points must be tested

## Documentation

### Code Documentation
- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Include parameter types and return values
- Add usage examples for complex functions

```python
def calculate_npv(cash_flows: List[float], discount_rate: float) -> float:
    """Calculate Net Present Value of cash flows.
    
    Args:
        cash_flows: List of cash flows including initial investment
        discount_rate: Annual discount rate as decimal (e.g., 0.1 for 10%)
    
    Returns:
        Net present value as float
        
    Example:
        >>> calculate_npv([-1000, 300, 400, 500], 0.1)
        48.68
    """
```

### README Updates
When adding features, update relevant documentation:
- Feature descriptions
- Installation instructions
- Usage examples
- Configuration options

## Pull Request Process

### Before Submitting

1. **Test your changes**
   ```bash
   make test
   make lint
   make type-check
   ```

2. **Update documentation**
   - Code comments
   - README if needed
   - API documentation

3. **Add/update tests**
   - Unit tests for new functions
   - Integration tests for new workflows
   - Update existing tests if behavior changes

### Pull Request Checklist

- [ ] Branch is up to date with main
- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Commit messages follow convention
- [ ] No sensitive information is committed

### Review Process

1. **Automated Checks**: CI pipeline runs automatically
2. **Code Review**: Maintainers review code and provide feedback
3. **Testing**: Manual testing of new features
4. **Approval**: Two maintainer approvals required
5. **Merge**: Squash and merge to main branch

## Issue Guidelines

### Bug Reports

When reporting bugs, include:
- **Environment details** (OS, Python version, deployment type)
- **Steps to reproduce** the issue
- **Expected vs. actual behavior**
- **Error logs** and stack traces
- **Screenshots** if applicable

### Feature Requests

For feature requests, provide:
- **Problem description** and use case
- **Proposed solution** or approach
- **Impact assessment** (users affected, priority)
- **Implementation suggestions** if you have ideas

### Labels

Issues are categorized with labels:
- `bug` - Something isn't working
- `enhancement` - New feature or improvement
- `documentation` - Documentation improvements
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `priority/high` - High priority issues

## Component-Specific Guidelines

### Financial Modeling Tools
```python
# Always validate inputs
def calculate_metric(params: Dict[str, Any]) -> Dict[str, Any]:
    validate_input(params, ['required_field'], {'required_field': float})
    
    # Handle edge cases
    if params['value'] <= 0:
        raise ValidationError("Value must be positive")
    
    # Return standardized format
    return {"metric": result, "confidence": confidence_score}
```

### Database Integration
```python
# Use database abstraction
@retry_with_backoff(**DATABASE_RETRY_CONFIG)
@handle_errors(error_mapping={ConnectionError: DatabaseError})
def query_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
    with self.db_config.get_connection() as conn:
        # Database operations
        pass
```

### Agent Integration
```python
# Follow AG2 tool patterns
def create_tool_spec():
    return {
        "name": "tool_name",
        "description": "Clear tool description",
        "parameters": {
            "type": "object",
            "properties": {
                "param": {"type": "string", "description": "Parameter description"}
            },
            "required": ["param"]
        }
    }
```

## Getting Help

- **GitHub Discussions**: For questions and ideas
- **GitHub Issues**: For bug reports and feature requests
- **Code Reviews**: For implementation feedback

## Recognition

Contributors are recognized in:
- GitHub contributors list
- Release notes for significant contributions
- README acknowledgments

Thank you for contributing to the Business Intelligence Platform! 🚀