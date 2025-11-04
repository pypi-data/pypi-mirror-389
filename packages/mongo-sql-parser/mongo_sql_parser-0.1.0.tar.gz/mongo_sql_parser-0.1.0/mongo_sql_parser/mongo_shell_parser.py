from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
from decimal import Decimal
try:
    from bson import ObjectId as _OID
except ImportError:
    _OID = None
try:
    from dateutil.parser import isoparse as dtparse
except ImportError:
    dtparse = None

MongoExpression = Dict[str, Union[str, List[Dict[str, Any]], Dict[str, Any], None]]


class MongoShellParser:
    _EXTRACT_RE = re.compile(
        r"^\s*db\.(?:(?P<db>[A-Za-z_][\w]*)\.)?(?P<coll>[A-Za-z_][\w]*)\.(?P<op>[A-Za-z_][\w]*)\((?P<params>[\s\S]*)\)\s*;?\s*$",
        re.DOTALL,
    )

    @staticmethod
    def extract_db_collection_op(query: str) -> Tuple[Optional[str], str, str, str]:
        m = MongoShellParser._EXTRACT_RE.match(query)
        if not m:
            raise ValueError(f"Invalid Mongo shell query format: {query}")
        db_name = m.group("db")
        coll = m.group("coll")
        op = m.group("op")
        params = (m.group("params") or "").strip()
        return db_name, coll, op, params

    @staticmethod
    def _normalize_single_quoted_strings(s: str) -> str:
        out: List[str] = []
        i = 0
        in_squote = False
        in_dquote = False
        while i < len(s):
            ch = s[i]
            if not in_dquote and ch == "'":
                esc = 0
                j = i - 1
                while j >= 0 and s[j] == "\\":
                    esc += 1
                    j -= 1
                if esc % 2 == 0:
                    in_squote = not in_squote
                    out.append('"')
                else:
                    out.append(ch)
            elif not in_squote and ch == '"':
                esc = 0
                j = i - 1
                while j >= 0 and s[j] == "\\":
                    esc += 1
                    j -= 1
                if esc % 2 == 0:
                    in_dquote = not in_dquote
                out.append(ch)
            else:
                if in_squote and ch == '"':
                    out.append('\\"')
                else:
                    out.append(ch)
            i += 1
        return "".join(out)

    @staticmethod
    def _transform_shell_intrinsics(s: str) -> str:
        out: List[str] = []
        i = 0
        in_string = False
        string_char: Optional[str] = None

        def read_identifier(idx: int) -> Tuple[str, int]:
            j = idx
            while j < len(s) and (s[j].isalnum() or s[j] in {'$', '_'}):
                j += 1
            return s[idx:j], j

        def skip_ws(idx: int) -> int:
            while idx < len(s) and s[idx] in (' ', '\t', '\n', '\r'):
                idx += 1
            return idx

        def read_balanced_paren(idx: int) -> Tuple[str, int]:
            depth = 0
            j = idx
            in_str = False
            str_ch: Optional[str] = None
            while j < len(s):
                ch = s[j]
                if ch in ('"', '\''):
                    esc = 0
                    k = j - 1
                    while k >= 0 and s[k] == '\\':
                        esc += 1
                        k -= 1
                    if esc % 2 == 0:
                        if not in_str:
                            in_str = True
                            str_ch = ch
                        elif ch == str_ch:
                            in_str = False
                            str_ch = None
                elif not in_str:
                    if ch == '(':
                        depth += 1
                    elif ch == ')':
                        depth -= 1
                        if depth == 0:
                            return s[idx + 1:j], j + 1
                j += 1
            raise ValueError('Unbalanced parentheses in shell intrinsic')

        while i < len(s):
            ch = s[i]
            if ch in ('"', '\''):
                esc = 0
                j = i - 1
                while j >= 0 and s[j] == '\\':
                    esc += 1
                    j -= 1
                if esc % 2 == 0:
                    if not in_string:
                        in_string = True
                        string_char = ch
                    elif ch == string_char:
                        in_string = False
                        string_char = None
                out.append(ch)
                i += 1
                continue

        
            if not in_string and (ch.isalpha() or ch in {'$', '_'}):
                ident, j = read_identifier(i)
                if ident == 'new':
                    j2 = skip_ws(j)
                    if s[j2:j2 + 4] == 'Date':
                        j2_next = j2 + 4
                        j2_next = skip_ws(j2_next)
                        if j2_next < len(s) and s[j2_next] == '(':
                            inner, after = read_balanced_paren(j2_next)
                            inner = inner.strip()
                            val = inner
                            if (len(inner) >= 2 and inner[0] in {'"', '\''} and inner[-1] == inner[0]):
                                val = inner[1:-1]
                            out.append('{"$date":"')
                            out.append(val)
                            out.append('"}')
                            i = after
                            continue
                if ident in ('ISODate', 'ObjectId', 'NumberLong', 'NumberInt', 'Decimal128'):
                    j = skip_ws(j)
                    if j < len(s) and s[j] == '(':
                        inner, after = read_balanced_paren(j)
                        inner_stripped = inner.strip()
                        if ident == 'ISODate':
                            val = inner_stripped
                            if (len(val) >= 2 and val[0] in {'"', '\''} and val[-1] == val[0]):
                                val = val[1:-1]
                            out.append('{"$date":"')
                            out.append(val)
                            out.append('"}')
                            i = after
                            continue
                        if ident == 'ObjectId':
                            val = inner_stripped
                            if (len(val) >= 2 and val[0] in {'"', '\''} and val[-1] == val[0]):
                                val = val[1:-1]
                            out.append('{"$oid":"')
                            out.append(val)
                            out.append('"}')
                            i = after
                            continue
                        if ident in ('NumberLong', 'NumberInt'):
                            num = inner_stripped.strip('"\'')
                            out.append(num)
                            i = after
                            continue
                        if ident == 'Decimal128':
                            val = inner_stripped
                            if (len(val) >= 2 and val[0] in {'"', '\''} and val[-1] == val[0]):
                                val = val[1:-1]
                            out.append('{"$numberDecimal":"')
                            out.append(val)
                            out.append('"}')
                            i = after
                            continue
                out.append(ident)
                i = j
                continue

            out.append(ch)
            i += 1

        return ''.join(out)

    @staticmethod
    def normalize_shell_to_json(s: str) -> str:
        if not s:
            return s
        s = MongoShellParser._transform_shell_intrinsics(s)
        s = MongoShellParser._normalize_single_quoted_strings(s)

        out: List[str] = []
        i = 0
        in_string = False
        string_char: Optional[str] = None

        def is_identifier_start(c: str) -> bool:
            return c.isalpha() or c in {"$", "_"}

        def is_identifier_char(c: str) -> bool:
            return c.isalnum() or c in {"$", "_"}

        while i < len(s):
            ch = s[i]
            if ch in ('"', "'"):
                esc = 0
                j = i - 1
                while j >= 0 and s[j] == "\\":
                    esc += 1
                    j -= 1
                if esc % 2 == 0:
                    if not in_string:
                        in_string = True
                        string_char = ch
                    elif ch == string_char:
                        in_string = False
                        string_char = None
                out.append(ch)
                i += 1
                continue

            if in_string:
                out.append(ch)
                i += 1
                continue

            if is_identifier_start(ch):
                k = i - 1
                while k >= 0 and s[k] in (" ", "\t", "\n", "\r"):
                    k -= 1
                prev = s[k] if k >= 0 else None
                if prev in ("{", ",", None):
                    start = i
                    j = i
                    while j < len(s) and is_identifier_char(s[j]):
                        j += 1
                    k = j
                    while k < len(s) and s[k] in (" ", "\t", "\n", "\r"):
                        k += 1
                    if k < len(s) and s[k] == ":":
                        key = s[start:j]
                        out.append('"'); out.append(key); out.append('"')
                        out.append(s[j:k]); out.append(":")
                        i = k + 1
                        continue

            out.append(ch)
            i += 1

        return "".join(out)

    @staticmethod
    def _strip_wrapping(s: str) -> str:
        s = s.strip()
        if s.endswith(";"):
            s = s[:-1].strip()
        return s

    @staticmethod
    def _extract_bracket_block(s: str, open_ch: str, close_ch: str) -> str:
        start = s.find(open_ch)
        if start == -1:
            raise ValueError("Expected bracket block not found")
        depth = 0
        for idx in range(start, len(s)):
            if s[idx] == open_ch:
                depth += 1
            elif s[idx] == close_ch:
                depth -= 1
                if depth == 0:
                    return s[start : idx + 1]
        raise ValueError("Unbalanced brackets in expression")

    def parse_pipeline(self, param_str: str) -> List[Dict[str, Any]]:
        s = self._strip_wrapping(param_str)
        block = self._extract_bracket_block(s, "[", "]")
        normalized = self.normalize_shell_to_json(block)
        data = json.loads(normalized)
        if not isinstance(data, list):
            raise ValueError("aggregate pipeline must be a list")
        return data

    def parse_find_filter(self, param_str: str) -> Dict[str, Any]:
        s = self._strip_wrapping(param_str)
        s = s.strip()
        if not s or s in ("{}",):
            return {}
        if s[0] in ("(", "{"):
            if s[0] == "(":
                obj = self._extract_bracket_block(s, "{", "}")
            else:
                obj = self._extract_bracket_block(s, "{", "}")
        else:
            obj = s
        normalized = self.normalize_shell_to_json(obj)
        data = json.loads(normalized)
        if not isinstance(data, dict):
            raise ValueError("find filter must be an object")
        return data

    def parse(self, query: str) -> MongoExpression:
        db_name, coll, op, params = self.extract_db_collection_op(query)
        op_lower = op.lower()
        if op_lower == "aggregate":
            expr = self.parse_pipeline(params)
        elif op_lower == "find":
            expr = self.parse_find_filter(params)
        elif op_lower == "count":
            expr = self.parse_find_filter(params)
        else:
            raise ValueError(f"Unsupported operation: {op}")
        return {
            "db_name": db_name,
            "collection_name": coll,
            "function": op_lower,
            "expression": expr,
        }
        
def convert_extjson_specials(obj):
    """
    Recursively convert Extended JSON objects:
    - {"$date": ...} → datetime
    - {"$oid": ...} → bson.ObjectId
    - {"$numberDecimal": ...} → Decimal
    - {"$numberLong": ...}, {"$numberInt": ...} → int
    """
    if isinstance(obj, dict):
        if set(obj.keys()) == {"$date"}:
            if dtparse:
                return dtparse(obj["$date"])
            else:
                return datetime.strptime(obj["$date"], "%Y-%m-%dT%H:%M:%SZ")
        if set(obj.keys()) == {"$oid"} and _OID is not None:
            return _OID(obj["$oid"])
        if set(obj.keys()) == {"$numberDecimal"}:
            return Decimal(obj["$numberDecimal"])
        if set(obj.keys()) in [{"$numberLong"}, {"$numberInt"}]:
            key = next(iter(obj))
            return int(obj[key])
        return {k: convert_extjson_specials(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_extjson_specials(x) for x in obj]
    else:
        return obj


