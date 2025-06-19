# EDA-Data-Accuracy-Test-Rule-Engine

## 📋 Challenge Overview

This project is a **Data Accuracy Test Rule Engine** developed for the Technology Hackathon 2025 - EDA Challenge Statement #24. The challenge is designed for Data Engineers to create an implementable solution that automates the validation of business logic rules across multiple data tables and columns.

### Problem Statement

Currently, test scripts are being developed ad-hoc/individually/separately to verify specific and complicated business logic rules. This project aims to create a unified rule engine that can:

- Generate parameterized SQL scripts to validate categorized and simplified rules
- Support Boolean operators to create complex rules by combining simple rules
- Provide scalable and flexible rule management
- Deliver real-time rule execution with minimal latency

## 🎯 Project Goals

The Data Accuracy Test Rule Engine addresses the complete data engineering development and test process:

```
Business Logic Rules → Development of Data Jobs & Pipelines → Test Scripts → Data Test Report
```

### Key Features

- **Rule Parameterization**: Support for KEYWORDS, NAMES, and VALUES parameters
- **Boolean Logic**: Complex rule creation using Boolean expressions
- **Multi-Database Support**: Compatible with DB2, PostgreSQL, AWS Redshift, MSSQL, Oracle
- **Real-time Processing**: Low latency rule execution
- **Flexible Configuration**: JSON, XML, SQL stored procedures rule definitions

## 📊 Supported Rule Types

The engine supports the following categorized and simplified rules:

| No | Rule Type | Applied On | Description | Examples |
|----|-----------|------------|-------------|----------|
| 1 | Value Range | A column | Validate data according to expected ranges | From... to... |
| 2 | Value Template | A column | Validate regex templates | Telephone number, email format |
| 3 | Data Continuity/Integrity | A column | Validate data continuity/integrity | Timestamp or id in sequence |
| 4 | Comparison of Same Statistical/Arithmetic Calculations | 2 groups of columns (same table) | Support statistical and arithmetic calculations, compare results | Sum, min, max, average |
| 5 | Comparison of Different Statistical/Arithmetic Calculations | 2 groups of columns (different tables) | Support different statistical calculations between groups | Sum of group vs another column |

## 🛠 Technical Requirements

### Programming Languages
- **SQL**: For rule definition and execution
- **Python**: For rule engine implementation and orchestration

### Database Support
The prototype is compatible with at least one of the following database engines:
- DB2
- PostgreSQL  
- AWS Redshift
- MSSQL
- Oracle

### Performance Metrics

#### Performance
- **Processing Speed**: Optimized execution time for rule sets
- **Latency**: Minimal delay in real-time rule execution

#### Flexibility
- **Easy Rule Customization**: Parameter-based configuration without code changes
- **Multiple Definition Formats**: Support for JSON, XML, SQL stored procedures
- **Scalability**: Handle large numbers of rules efficiently

## 🏗 Architecture

### Rule Parameters

The engine uses three main parameter types:

1. **KEYWORDS**: References to functions for statistical and arithmetic calculations
   - Pre-built database engine functions
   - User-defined functions (loaded into database engine)
   - Note: User-defined function scripts are out of scope

2. **NAMES**: References to specific data objects
   - Schema, table, and column references
   - Follows database engine naming conventions
   - Format: `<schema>.<table>.<column>`

3. **VALUES**: Constant values for different data types
   - Lists, enumerated data, collections
   - Compatible with database engine requirements

### Rule Execution Flow

```
Simple Rules → Boolean Operations → Complex Rules → TRUE/FALSE Result → PASS/FAIL Status
```

## 📦 Deliverables

- [ ] **Principle Design Document**: Comprehensive architecture and design specifications
- [ ] **Prototype Demo**: Working demonstration including source code and running demo
- [ ] **Source Code**: Complete implementation with documentation
- [ ] **Documentation**: Setup, configuration, and usage guides

## 🚀 Getting Started

### Prerequisites

```bash
# Python dependencies
pip install -r requirements.txt

# Database connection setup
# Configure your database connection parameters
```

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/EDA-Data-Accuracy-Test-Rule-Engine.git

# Navigate to project directory
cd EDA-Data-Accuracy-Test-Rule-Engine

# Install dependencies
pip install -r requirements.txt
```

### Quick Start

```python
# Basic usage example
from rule_engine import DataAccuracyEngine

# Initialize the engine
engine = DataAccuracyEngine(database_config)

# Define a simple rule
rule = {
    "type": "value_range",
    "column": "schema.table.column",
    "min_value": 0,
    "max_value": 100
}

# Execute rule
result = engine.execute_rule(rule)
print(f"Rule validation: {'PASS' if result else 'FAIL'}")
```

## 📁 Project Structure

```
EDA-Data-Accuracy-Test-Rule-Engine/
│
├── src/
│   ├── rule_engine/         # Core rule engine implementation
│   ├── database/           # Database connectors and utilities
│   ├── parsers/            # Rule definition parsers (JSON, XML, SQL)
│   └── validators/         # Rule validation logic
│
├── tests/                  # Unit and integration tests
├── docs/                   # Documentation
├── examples/              # Example rules and configurations
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🧪 Testing

```bash
# Run unit tests
python -m pytest tests/

# Run integration tests
python -m pytest tests/integration/

# Generate test coverage report
python -m pytest --cov=src tests/
```

## 📈 Performance Considerations

- **Optimized SQL Generation**: Efficient query construction for minimal database load
- **Connection Pooling**: Database connection management for high throughput
- **Caching**: Rule compilation and result caching for repeated executions
- **Parallel Processing**: Support for concurrent rule execution

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 Hackathon Information

**Event**: Technology Hackathon 2025  
**Challenge**: EDA Challenge Statement #24  
**Category**: Data Engineering  
**Focus**: Data Accuracy Test Rule Engine Development

---

*This project was developed as part of the Technology Hackathon 2025 EDA Challenge to demonstrate skills in data engineering, rule engine development, and automated testing solutions.*