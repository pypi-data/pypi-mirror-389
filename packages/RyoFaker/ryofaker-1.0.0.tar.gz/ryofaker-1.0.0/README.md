# RyoFaker 🎲

**Enterprise data generation library extending Faker** with schema-driven generation, referential integrity management, and data quality features specifically designed for QA engineers, data scientists, and ETL developers.

[![PyPI version](https://badge.fury.io/py/RyoFaker.svg)](https://badge.fury.io/py/RyoFaker)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

##  Why RyoFaker?

RyoFaker solves **real-world data generation challenges** that standard Faker doesn't address:

✅ **Schema-driven generation** from JSON/YAML (no repetitive code)  
✅ **Referential integrity** with automatic FK management  
✅ **Data quality testing** (inject nulls, duplicates, constraint violations)  
✅ **Time-series & CDC** event simulation  
✅ **India-specific providers** (PAN, Aadhaar, GSTIN, IFSC, IMEI, IMSI)  
✅ **Multi-format output** (Pandas, PySpark, Parquet, CSV, SQL, Cloud)  
✅ **100% Faker-compatible** — drop-in replacement

---

##  Installation

Basic installation
pip install RyoFaker

With PySpark support
pip install RyoFaker[spark]

With cloud storage support (OCI, Azure, S3)
pip install RyoFaker[cloud]

Install everything
pip install RyoFaker[all]

text

---

##  Quick Start

### Basic Usage (Faker-compatible)

from ryofaker import RyoFaker

All Faker methods work identically
rf = RyoFaker('en_IN')
print(rf.name()) # "Aryan Mullick"
print(rf.address()) # "Plot 45, Sector 12, New Delhi 110001"

text

### India-Specific Providers

Indian identity documents
print(rf.pan()) # "ABCDE1234F"
print(rf.aadhaar()) # "1234 5678 9012"
print(rf.gstin()) # "27ABCDE1234F1Z5"
print(rf.ifsc()) # "SBIN0001234"

Telecom identifiers
print(rf.imei()) # "123456789012345"
print(rf.imsi()) # "404011234567890"
print(rf.msisdn()) # "+91 98765 43210"

text

### Schema-Driven Generation

**Define schema once** (`customer_order.json`):

{
"tables": {
"customers": {
"rows": 100,
"columns": {
"customer_id": {"provider": "uuid4", "primary_key": true},
"first_name": {"provider": "first_name"},
"last_name": {"provider": "last_name"},
"email": {"provider": "email", "unique": true},
"pan": {"provider": "pan"},
"created_at": {"provider": "date_between", "args": {"start_date": "-2y"}}
}
},
"orders": {
"rows": 500,
"columns": {
"order_id": {"provider": "uuid4", "primary_key": true},
"customer_id": {"foreign_key": "customers.customer_id"},
"order_date": {"provider": "date_time_this_year"},
"amount": {"provider": "pydecimal", "args": {"left_digits": 5, "right_digits": 2}},
"status": {"provider": "random_element", "args": {"elements": ["pending", "shipped", "delivered"]}}
}
}
},
"relationships": [
{"parent": "customers", "child": "orders", "ratio": 5}
]
}

text

**Generate with one line**:

from ryofaker import RyoFaker

rf = RyoFaker()
data = rf.from_schema('customer_order.json', format='pandas')

Returns: {'customers': DataFrame, 'orders': DataFrame}
FK integrity guaranteed: all orders.customer_id exist in customers.customer_id
text

### Referential Integrity

Manual FK management
tables = rf.with_relationships({
'users': {
'rows': 50,
'schema': {'user_id': 'uuid4', 'name': 'name'}
},
'orders': {
'rows': 200,
'schema': {'order_id': 'uuid4', 'user_id': 'fk:users.user_id', 'amount': 'pydecimal'}
}
})

Guaranteed: Every orders.user_id exists in users.user_id
text

### Data Quality Testing

import pandas as pd

Generate clean data
df = rf.from_schema('schema.json', format='pandas')['customers']

Inject nulls for testing
df_with_nulls = rf.inject_nulls(df, columns=['phone', 'email'], rate=0.1)

Inject duplicates for deduplication testing
df_with_dupes = rf.inject_duplicates(df, rate=0.05)

Edge case testing
print(rf.testing.max_varchar(255)) # String exactly 255 chars
print(rf.testing.unicode_emoji()) # "🚀💯😊"
print(rf.testing.sql_injection()) # "'; DROP TABLE users; --"

text

### Time-Series & CDC Simulation

Generate CDC event stream
for event in rf.cdc_stream(schema={'user_id': 'uuid4', 'name': 'name'}, duration_seconds=60):
print(event)
# {'operation': 'INSERT', 'timestamp': '2025-10-14T10:30:15', 'data': {...}}
# {'operation': 'UPDATE', 'timestamp': '2025-10-14T10:30:45', 'data': {...}}

text

### Multi-Format Output

Pandas DataFrame (default)
df = rf.from_schema('schema.json', format='pandas')

PySpark DataFrame
spark_df = rf.from_schema('schema.json', format='pyspark')

Parquet file
rf.from_schema('schema.json', format='parquet', output='data.parquet')

CSV file
rf.from_schema('schema.json', format='csv', output='data.csv')

SQL INSERT statements
sql = rf.from_schema('schema.json', format='sql')

text

---

##  Use Cases

### 1. Software Testing & QA

Repeatable regression datasets
rf = RyoFaker()
rf.seed(42)
test_data = rf.from_schema('test_schema.json', rows=1000)

Same seed = identical data every run
text

### 2. Load Testing

Generate 10 million rows at scale
rf.from_schema('load_test.json', rows=10_000_000, format='parquet', output='load_data.parquet')

text

### 3. Privacy & Compliance

Replace production data with synthetic copies
synthetic_users = rf.from_schema('user_schema.json', rows=100000)

Preserves patterns but no real identities
text

### 4. ETL Testing

CDC stream testing
for event in rf.cdc_stream(schema={...}, duration_seconds=300):
kafka_producer.send('cdc-topic', event)

text

---

##  Custom Providers Available

### Enterprise Providers

| Provider | Methods | Use Case |
|----------|---------|----------|
| **india_identity** | `pan()`, `aadhaar()`, `gstin()`, `ifsc()` | Indian KYC, banking, tax |
| **telecom** | `imei()`, `imsi()`, `msisdn()` | Mobile network, SIM provisioning |
| **healthcare** | `mrn()`, `insurance_id()`, `icd10_code()` | Patient records, claims |
| **retail** | `sku()`, `upc()`, `order_id()` | Inventory, e-commerce |
| **banking** | `account_number()`, `transaction_id()`, `swift_code()` | Payment systems, ledgers |

### Testing Providers

| Provider | Methods | Use Case |
|----------|---------|----------|
| **edge_cases** | `max_varchar()`, `unicode_emoji()`, `sql_injection()` | Boundary testing, security |
| **stress** | `random_blob()`, `deep_json()` | Load testing, performance |
| **regression** | Seeded fixed datasets | Reproducible test scenarios |

---

##  Advanced Features

### Dependency Graph Resolution

RyoFaker uses **NetworkX** to automatically resolve FK dependencies and generate tables in the correct order:

Define complex multi-table schema with circular references
RyoFaker automatically detects and resolves the dependency graph
data = rf.from_schema('complex_schema.json')

text

### Progress Tracking

Built-in progress bars for large datasets
rf.from_schema('big_schema.json', rows=1_000_000, show_progress=True)

Progress: 100%|████████████| 1000000/1000000 [00:45<00:00, 22000rows/s]
text

### Locale Support

All Faker locales supported + India-specific enhancements
rf_india = RyoFaker('en_IN')
rf_us = RyoFaker('en_US')
rf_multi = RyoFaker(['en_IN', 'hi_IN'], use_weighting=True)

text

---

## 📚 Documentation

- **Full Documentation**: [https://ryofaker.readthedocs.io](https://ryofaker.readthedocs.io)
- **API Reference**: [https://ryofaker.readthedocs.io/api/](https://ryofaker.readthedocs.io/api/)
- **Schema Reference**: [https://ryofaker.readthedocs.io/schema/](https://ryofaker.readthedocs.io/schema/)
- **Examples**: [https://github.com/ada/ryofaker/tree/main/examples](https://github.com/ada/ryofaker/tree/main/examples)

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Clone repository
git clone https://github.com/ada/ryofaker.git
cd ryofaker

Install in development mode
pip install -e ".[dev]"

Run tests
pytest tests/ -v

Format code
black ryofaker/ tests/

text

---

## 📄 License

RyoFaker is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

RyoFaker is built on top of the excellent [Faker](https://github.com/joke2k/faker) library. We extend deep gratitude to the Faker maintainers and contributors.

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/ada/ryofaker/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ada/ryofaker/discussions)
- **Email**: data-science@ada.com

---

**Made with ❤️ by the ADA Data Science Team**