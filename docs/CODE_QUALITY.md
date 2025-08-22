# 📏 Business Intelligence Platform - Code Quality Guidelines

This document establishes comprehensive code quality standards and practices for the Business Intelligence Platform development.

## 📋 Table of Contents

- [Overview](#overview)
- [Code Quality Tools](#code-quality-tools)
- [Linting Standards](#linting-standards)
- [Type Checking](#type-checking)
- [Code Formatting](#code-formatting)
- [Complexity Analysis](#complexity-analysis)
- [Documentation Standards](#documentation-standards)
- [Testing Requirements](#testing-requirements)
- [CI/CD Integration](#cicd-integration)
- [Development Workflow](#development-workflow)

## 🎯 Overview

The Business Intelligence Platform maintains high code quality standards through automated tooling, comprehensive testing, and strict adherence to Python best practices.

### Quality Metrics

- **Test Coverage**: 97.91% (1,719 statements, 36 missing)
- **Code Quality**: A-grade average complexity
- **Type Safety**: Full mypy compliance with strict settings
- **Linting**: Zero violations with ruff, black, flake8, isort
- **Documentation**: Comprehensive docstring coverage with pydocstyle

### Quality Tools Stack

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **ruff** | Fast Python linting and formatting | `.ruff.toml` |
| **black** | Opinionated code formatting | Line length: 100 |
| **isort** | Import sorting and organization | Profile: black-compatible |
| **mypy** | Static type checking | Strict mode with error codes |
| **flake8** | Additional linting rules | Max line length: 100 |
| **pydocstyle** | Docstring convention checking | Google style |
| **radon** | Complexity analysis | Cyclomatic and maintainability |
| **xenon** | Complexity threshold enforcement | Grade A requirement |

## 🔧 Code Quality Tools

### Installation

```bash
# Install all code quality tools
make install-quality-tools

# Or manually
pip install ruff black isort mypy pydocstyle radon xenon flake8 autoflake
```

### Quick Commands

```bash
# Run comprehensive code quality analysis
make code-quality

# Individual tool commands
make lint           # Comprehensive linting
make type-check     # Type checking
make format         # Auto-format code
make complexity-check    # Complexity analysis
make docstring-check     # Docstring coverage
make fix-format     # Auto-fix formatting issues
```

## 📏 Linting Standards

### Ruff Configuration

Primary linting tool with fast performance and comprehensive rule coverage.

**Enabled Rules:**
- **E**: Pycodestyle errors
- **W**: Pycodestyle warnings  
- **F**: Pyflakes
- **I**: isort
- **N**: pep8-naming
- **D**: pydocstyle
- **UP**: pyupgrade
- **S**: bandit (security)
- **B**: flake8-bugbear
- **C**: complexity

**Configuration Example:**
```toml
# pyproject.toml or .ruff.toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "D", "UP", "S", "B", "C90"]
ignore = [
    "D203",  # 1 blank line required before class docstring
    "D213",  # Multi-line docstring summary should start at the second line
]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["D", "S101"]  # Allow missing docstrings and asserts in tests

[tool.ruff.lint.mccabe]
max-complexity = 10
```

### Flake8 Configuration

Additional linting for compatibility and legacy rule coverage.

**Settings:**
- Max line length: 100
- Ignore: E203 (whitespace before ':'), W503 (line break before binary operator)
- Max complexity: 10

### Import Sorting (isort)

Consistent import organization following black-compatible style.

**Configuration:**
```toml
[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
```

**Import Order:**
1. Standard library imports
2. Third-party imports
3. Local application imports

**Example:**
```python
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI

from src.business_intelligence import BusinessIntelligenceAgent
from src.database_config import db_config
```

## 🏷️ Type Checking

### MyPy Configuration

Strict type checking with comprehensive coverage.

**Settings:**
```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true
```

### Type Annotation Standards

**Function Signatures:**
```python
def process_business_data(
    data: List[Dict[str, Any]], 
    config: Optional[Dict[str, str]] = None
) -> BusinessIntelligenceResult:
    """Process business intelligence data with optional configuration.
    
    Args:
        data: List of business data records
        config: Optional configuration parameters
        
    Returns:
        Processed business intelligence result
        
    Raises:
        ValidationError: If data format is invalid
    """
    ...
```

**Class Definitions:**
```python
from typing import Protocol, TypeVar, Generic

T = TypeVar('T')

class DataProcessor(Generic[T]):
    """Generic data processor for business intelligence."""
    
    def __init__(self, validator: Callable[[T], bool]) -> None:
        self.validator = validator
    
    def process(self, data: T) -> ProcessedData[T]:
        """Process data with validation."""
        ...

class DatabaseProtocol(Protocol):
    """Type-safe database interface."""
    
    def query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute database query."""
        ...
```

### Protocol Patterns

Use Protocol for type-safe interfaces without inheritance:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class MetricsCollector(Protocol):
    """Protocol for metrics collection implementations."""
    
    def collect_metric(self, name: str, value: float, labels: Dict[str, str]) -> None:
        """Collect a metric value."""
        ...
    
    def get_metrics(self) -> Dict[str, float]:
        """Retrieve collected metrics."""
        ...

# Implementation
class PrometheusCollector:
    """Prometheus-based metrics collector."""
    
    def collect_metric(self, name: str, value: float, labels: Dict[str, str]) -> None:
        # Implementation
        ...
    
    def get_metrics(self) -> Dict[str, float]:
        # Implementation
        ...

# Usage with type checking
def process_with_metrics(collector: MetricsCollector) -> None:
    """Process data with metrics collection."""
    collector.collect_metric("requests_total", 1.0, {"status": "success"})
```

## 🎨 Code Formatting

### Black Configuration

Opinionated code formatting for consistency.

**Settings:**
- Line length: 100 characters
- String normalization: enabled
- Magic trailing comma: enabled

**Configuration:**
```toml
[tool.black]
line-length = 100
target-version = ['py310']
include = '\.pyi?$'
extend-exclude = '''
/(
  # Exclude specific files
  tests/test_document_generation_integration.py
)/
'''
```

### Formatting Rules

**Line Length:**
- Maximum 100 characters per line
- Break long function calls and definitions
- Use parentheses for line continuation

**String Formatting:**
```python
# Preferred: f-strings for simple cases
name = f"Hello, {user.name}!"

# For complex formatting
message = (
    f"Processing {len(records)} records "
    f"with {config.workers} workers "
    f"in {config.batch_size} batches"
)

# Multi-line strings
query = """
    SELECT user_id, name, email
    FROM users 
    WHERE active = true
      AND created_at > %s
    ORDER BY created_at DESC
"""
```

**Function and Class Definitions:**
```python
# Function with many parameters
def create_business_intelligence_report(
    data_source: str,
    analysis_type: str,
    filters: Optional[Dict[str, Any]] = None,
    output_format: str = "json",
    include_charts: bool = True,
    cache_results: bool = False,
) -> BusinessIntelligenceReport:
    """Create comprehensive business intelligence report."""
    ...

# Class with inheritance
class AdvancedBusinessIntelligenceAgent(
    BusinessIntelligenceAgent,
    MetricsCollectorMixin,
    CacheableMixin,
):
    """Advanced BI agent with additional capabilities."""
    ...
```

## 📊 Complexity Analysis

### Cyclomatic Complexity

Measure code complexity using radon and enforce thresholds with xenon.

**Complexity Grades:**
- **A**: 1-5 (Simple, low risk)
- **B**: 6-10 (Complex, moderate risk)  
- **C**: 11-20 (Very complex, high risk)
- **D**: 21-50 (Extremely complex, very high risk)
- **F**: 51+ (Unmaintainable, highest risk)

**Target Standards:**
- **Average Grade**: A-B
- **Maximum Individual Function**: B (≤10)
- **Maximum Class**: B (≤10)

### Complexity Commands

```bash
# Analyze complexity with radon
radon cc src --min B --show-complexity --total-average

# Check complexity thresholds with xenon
xenon --max-absolute A --max-modules A --max-average A src/

# Generate complexity reports
radon cc src --json > complexity-report.json
radon mi src --json > maintainability-report.json
```

### Complexity Reduction Strategies

**1. Extract Functions:**
```python
# Before: High complexity function
def process_user_data(user_data):
    # 20+ lines of complex logic
    if user_data.get('type') == 'premium':
        # Premium processing logic
        ...
    elif user_data.get('type') == 'standard':
        # Standard processing logic  
        ...
    # More complex conditions...

# After: Extracted functions
def process_user_data(user_data):
    """Process user data based on user type."""
    user_type = user_data.get('type', 'standard')
    
    if user_type == 'premium':
        return process_premium_user(user_data)
    elif user_type == 'standard':
        return process_standard_user(user_data)
    else:
        return process_default_user(user_data)

def process_premium_user(user_data):
    """Process premium user with advanced features."""
    ...
```

**2. Use Strategy Pattern:**
```python
from abc import ABC, abstractmethod

class UserProcessor(ABC):
    """Abstract user processor."""
    
    @abstractmethod
    def process(self, user_data: Dict[str, Any]) -> ProcessedUser:
        """Process user data."""
        ...

class PremiumUserProcessor(UserProcessor):
    """Processor for premium users."""
    
    def process(self, user_data: Dict[str, Any]) -> ProcessedUser:
        # Simple, focused logic
        ...

class StandardUserProcessor(UserProcessor):
    """Processor for standard users."""
    
    def process(self, user_data: Dict[str, Any]) -> ProcessedUser:
        # Simple, focused logic
        ...

# Factory for processor selection
def get_user_processor(user_type: str) -> UserProcessor:
    """Get appropriate user processor."""
    processors = {
        'premium': PremiumUserProcessor(),
        'standard': StandardUserProcessor(),
    }
    return processors.get(user_type, StandardUserProcessor())
```

## 📝 Documentation Standards

### Docstring Convention

Use Google-style docstrings with comprehensive coverage.

**Function Documentation:**
```python
def analyze_business_metrics(
    data: List[Dict[str, Any]], 
    metrics: List[str],
    time_range: Optional[DateRange] = None
) -> AnalysisResult:
    """Analyze business metrics for given data and time range.
    
    This function processes business data to calculate specified metrics
    over an optional time range. Supports various metric types including
    financial, operational, and customer metrics.
    
    Args:
        data: List of business data records containing metric values.
        metrics: List of metric names to calculate. Supported metrics:
            - 'revenue': Total revenue calculation
            - 'growth': Growth rate analysis  
            - 'conversion': Conversion rate metrics
        time_range: Optional date range for filtering data. If None,
            analyzes all available data.
    
    Returns:
        AnalysisResult containing calculated metrics, trends, and insights.
        
    Raises:
        ValueError: If metrics list is empty or contains unsupported metrics.
        DataError: If data format is invalid or insufficient for analysis.
        
    Example:
        >>> data = [{'date': '2023-01-01', 'revenue': 1000, 'users': 100}]
        >>> metrics = ['revenue', 'growth']
        >>> result = analyze_business_metrics(data, metrics)
        >>> print(result.metrics['revenue'])
        1000.0
        
    Note:
        This function requires data with consistent date formatting
        and numeric values for metric calculations.
    """
    ...
```

**Class Documentation:**
```python
class BusinessIntelligenceAgent:
    """Multi-agent business intelligence platform with Claude AI integration.
    
    This class provides comprehensive business intelligence capabilities
    including financial analysis, market research, and automated report
    generation using AG2 multi-agent framework and Claude AI.
    
    Attributes:
        config: Agent configuration settings
        tools: Available business intelligence tools
        memory: Conversation memory for context retention
        
    Example:
        >>> agent = BusinessIntelligenceAgent(
        ...     name="Financial Analyst",
        ...     tools=['financial_modeling', 'market_research']
        ... )
        >>> result = agent.analyze("Analyze Q4 revenue trends")
        >>> print(result.summary)
        
    Note:
        Requires ANTHROPIC_API_KEY environment variable for Claude AI access.
    """
    
    def __init__(
        self, 
        name: str, 
        tools: List[str], 
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize Business Intelligence Agent.
        
        Args:
            name: Human-readable name for the agent
            tools: List of tool names to enable for this agent
            config: Optional configuration overrides
            
        Raises:
            ConfigurationError: If required configuration is missing
            ToolError: If specified tools are not available
        """
        ...
```

### Documentation Coverage

Check docstring coverage with pydocstyle:

```bash
# Check docstring coverage
make docstring-check

# Generate detailed docstring report
pydocstyle src --explain --source --count
```

**Required Documentation:**
- All public functions and methods
- All classes and class methods
- All modules with module-level docstrings
- Complex algorithms and business logic
- Error handling and edge cases

## 🧪 Testing Requirements

### Test Coverage Standards

- **Minimum Coverage**: 95%
- **Current Coverage**: 97.91%
- **Target Coverage**: 98%+

### Test Categories

**1. Unit Tests:**
```python
import pytest
from unittest.mock import Mock, patch

class TestBusinessIntelligenceAgent:
    """Test suite for BusinessIntelligenceAgent."""
    
    def setup_method(self):
        """Setup test environment before each test."""
        self.mock_config = {'api_key': 'test-key'}
        self.agent = BusinessIntelligenceAgent(
            name="Test Agent",
            tools=['financial_modeling'],
            config=self.mock_config
        )
    
    def test_agent_initialization(self):
        """Test agent initializes with correct configuration."""
        assert self.agent.name == "Test Agent"
        assert 'financial_modeling' in self.agent.tools
        
    @patch('src.business_intelligence.claude_api')
    def test_analyze_with_mock_api(self, mock_api):
        """Test analysis with mocked API calls."""
        mock_api.return_value = {'result': 'analysis complete'}
        
        result = self.agent.analyze("Test query")
        
        assert result['result'] == 'analysis complete'
        mock_api.assert_called_once()
```

**2. Integration Tests:**
```python
class TestDatabaseIntegration:
    """Integration tests for database operations."""
    
    def test_full_query_pipeline(self):
        """Test complete query pipeline with real database."""
        # Use test database
        with test_database_context():
            # Insert test data
            db_config.execute_query(
                "INSERT INTO test_table (name, value) VALUES (%s, %s)",
                ("test", 100)
            )
            
            # Test query
            result = db_config.fetch_query(
                "SELECT * FROM test_table WHERE name = %s",
                ("test",)
            )
            
            assert len(result) == 1
            assert result[0]['value'] == 100
```

**3. Performance Tests:**
```python
import time
import pytest

class TestPerformance:
    """Performance test suite."""
    
    @pytest.mark.performance
    def test_large_dataset_processing(self):
        """Test processing performance with large datasets."""
        # Generate large dataset
        data = [{'id': i, 'value': i * 2} for i in range(10000)]
        
        start_time = time.time()
        result = process_business_data(data)
        execution_time = time.time() - start_time
        
        # Performance assertions
        assert execution_time < 5.0, f"Processing took {execution_time}s, expected < 5s"
        assert len(result) == 10000
```

### Test Commands

```bash
# Run all tests with coverage
make test-coverage

# Run specific test categories
make test-unit           # Unit tests only
make test-integration    # Integration tests only
make test-infrastructure # Infrastructure tests only

# Run tests with specific markers
pytest -m performance tests/    # Performance tests
pytest -m slow tests/          # Slow tests
pytest -m security tests/     # Security tests
```

## 🚀 CI/CD Integration

### Code Quality Pipeline

The CI/CD pipeline includes comprehensive code quality checks:

**Pipeline Stages:**
1. **Code Quality & Type Checking** (Parallel)
2. **Test Suite Execution** (Parallel)
3. **Security Scanning** (Parallel)
4. **Build & Deployment** (Sequential)

### Pre-commit Hooks

Automated code quality checks before commits:

```yaml
# .pre-commit-config.yaml
repos:
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.1.0
  hooks:
  - id: ruff
    args: [--fix, --exit-non-zero-on-fix]
  - id: ruff-format

- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.5.1
  hooks:
  - id: mypy
    additional_dependencies: [types-all]

- repo: https://github.com/pycqa/isort
  rev: 5.12.0
  hooks:
  - id: isort
    args: ["--profile", "black"]
```

### Quality Gates

All changes must pass these quality gates:

- ✅ **Linting**: Zero violations (ruff, flake8, isort)
- ✅ **Type Checking**: No type errors (mypy)
- ✅ **Formatting**: Consistent style (black, ruff format)  
- ✅ **Complexity**: Grade A-B maximum (radon, xenon)
- ✅ **Coverage**: 95%+ test coverage
- ✅ **Security**: No high/critical vulnerabilities
- ✅ **Documentation**: Complete docstring coverage

## 💻 Development Workflow

### Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd business_intelligence_platform

# Setup Python environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies and development tools
pip install -r requirements.txt
make install-quality-tools

# Setup pre-commit hooks
pre-commit install

# Verify setup
make code-quality
```

### Daily Development Workflow

**1. Before Coding:**
```bash
# Pull latest changes
git pull origin main

# Check current code quality
make code-quality

# Run tests to ensure clean baseline
make test
```

**2. During Development:**
```bash
# Auto-format code regularly
make format

# Check linting incrementally
make lint

# Run relevant tests
pytest tests/test_specific_module.py -v
```

**3. Before Committing:**
```bash
# Run comprehensive quality checks
make code-quality

# Run full test suite
make test

# Check coverage
make test-coverage

# Commit changes (pre-commit hooks will run automatically)
git add .
git commit -m "feat: implement new business intelligence feature"
```

### Code Review Checklist

**Functionality:**
- [ ] Code works as intended
- [ ] Edge cases are handled
- [ ] Error handling is appropriate
- [ ] Performance is acceptable

**Quality:**
- [ ] Code follows style guidelines
- [ ] Functions are small and focused
- [ ] Names are descriptive and clear
- [ ] Comments explain why, not what

**Testing:**
- [ ] Appropriate tests are included
- [ ] Test coverage is maintained
- [ ] Tests are meaningful and not just for coverage

**Documentation:**
- [ ] Public functions have docstrings
- [ ] Complex logic is documented
- [ ] README is updated if needed

### Best Practices

**1. Function Design:**
- Keep functions small (< 20 lines preferred)
- Single responsibility principle
- Pure functions when possible
- Clear input/output contracts

**2. Error Handling:**
```python
from src.error_handling import BusinessIntelligenceError

def process_data(data: List[Dict[str, Any]]) -> ProcessedData:
    """Process business data with comprehensive error handling."""
    if not data:
        raise ValueError("Data cannot be empty")
    
    try:
        validated_data = validate_business_data(data)
        return transform_data(validated_data)
    except ValidationError as e:
        raise BusinessIntelligenceError(
            f"Data validation failed: {e}",
            context={"data_length": len(data), "error": str(e)}
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error processing data: {e}")
        raise BusinessIntelligenceError(
            "Data processing failed due to unexpected error",
            context={"data_length": len(data)}
        ) from e
```

**3. Configuration Management:**
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class BusinessIntelligenceConfig:
    """Configuration for business intelligence operations."""
    
    api_key: str
    database_url: str
    cache_ttl: int = 3600
    debug_mode: bool = False
    max_workers: int = 4
    
    @classmethod
    def from_env(cls) -> 'BusinessIntelligenceConfig':
        """Create configuration from environment variables."""
        return cls(
            api_key=os.getenv('ANTHROPIC_API_KEY', ''),
            database_url=os.getenv('DATABASE_URL', ''),
            cache_ttl=int(os.getenv('CACHE_TTL', '3600')),
            debug_mode=os.getenv('DEBUG_MODE', 'false').lower() == 'true',
            max_workers=int(os.getenv('MAX_WORKERS', '4'))
        )
    
    def validate(self) -> None:
        """Validate configuration values."""
        if not self.api_key:
            raise ValueError("API key is required")
        if not self.database_url:
            raise ValueError("Database URL is required")
```

## 📊 Metrics and Monitoring

### Code Quality Metrics

Track these metrics over time:

- **Test Coverage**: Target 98%+
- **Complexity Score**: Maintain A-B grade
- **Linting Violations**: Zero tolerance
- **Type Coverage**: 100% of public APIs
- **Documentation Coverage**: 95%+ of public functions

### Quality Dashboard

Monitor code quality trends:

```bash
# Generate quality metrics
make code-metrics

# Generate complexity reports
radon cc src --json > metrics/complexity.json
radon mi src --json > metrics/maintainability.json

# Coverage reports  
coverage html --directory=metrics/coverage/
coverage json --output=metrics/coverage.json
```

### Continuous Improvement

**Monthly Quality Reviews:**
- Review complexity trends
- Identify refactoring opportunities
- Update coding standards
- Team training on new tools/practices

**Quality Goals:**
- Reduce average complexity by 5% quarterly
- Increase test coverage by 1% quarterly
- Maintain zero critical security vulnerabilities
- Keep technical debt ratio below 5%

---

These code quality guidelines ensure the Business Intelligence Platform maintains high standards for maintainability, reliability, and performance. For deployment and infrastructure details, see [DEPLOYMENT.md](DEPLOYMENT.md) and [INFRASTRUCTURE.md](INFRASTRUCTURE.md).