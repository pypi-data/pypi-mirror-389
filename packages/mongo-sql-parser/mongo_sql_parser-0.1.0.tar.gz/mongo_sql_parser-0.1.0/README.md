# mongo-sql-parser

A Python library for converting SQL queries to MongoDB aggregation pipelines. This library provides comprehensive support for SQL-to-MongoDB query translation, including WHERE clauses, JOINs, GROUP BY, aggregations, and subqueries.

## Features

- **SQL to MongoDB Conversion**: Convert SQL SELECT queries to MongoDB aggregation pipelines
- **WHERE Clause Parsing**: Parse complex SQL WHERE conditions into MongoDB filters
- **JOIN Support**: Convert SQL JOINs to MongoDB `$lookup` operations
- **Aggregation Support**: Support for GROUP BY, COUNT, SUM, AVG, MIN, MAX
- **Subquery Support**: Handle EXISTS, IN, NOT IN, and comparison subqueries
- **MongoDB Shell Parser**: Parse MongoDB shell expressions to Python dictionaries
- **MongoDB Query Validator**: Validate MongoDB shell queries for security

## Installation

```bash
pip install mongo-sql-parser
```

## Quick Start

### Convert SQL to MongoDB Pipeline

```python
from mongo_sql_parser import MongoQueryParser

parser = MongoQueryParser()
sql = "SELECT name, age FROM users WHERE age > 25 AND city = 'NYC'"
pipeline = parser.parse_query(sql)
print(pipeline)
# Output: [
#   {'$match': {'age': {'$gt': 25}, 'city': 'NYC'}},
#   {'$project': {'_id': 0, 'name': 1, 'age': 1}}
# ]
```

### Parse WHERE Conditions

```python
from mongo_sql_parser import MongoFilterParser

parser = MongoFilterParser()
condition = "age > 25 AND (city = 'NYC' OR city = 'LA')"
filter_dict = parser.parse(condition)
print(filter_dict)
# Output: {'$and': [{'age': {'$gt': 25}}, {'$or': [{'city': 'NYC'}, {'city': 'LA'}]}]}
```

### Parse MongoDB Shell Queries

```python
from mongo_sql_parser import MongoShellParser

parser = MongoShellParser()
query = 'db.users.find({"age": {"$gt": 25}})'
result = parser.parse(query)
print(result)
# Output: {
#   'db_name': None,
#   'collection_name': 'users',
#   'function': 'find',
#   'expression': {'age': {'$gt': 25}}
# }
```

## Supported SQL Features

- **SELECT**: Projection of fields
- **WHERE**: Filter conditions with support for:
  - Comparison operators (`=`, `!=`, `>`, `<`, `>=`, `<=`)
  - Logical operators (`AND`, `OR`, `NOT`)
  - `LIKE` / `ILIKE` pattern matching
  - `IN` / `NOT IN` clauses
  - `IS NULL` / `IS NOT NULL`
  - `BETWEEN` ranges
- **JOIN**: INNER, LEFT, RIGHT, and CROSS JOINs
- **GROUP BY**: Field grouping with aggregations
- **HAVING**: Post-aggregation filtering
- **ORDER BY**: Sorting
- **LIMIT**: Result limiting
- **Subqueries**: EXISTS, IN, NOT IN, comparison subqueries

## API Reference

### MongoQueryParser

Main class for parsing SQL queries into MongoDB pipelines.

```python
parser = MongoQueryParser()
pipeline = parser.parse_query(sql_string)
```

### MongoFilterParser

Parses SQL WHERE conditions into MongoDB filters.

```python
parser = MongoFilterParser()
filter_dict = parser.parse(condition_string)
```

### MongoShellParser

Parses MongoDB shell queries to extract database, collection, and expression information.

```python
parser = MongoShellParser()
result = parser.parse(shell_query_string)
```

## Requirements

- Python 3.7+
- sqlglot >= 10.0.0

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Changelog

### 0.1.0 (Initial Release)
- Initial release with SQL to MongoDB conversion support
- WHERE clause parsing
- JOIN support
- Aggregation support
- Subquery handling

