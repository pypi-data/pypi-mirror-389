"""
MongoDB SQL Parser - A library for converting SQL queries to MongoDB aggregation pipelines
"""

__version__ = "0.1.0"

from .mongo_filter_parser import (
    MongoFilterParser,
    ParseError,
    SyntaxError,
    UnsupportedOperatorError,
    Operator,
    Token
)

from .sql_mongo_parser import MongoQueryParser

from .mongo_shell_parser import (
    MongoShellParser,
    convert_extjson_specials,
    MongoExpression
)

from .mongodb_validator import MongoExpressionValidator

__all__ = [
    "MongoFilterParser",
    "MongoQueryParser",
    "MongoShellParser",
    "MongoExpressionValidator",
    "ParseError",
    "SyntaxError",
    "UnsupportedOperatorError",
    "Operator",
    "Token",
    "convert_extjson_specials",
    "MongoExpression",
]

