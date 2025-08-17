# 🧠 Business Intelligence Platform

A comprehensive AI-powered business analysis platform built with AG2 (AutoGen) and Claude AI. **Evolved from a simple Business-Idea Pre-Validator** into a full enterprise-grade Business Intelligence Platform with multi-agent collaboration, advanced financial modeling, market research, and scenario planning.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Tests](https://img.shields.io/badge/tests-966%20passing-brightgreen.svg)
![Security](https://github.com/UMainLove/business_intelligence_platform/actions/workflows/security.yml/badge.svg)
[![Snyk Security](https://github.com/UMainLove/business_intelligence_platform/actions/workflows/snyk-security.yml/badge.svg)](https://github.com/UMainLove/business_intelligence_platform/actions/workflows/snyk-security.yml)
[![codecov](https://codecov.io/github/UMainLove/business_intelligence_platform/graph/badge.svg?token=OH6S2RUPCH)](https://codecov.io/github/UMainLove/business_intelligence_platform)


## 🚀 Features

### 🎯 **Multi-Agent Business Analysis**
- **Economist Agent**: Financial modeling, ROI analysis, unit economics
- **Lawyer Agent**: Legal compliance, regulatory analysis, risk assessment  
- **Sociologist Agent**: Market research, customer behavior, social trends
- **Synthesizer Agent**: Comprehensive report generation and strategic recommendations

### 🛠️ **Advanced Business Intelligence Tools**
- **Financial Modeling**: NPV, IRR, payback analysis, unit economics, cash flow projections
- **Market Research RAG**: Historical data analysis with vector database integration
- **Web Intelligence**: Real-time market data collection and competitive analysis
- **Database Integration**: PostgreSQL for production, SQLite for development
- **Document Generation**: Automated business reports and analysis documents
- **External API Integration**: Third-party data sources and services

### 📊 **Three Analysis Modes**
1. **Interactive Analysis**: Real-time chat with AI specialists (original validator enhanced)
2. **Sequential Validation**: 7-phase structured business validation workflow
3. **Swarm Scenario Planning**: 8 stress-test scenarios for risk assessment

### 🏗️ **Production-Ready Infrastructure**
- **Docker & Kubernetes**: Full containerization with auto-scaling
- **PostgreSQL + Redis**: Production database with caching layer
- **Health Monitoring**: System metrics, error tracking, performance monitoring
- **Security**: RBAC, network policies, secrets management
- **Error Handling**: Comprehensive retry logic and graceful degradation

### ✅ **Production Quality Assurance**
- **966 Tests Passing**: 100% test suite success rate with 98% code coverage
- **Zero Test Isolation Issues**: Fixed global state management and test independence  
- **Clean Deprecation Handling**: Updated all datetime usage, ag2 v0.97 stable version
- **Robust Error Handling**: Fixed 133→0 failing tests, systematic test fixes
- **Performance Validated**: All agents, workflows, and tools thoroughly tested

## 📋 Quick Start

### Prerequisites
- Python 3.10+ (required for AG2/AutoGen)
- Anthropic API Key
- Docker (optional, for production deployment)

### 1. Installation

```bash
git clone https://github.com/UMainLove/business_intelligence_platform.git
cd business_intelligence_platform
python -m venv venv && source venv/bin/activate
python -m pip install -U pip setuptools wheel
pip install -r requirements.txt
```

### 2. Configuration

```bash
cp .env.example .env
# Edit .env with your Anthropic API key and model preferences
```

**Professional Configuration (.env):**
```bash
# Core API
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Professional Models (recommended)
ANTHROPIC_MODEL_SPECIALISTS=claude-sonnet-4-20250514
ANTHROPIC_MODEL_SYNTH=claude-3-7-sonnet-20250219
ANTHROPIC_MODEL_MEMORY=claude-3-5-haiku-20241022

# Performance Optimization
TEMPERATURE_ECONOMIST=0.2
TEMPERATURE_LAWYER=0.1
TEMPERATURE_SOCIOLOGIST=0.4
MAX_TOKENS_SPECIALISTS=1500
MAX_TOKENS_SYNTH=2500
```

### 3. Run the Application

```bash
# Original Business-Idea Pre-Validator (still available)
streamlit run app.py

# Enhanced Business Intelligence Platform
streamlit run app_bi.py

# Or using Make
make run
```

Visit `http://localhost:8501` to access the platform.

## 🧪 Testing

Comprehensive test suite with 95%+ coverage across 4 specialized test types:

### Test Types

- **`test_*_focused.py`** - High-coverage unit tests targeting 95%+ line coverage for specific modules
- **`test_*_synthetic.py`** - AI-generated behavioral tests for realistic scenarios and edge cases  
- **`test_*_comprehensive.py`** - Integration and end-to-end tests across multiple components
- **`test_*.py` (untagged)** - Legacy/original test suite for basic functionality validation

### Running Tests

```bash
# Run all tests
make test

# Run with coverage reporting
make test-coverage

# Run specific test categories  
make test-focused       # Coverage validation tests
make test-synthetic     # Business scenario tests
make test-comprehensive # Integration tests
make test-unit          # Unit tests
make test-integration   # Integration tests

# Fast tests (exclude slow ones)
make test-fast
```

## 🐳 Production Deployment

### Docker Compose (Recommended)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f bi-app
```

### Kubernetes
```bash
# Deploy to Kubernetes
kubectl apply -f k8s/

# Check status
kubectl get pods -n business-intelligence
```

## 📊 Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI  │────│  AG2 Multi-Agent │────│  Claude AI APIs │
└─────────────────┘    │     Framework    │    └─────────────────┘
                       └──────────────────┘
                               │
                    ┌──────────┼──────────┐
                    │          │          │
            ┌───────▼───┐ ┌────▼────┐ ┌───▼────┐
            │Financial  │ │Database │ │ Web    │
            │Modeling   │ │ & RAG   │ │ Intel  │
            └───────────┘ └─────────┘ └────────┘
                               │
                    ┌──────────┼──────────┐
                    │          │          │
               ┌────▼────┐ ┌───▼───┐ ┌───▼────┐
               │PostgreSQL│ │Redis  │ │Monitor │
               └─────────┘ └───────┘ └────────┘
```

## 📱 Platform Modes

### 1. Interactive Analysis 🎯
Enhanced chat interface with tool-enabled AI specialists:
- Real-time business intelligence integration
- Smart commands: `DONE`, `SEQUENTIAL`, `SWARM`
- Visual tool usage indicators

### 2. Sequential Validation 📋
Structured 7-phase business validation:
1. Market Research
2. Financial Modeling
3. Legal & Regulatory
4. Technical Feasibility
5. Competitive Analysis
6. Risk Assessment
7. Strategic Planning

### 3. Scenario Analysis 🌪️
Multi-scenario stress testing with 8 scenario types:
- Economic Downturn
- Competitive Disruption
- Regulatory Changes
- Tech Obsolescence
- Supply Chain Crisis
- Market Saturation
- Funding Drought
- Talent Shortage

## 🎯 Key Transformation

### From Simple Validator to BI Platform

**Original Tool:**
- 3 AI specialists (Economist, Lawyer, Sociologist)
- Basic chat interface
- Simple text reports
- Single workflow

**Enhanced Platform:**
- **Tool-Enhanced Specialists** with business intelligence capabilities
- **Multi-Modal Analysis** (Interactive, Sequential, Swarm)
- **Generated Documents** (Business Plans, Financial Models, Risk Assessments)
- **Real-Time Intelligence** (Web APIs, Database, Market Research)
- **Production Infrastructure** (Docker, K8s, PostgreSQL, Redis)
- **Comprehensive Testing** (95%+ coverage, integration tests)
- **Health Monitoring** (System metrics, error tracking)

## 🔒 Security

### Multi-Layer Security Scanning

The platform includes comprehensive security scanning across multiple layers:

**Static Analysis:**
- **Bandit**: Python security linter for common security issues
- **Safety**: Checks Python dependencies for known vulnerabilities  
- **pip-audit**: Audits Python packages for known vulnerabilities

**Dynamic Analysis:**
- **Snyk**: Multi-layer vulnerability scanning
  - Dependency scanning for Python packages
  - Docker image vulnerability scanning
  - Infrastructure as Code (Kubernetes) security analysis
  - Static application security testing (SAST)
  - Continuous monitoring in production

**Security Workflows:**
- Daily security scans via GitHub Actions (2 AM UTC)
- Real-time PR security checks (blocks vulnerable changes)
- SARIF integration with GitHub Security tab
- Automated dependency monitoring and alerting
- Optional: Automatic fix PRs for vulnerabilities

### Security Configuration

**Basic Setup (GitHub Actions only):**
```bash
# 1. Create Snyk account at https://snyk.io
# 2. Get API token from account settings
# 3. Add SNYK_TOKEN to GitHub repository secrets
```

**Enhanced Setup (Optional - for automatic PRs and advanced features):**
```bash
# 1. Connect GitHub OAuth app integration via Snyk dashboard
# 2. Enable automatic fix PRs and dependency upgrades
# 3. Configure PR status checks and vulnerability monitoring
# 4. Set up branch protection rules with Snyk checks
```

Security reports are available in:
- GitHub Security tab (Code scanning alerts)
- CI/CD artifacts (JSON reports)
- Snyk dashboard for continuous monitoring
- PR checks (blocks/allows merging based on vulnerabilities)

## 🛠️ Development

### Environment Setup
```bash
# Setup development environment
make setup-dev

# Code formatting
make format

# Linting
make lint

# Type checking
make type-check
```

### File Structure
```
business_intelligence_platform/
├── src/
│   ├── tools/              # Business Intelligence Tools
│   │   ├── financial_tools.py
│   │   ├── rag_tools.py
│   │   ├── web_tools.py
│   │   ├── database_production.py
│   │   ├── document_tools.py
│   │   └── api_tools.py
│   ├── workflows/          # Analysis Workflows
│   │   ├── sequential_validation.py
│   │   └── swarm_scenarios.py
│   ├── error_handling.py   # Error handling & retry logic
│   ├── health_monitor.py   # System monitoring
│   └── business_intelligence.py  # Main BI integration
├── tests/                  # Comprehensive test suite
├── k8s/                    # Kubernetes manifests
├── scripts/                # Utility scripts
├── app.py                  # Original validator
└── app_bi.py              # Enhanced BI platform
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests and ensure they pass (`make test`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **AG2 (AutoGen)**: Multi-agent framework foundation
- **Anthropic Claude**: AI models and capabilities  
- **Streamlit**: Interactive web interface
- **Original Contributors**: Business-Idea Pre-Validator foundation

---

**Built with ❤️ using AG2, Claude AI, and modern DevOps practices**

*Evolved from Business-Idea Pre-Validator to comprehensive Business Intelligence Platform - August 2025*
