from typing import List, Dict, Union, Any
import re
from enum import Enum
from dataclasses import dataclass
from datetime import datetime  # Added from code 2

class ParseError(Exception):
    """Base exception for parsing errors."""
    pass

class SyntaxError(ParseError):
    """Raised for invalid syntax in conditions."""
    pass

class UnsupportedOperatorError(ParseError):
    """Raised for unsupported operators or conditions."""
    pass

class Operator(Enum):
    """Supported MongoDB operators."""
    EQ = ('=', '$eq')
    NE = ('!=', '$ne')
    GT = ('>', '$gt')
    GTE = ('>=', '$gte')
    LT = ('<', '$lt')
    LTE = ('<=', '$lte')
    NE_ALT = ('<>', '$ne')

    @classmethod
    def from_sql(cls, sql_op: str) -> 'Operator':
        """Map SQL operator to MongoDB operator."""
        for op in cls:
            if op.value[0] == sql_op:
                return op
        raise UnsupportedOperatorError(f"Unsupported operator: {sql_op}")

@dataclass
class Token:
    """Represents a parsed token."""
    value: str
    type: str  # 'field', 'operator', 'value', 'keyword', 'paren'

class MongoFilterParser:
    """Parses SQL-like WHERE conditions into MongoDB filters."""
    
    def __init__(self):
        self.op_map = {op.value[0]: op.value[1] for op in Operator}
        self.keywords = {'AND', 'OR', 'LIKE', 'ILIKE', 'NOT LIKE', 'NOT ILIKE', 'IN', 'NOT IN', 'IS', 'IS NOT', 'BETWEEN', 'EXISTS', 'NOT EXISTS'}
        
        # Pre-compile regex patterns for better performance
        self.compiled_token_pattern = re.compile(
            r"'[^']*'|"  # Quoted strings
            r'"[^"]*"|'  # Double quoted strings
            r'[\(\)]|\w+\.\w+|<>|[<>=!]=|[<>]|'  # Individual parens, dot fields, operators (multi-char first)
            r'(?:NOT\s+LIKE|NOT\s+IN|NOT\s+EXISTS|IS\s+NOT|BETWEEN\s+[^\s)]+\s+AND\s+[^\s)]+|IN\s*\([^)]*\)|NOT\s+IN\s*\([^)]*\)|EXISTS\s*\([^)]*\)|IN|NOT|AND|OR|IS|EXISTS)|'  # Keywords including IN clauses
            r'\w+|'  # Individual words
            r'\S+'  # Fallback for other tokens
        )
        self.whitespace_pattern = re.compile(r'\s+')
        self.field_pattern = re.compile(r'\w+\.\w+')
        self.between_pattern = re.compile(r'BETWEEN\s+[^\s)]+\s+AND\s+[^\s)]+', re.IGNORECASE)
        self.in_pattern = re.compile(r'IN\s*\([^)]*\)', re.IGNORECASE)
        self.not_in_pattern = re.compile(r'NOT\s+IN\s*\([^)]*\)', re.IGNORECASE)
        self.comma_split_pattern = re.compile(r',\s*')
        
        # Pre-compile condition parsing patterns
        self.condition_patterns = {
            'is_null': re.compile(r'(.+)\s+IS\s+NULL\s*$', re.IGNORECASE),
            'is_not_null': re.compile(r'(.+)\s+IS\s+NOT\s+NULL\s*$', re.IGNORECASE),
            'not_ilike': re.compile(r'(.+)\s+NOT\s+ILIKE\s+(.+)', re.IGNORECASE),
            'ilike': re.compile(r'(.+)\s+ILIKE\s+(.+)', re.IGNORECASE),
            'not_like': re.compile(r'(.+)\s+NOT\s+LIKE\s+(.+)', re.IGNORECASE),
            'like': re.compile(r'(.+)\s+LIKE\s+(.+)', re.IGNORECASE),
            'between': re.compile(r'(.+)\s+BETWEEN\s+(.+)\s+AND\s+(.+)', re.IGNORECASE),
            'in': re.compile(r'(.+)\s+IN\s+(.+)', re.IGNORECASE),
            'not_in': re.compile(r'(.+)\s+NOT\s+IN\s+(.+)', re.IGNORECASE),
            'exists': re.compile(r'(.+)\s+EXISTS\s+(.+)', re.IGNORECASE),
            'not_exists': re.compile(r'(.+)\s+NOT\s+EXISTS\s+(.+)', re.IGNORECASE),
            'between_extract': re.compile(r'(\w+)\s+BETWEEN\s+([^\s]+)\s+AND\s+([^\s]+)', re.IGNORECASE),
            'boolean_true': re.compile(r'(.+)\s*=\s*1\s*$', re.IGNORECASE),
            'boolean_false': re.compile(r'(.+)\s*=\s*0\s*$', re.IGNORECASE),
            'boolean_not_true': re.compile(r'(.+)\s*!=\s*1\s*$', re.IGNORECASE),
            'boolean_not_false': re.compile(r'(.+)\s*!=\s*0\s*$', re.IGNORECASE)
        }

    def tokenize(self, condition: str) -> List[Token]:
        """Tokenize a condition string into tokens."""
        condition = self.whitespace_pattern.sub(' ', condition.strip())
        tokens = []
        i = 0
        while i < len(condition):
            if condition[i].isspace():
                i += 1
                continue
            for match in self.compiled_token_pattern.finditer(condition[i:]):
                value = match.group(0)
                start, end = match.span()
                if start == 0:  # Only match tokens starting at current position
                    if value in '()':
                        typ = 'paren'
                    elif (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
                        typ = 'value'
                    elif self.field_pattern.match(value):
                        typ = 'field'
                    elif value in {'=', '!=', '>', '>=', '<', '<=', '<>'}:
                        typ = 'operator'
                    elif self.between_pattern.match(value):
                        typ = 'keyword'  # BETWEEN clause
                    elif self.in_pattern.match(value):
                        typ = 'keyword'  # IN clause with parentheses
                    elif self.not_in_pattern.match(value):
                        typ = 'keyword'  # NOT IN clause with parentheses
                    elif value.upper() in self.keywords or value.upper().startswith('IN '):
                        typ = 'keyword'
                    else:
                        typ = 'value'
                    tokens.append(Token(value, typ))
                    i += end
                    break
            else:
                raise SyntaxError(f"Invalid token at position {i} in '{condition}'")
        return tokens

    def parse_value(self, value: str) -> Any:
        """Convert string value to appropriate type."""
        value = value.strip()
        if value.lower() == 'true':
            return True
        if value.lower() == 'false':
            return False
        if value.isdigit():
            return int(value)
        if value.replace('.', '', 1).isdigit():
            return float(value)
        if value.startswith("'") and value.endswith("'"):
            return value.strip("'")
        return value

    def parse_single_condition(self, cond: str) -> Dict:
        """Parse a single condition into a MongoDB filter."""
        cond = cond.strip()
        if not cond:  # Early exit for empty conditions
            return {}
            
        try:
            # Use pre-compiled patterns for better performance
            # Handle boolean conditions first
            match = self.condition_patterns['boolean_true'].match(cond)
            if match:
                return {self.get_filter_key(match.group(1)): True}
                
            match = self.condition_patterns['boolean_false'].match(cond)
            if match:
                return {self.get_filter_key(match.group(1)): False}
                
            match = self.condition_patterns['boolean_not_true'].match(cond)
            if match:
                return {self.get_filter_key(match.group(1)): {'$ne': True}}
                
            match = self.condition_patterns['boolean_not_false'].match(cond)
            if match:
                return {self.get_filter_key(match.group(1)): {'$ne': False}}
            
            match = self.condition_patterns['is_null'].match(cond)
            if match:
                return {self.get_filter_key(match.group(1)): {'$exists': False}}
                
            match = self.condition_patterns['is_not_null'].match(cond)
            if match:
                return {self.get_filter_key(match.group(1)): {'$exists': True}}
                
            match = self.condition_patterns['not_ilike'].match(cond)
            if match:
                field, pattern = match.groups()
                pattern = self._convert_like_pattern(pattern.strip("'"))
                return {self.get_filter_key(field): {'$not': {'$regex': pattern, '$options': 'i'}}}
                
            match = self.condition_patterns['ilike'].match(cond)
            if match:
                field, pattern = match.groups()
                pattern = self._convert_like_pattern(pattern.strip("'"))
                return {self.get_filter_key(field): {'$regex': pattern, '$options': 'i'}}
                
            match = self.condition_patterns['not_like'].match(cond)
            if match:
                field, pattern = match.groups()
                pattern = self._convert_like_pattern(pattern.strip("'"))
                return {self.get_filter_key(field): {'$not': {'$regex': pattern}}}
                
            match = self.condition_patterns['like'].match(cond)
            if match:
                field, pattern = match.groups()
                pattern = self._convert_like_pattern(pattern.strip("'"))
                return {self.get_filter_key(field): {'$regex': pattern}}
                
            match = self.condition_patterns['between'].match(cond)
            if match:
                field, start_val, end_val = match.groups()
                return {self.get_filter_key(field): {'$gte': self.parse_value(start_val), '$lte': self.parse_value(end_val)}}
                
            match = self.condition_patterns['in'].match(cond)
            if match:
                field, values = match.groups()
                if values.startswith('(') and values.endswith(')'):
                    values = values[1:-1]
                values = list(self._parse_comma_separated_values(values))
                return {self.get_filter_key(field): {'$in': values}}
                
            match = self.condition_patterns['not_in'].match(cond)
            if match:
                field, values = match.groups()
                if values.startswith('(') and values.endswith(')'):
                    values = values[1:-1]
                values = list(self._parse_comma_separated_values(values))
                return {self.get_filter_key(field): {'$nin': values}}
                
            if ' EXISTS ' in cond.upper():
                # For EXISTS, we'll use a placeholder - in real implementation,
                # this would be handled by the subquery processor
                return {'$expr': {'$gt': [{'$size': 'SUBQUERY_RESULTS'}, 0]}}
            if ' NOT EXISTS ' in cond.upper():
                # For NOT EXISTS, we'll use a placeholder
                return {'$expr': {'$eq': [{'$size': 'SUBQUERY_RESULTS'}, 0]}}
            if cond.upper().startswith('NOT EXISTS'):
                # Handle NOT EXISTS at the beginning of condition
                return {'$expr': {'$eq': [{'$size': 'SUBQUERY_RESULTS'}, 0]}}
                
            # Enhanced operator parsing to handle multi-character operators properly
            for sql_op, mongo_op in sorted(self.op_map.items(), key=len, reverse=True):
                op_pattern = f' {re.escape(sql_op)} '
                if op_pattern in cond:
                    parts = cond.split(op_pattern, 1)
                    if len(parts) == 2:
                        field, value = parts
                        return {self.get_filter_key(field): {mongo_op: self.parse_value(value)}}
            raise UnsupportedOperatorError(f"Unsupported condition: {cond}")
        except Exception as e:
            raise SyntaxError(f"Error parsing condition '{cond}': {str(e)}")
    
    def _parse_comma_separated_values(self, values_str):
        """Generator-based value parsing for better performance."""
        for v in self.comma_split_pattern.split(values_str):
            v = v.strip()
            if v:
                yield self.parse_value(v)
        
    def get_filter_key(self, field: str) -> str:
        """Get the MongoDB filter key for a given field."""
        return field.strip().replace(' ', '')

    def _convert_like_pattern(self, pattern: str) -> str:
        """Convert SQL LIKE pattern to MongoDB regex pattern."""
        import re
        
        # Track original wildcards before processing
        starts_with_wildcard = pattern.startswith('%')
        ends_with_wildcard = pattern.endswith('%')
        
        # Replace SQL wildcards with unique placeholders
        temp_pattern = pattern.replace('%', '<<<PERCENT>>>').replace('_', '<<<UNDERSCORE>>>')
        
        # Escape special regex characters  
        escaped = re.escape(temp_pattern)
        
        # Convert placeholders to regex equivalents
        regex_pattern = escaped.replace('<<<PERCENT>>>', '.*').replace('<<<UNDERSCORE>>>', '.')
        
        # Add anchors based on original pattern
        if starts_with_wildcard and ends_with_wildcard:
            # Contains: %pattern% → no anchors, remove leading/trailing .*
            regex_pattern = regex_pattern[2:-2]
        elif starts_with_wildcard:
            # Ends with: %pattern → pattern$
            regex_pattern = regex_pattern[2:] + '$'
        elif ends_with_wildcard:
            # Starts with: pattern% → ^pattern
            regex_pattern = '^' + regex_pattern[:-2]
        else:
            # Exact match: pattern → ^pattern$
            regex_pattern = '^' + regex_pattern + '$'
            
        return regex_pattern

    def parse(self, condition: str, depth: int = 0, max_depth: int = 10) -> Dict:
        """Parse the entire condition into a MongoDB filter."""
        if depth > max_depth:
            raise SyntaxError("Maximum recursion depth exceeded")
        
        tokens = self.tokenize(condition)
        if not tokens:
            return {}
        
        stack: List[List[Union[Token, Dict]]] = [[]]
        i = 0
        max_iterations = len(tokens) * 2
        iteration = 0
        
        while i < len(tokens):
            if iteration > max_iterations:
                raise SyntaxError(f"Infinite loop detected while parsing '{condition}'")
            iteration += 1
            
            token = tokens[i]
            if token.value == '(':
                i = self._handle_opening_paren(tokens, i, stack, depth, max_depth)
            elif token.value == ')':
                result = self._handle_closing_paren(stack, depth, max_depth)
                if result == -1:
                    pass  # Don't increment here, let the main loop handle it
                else:
                    i = result  # Use returned index
            elif token.value.upper() == 'NOT' and i + 1 < len(tokens) and tokens[i + 1].value == '(':
                stack.append([Token('NOT', 'keyword')])
                i += 1
            elif token.value.upper() == 'OR' and len(stack) == 1:
                # Handle top-level OR operator
                stack[-1].append(token)
            else:
                stack[-1].append(token)
            i += 1
        
        if len(stack) > 1:
            raise SyntaxError("Mismatched opening parenthesis")
        
        return self._process_top_level_tokens(stack[0], depth, max_depth)

    def _handle_opening_paren(self, tokens: List[Token], i: int, stack: List[List[Union[Token, Dict]]], depth: int, max_depth: int) -> int:
        """Handle opening parenthesis, including IN clause detection."""
        # Check if this is part of an IN clause
        is_in_clause = self._is_in_clause_context(tokens, i, stack)
        
        if is_in_clause:
            return self._process_in_clause(tokens, i, stack)
        else:
            stack.append([])
            return i

    def _is_in_clause_context(self, tokens: List[Token], i: int, stack: List[List[Union[Token, Dict]]]) -> bool:
        """Check if the opening parenthesis is part of an IN clause."""
        # Check if the last two tokens are field and IN
        if len(stack[-1]) >= 2:
            last_tokens = stack[-1][-2:]
            if (isinstance(last_tokens[0], Token) and last_tokens[0].value.upper() == 'IN') or \
               (isinstance(last_tokens[1], Token) and last_tokens[1].value.upper() == 'IN'):
                return True
        
        # Check if the last three tokens are field, NOT, and IN
        if len(stack[-1]) >= 3:
            last_tokens = stack[-1][-3:]
            if (isinstance(last_tokens[0], Token) and last_tokens[0].value.upper() == 'NOT' and
                isinstance(last_tokens[1], Token) and last_tokens[1].value.upper() == 'IN'):
                return True
        
        # Check if the previous token in the sequence is IN
        return i > 0 and tokens[i-1].value.upper() == 'IN'

    def _process_in_clause(self, tokens: List[Token], i: int, stack: List[List[Union[Token, Dict]]]) -> int:
        """Process an IN clause including parentheses."""
        in_tokens = []
        
        # Find the field name and IN token in the stack or token sequence
        field_name, in_token, not_token = self._find_in_clause_tokens(tokens, i, stack)
        
        if field_name and in_token:
            # Remove the field name and IN token from the stack if they're there
            self._remove_tokens_from_stack(stack, field_name, in_token, not_token)
            
            # Build the IN clause
            if not_token:
                in_tokens.append(not_token)
            in_tokens.append(field_name)
            in_tokens.append(in_token)
            in_tokens.append(tokens[i])  # Add the opening parenthesis
            
            # Collect tokens until matching closing parenthesis
            j = i + 1
            paren_count = 1
            while j < len(tokens) and paren_count > 0:
                if tokens[j].value == '(':
                    paren_count += 1
                elif tokens[j].value == ')':
                    paren_count -= 1
                in_tokens.append(tokens[j])
                j += 1
            
            # Create a single token for the entire IN clause
            in_clause = ' '.join([t.value for t in in_tokens])
            stack[-1].append(Token(in_clause, 'keyword'))
            return j
        else:
            stack.append([])
            return i

    def _find_in_clause_tokens(self, tokens: List[Token], i: int, stack: List[List[Union[Token, Dict]]]) -> tuple:
        """Find field name, IN token, and NOT token for IN clause processing."""
        field_name = None
        in_token = None
        not_token = None
        
        # First try to find in the stack
        for j in range(len(stack[-1]) - 1, -1, -1):
            if isinstance(stack[-1][j], Token) and stack[-1][j].value.upper() == 'IN':
                in_token = stack[-1][j]
                if j > 0 and isinstance(stack[-1][j-1], Token):
                    field_name = stack[-1][j-1]
                    if j > 1 and isinstance(stack[-1][j-2], Token) and stack[-1][j-2].value.upper() == 'NOT':
                        not_token = stack[-1][j-2]
                break
        
        # If not found in stack, look in the token sequence
        if not field_name and i > 0:
            in_token = tokens[i-1]
            if i > 1:
                field_name = tokens[i-2]
                if i > 2 and tokens[i-3].value.upper() == 'NOT':
                    not_token = tokens[i-3]
        
        return field_name, in_token, not_token

    def _remove_tokens_from_stack(self, stack: List[List[Union[Token, Dict]]], field_name, in_token, not_token):
        """Remove tokens from stack for IN clause processing."""
        if field_name in stack[-1]:
            stack[-1].remove(field_name)
        if in_token in stack[-1]:
            stack[-1].remove(in_token)
        if not_token and not_token in stack[-1]:
            stack[-1].remove(not_token)

    def _handle_closing_paren(self, stack: List[List[Union[Token, Dict]]], depth: int, max_depth: int) -> int:
        """Handle closing parenthesis."""
        if len(stack) > 1:
            sub_filter = self._parse_sub_condition(stack.pop(), depth + 1, max_depth)
            if stack:
                stack[-1].append(sub_filter)
        else:
            raise SyntaxError("Mismatched closing parenthesis")
        return -1  # Signal that the caller should not increment i

    def _process_top_level_tokens(self, top_level_tokens: List[Union[Token, Dict]], depth: int, max_depth: int) -> Dict:
        """Process top-level tokens, handling OR operators."""
        or_positions = []
        for i, token in enumerate(top_level_tokens):
            if isinstance(token, Token) and token.value.upper() == 'OR':
                or_positions.append(i)
        
        if or_positions:
            return self._process_or_conditions(top_level_tokens, or_positions, depth, max_depth)
        else:
            return self._parse_sub_condition(top_level_tokens, depth + 1, max_depth)

    def _process_or_conditions(self, tokens: List[Union[Token, Dict]], or_positions: List[int], depth: int, max_depth: int) -> Dict:
        """Process OR conditions at the top level."""
        parts = []
        start = 0
        for or_pos in or_positions:
            if start < or_pos:
                parts.append(tokens[start:or_pos])
            start = or_pos + 1
        if start < len(tokens):
            parts.append(tokens[start:])
        
        # Parse each part and combine with OR
        sub_filters = []
        for part in parts:
            if part:
                sub_filter = self._parse_sub_condition(part, depth + 1, max_depth)
                sub_filters.append(sub_filter)
        
        if len(sub_filters) == 1:
            return sub_filters[0]
        else:
            return {'$or': sub_filters}

    def _parse_sub_condition(self, tokens: List[Union[Token, Dict]], depth: int, max_depth: int) -> Dict:
        """Parse a group of tokens into a MongoDB filter."""
        if not tokens:
            return {}
        
        parts = self._split_tokens_into_parts(tokens)
        sub_filters, logical_ops = self._process_token_parts(parts, depth, max_depth)
        
        if not sub_filters:
            return {}
        if len(sub_filters) == 1:
            return sub_filters[0]
        
        return self._combine_filters_with_logical_ops(sub_filters, logical_ops)

    def _split_tokens_into_parts(self, tokens: List[Union[Token, Dict]]) -> List[tuple]:
        """Split tokens into parts based on logical operators."""
        parts = []
        current = []
        i = 0
        max_iterations = len(tokens) * 2
        iteration = 0
        
        while i < len(tokens):
            if iteration > max_iterations:
                raise SyntaxError("Infinite loop detected in sub-condition parsing")
            iteration += 1
            
            token = tokens[i]
            if isinstance(token, dict):
                if current:
                    parts.append((current, None))
                    current = []
                parts.append(([token], None))
            elif isinstance(token, Token) and token.value.upper() in ('AND', 'OR'):
                if current:
                    parts.append((current, token.value.upper()))
                    current = []
                else:
                    # Handle standalone AND/OR operators
                    parts.append(([token], token.value.upper()))
            else:
                current.append(token)
            i += 1
        
        if current:
            parts.append((current, None))
        
        return parts

    def _process_token_parts(self, parts: List[tuple], depth: int, max_depth: int) -> tuple:
        """Process token parts into filters and logical operators."""
        sub_filters = []
        logical_ops = []
        
        for part, op in parts:
            if not part:
                continue
            if len(part) == 1 and isinstance(part[0], dict):
                sub_filters.append(part[0])
            elif len(part) == 1 and isinstance(part[0], Token) and part[0].value.upper() in ('AND', 'OR'):
                # Skip standalone AND/OR operators - they're handled by the logical_ops
                continue
            elif isinstance(part[0], Token) and part[0].value.upper() == 'NOT':
                sub_filters.append(self._process_not_condition(part, depth, max_depth))
            else:
                sub_filters.append(self._process_regular_condition(part))
            if op:
                logical_ops.append(op)
        
        return sub_filters, logical_ops

    def _process_not_condition(self, part: List[Union[Token, Dict]], depth: int, max_depth: int) -> Dict:
        """Process NOT conditions."""
        # Check if this is an IS NOT clause (like "IS NOT NULL")
        if len(part) >= 3 and isinstance(part[1], Token) and part[1].value.upper() == 'IS':
            # This is an IS NOT clause, handle it as a special clause
            cond = ' '.join(t.value if isinstance(t, Token) else str(t) for t in part)
            return self.parse_single_condition(cond)
        elif len(part) >= 3 and isinstance(part[1], Token) and part[1].value != '(':
            # This is a NOT condition without parentheses (like "NOT age IS NULL")
            sub_condition = self._parse_sub_condition(part[1:], depth + 1, max_depth)
            return {'$not': sub_condition}
        elif len(part) < 3 or not isinstance(part[1], Token) or part[1].value != '(' or not isinstance(part[-1], Token) or part[-1].value != ')':
            raise SyntaxError("Invalid NOT condition")
        else:
            sub_condition = self._parse_sub_condition(part[2:-1], depth + 1, max_depth)
            return {'$not': sub_condition}

    def _process_regular_condition(self, part: List[Union[Token, Dict]]) -> Dict:
        """Process regular conditions (non-NOT)."""
        # Handle special clauses
        if len(part) >= 3 and isinstance(part[1], Token) and part[1].value.upper() == 'IN':
            # This is an IN clause, reconstruct it properly
            field = part[0].value if isinstance(part[0], Token) else str(part[0])
            in_values = []
            for token in part[2:]:
                if isinstance(token, Token):
                    in_values.append(token.value)
                else:
                    in_values.append(str(token))
            cond = f"{field} IN ({' '.join(in_values)})"
        elif len(part) >= 5 and isinstance(part[1], Token) and part[1].value.upper() == 'BETWEEN':
            # This is a BETWEEN clause, reconstruct it properly
            field = part[0].value if isinstance(part[0], Token) else str(part[0])
            start_val = part[2].value if isinstance(part[2], Token) else str(part[2])
            end_val = part[4].value if isinstance(part[4], Token) else str(part[4])
            cond = f"{field} BETWEEN {start_val} AND {end_val}"
        else:
            cond = ' '.join(t.value if isinstance(t, Token) else str(t) for t in part)
        return self.parse_single_condition(cond)

    def _combine_filters_with_logical_ops(self, sub_filters: List[Dict], logical_ops: List[str]) -> Dict:
        """Combine filters using logical operators."""
        if not logical_ops:
            return {'$and': sub_filters}
        
        if all(op == 'AND' for op in logical_ops):
            return {'$and': sub_filters}
        elif all(op == 'OR' for op in logical_ops):
            return {'$or': sub_filters}
        else:
            # Mixed operators - group by operator type
            return self._handle_mixed_logical_operators(sub_filters, logical_ops)

    def _handle_mixed_logical_operators(self, sub_filters: List[Dict], logical_ops: List[str]) -> Dict:
        """Handle mixed AND/OR logical operators."""
        and_groups = []
        or_groups = []
        current_group = []
        current_op = None
        
        for i, (filter, op) in enumerate(zip(sub_filters, logical_ops + [None])):
            if op != current_op and current_group:
                if current_op == 'AND':
                    and_groups.extend(current_group)
                else:
                    or_groups.extend(current_group)
                current_group = []
            current_group.append(filter)
            current_op = op
        
        if current_group:
            if current_op == 'AND':
                and_groups.extend(current_group)
            else:
                or_groups.extend(current_group)
        
        if and_groups and or_groups:
            return {'$or': [{'$and': and_groups}, {'$and': or_groups}]}
        elif and_groups:
            return {'$and': and_groups}
        elif or_groups:
            return {'$or': or_groups}
        
        return {'$and': sub_filters}

    # New methods from code 2
    def parse_value(self, value: str, field_name: str = None) -> Any:  # Added from code 2
        """Parse value with context awareness for dates"""
        value = value.strip()
        if value.lower() == 'true':
            return True
        if value.lower() == 'false':
            return False
        
        # Remove quotes if present
        if value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
        
        # Check if this looks like a date (YYYY-MM-DD format)
        # or if the field name suggests it's a date field
        if (field_name and 'date' in field_name.lower()):
            try:
                # Try to parse as date
                dt = datetime.strptime(value, '%Y-%m-%d')
                return dt
            except:
                pass
        
        # Try to parse as number
        if value.replace('.', '').replace('-', '').isdigit():
            if '.' in value:
                try:
                    return float(value)
                except:
                    pass
            else:
                try:
                    return int(value)
                except:
                    pass
        
        return value

    def escape_regex_special_chars(self, pattern: str) -> str:  # Added from code 2
        """Escape special regex characters except for SQL wildcards"""
        # Escape regex special characters but not % and _
        special_chars = r'\.^$*+?{}[]|()'
        for char in special_chars:
            pattern = pattern.replace(char, '\\' + char)
        # Now replace SQL wildcards
        pattern = pattern.replace('%', '.*')
        pattern = pattern.replace('_', '.')
        return pattern

    def sql_like_to_regex(self, pattern: str) -> str:  # Added from code 2
        """Convert SQL LIKE pattern to MongoDB regex pattern"""
        # First escape special regex characters
        pattern = self.escape_regex_special_chars(pattern)
        # Add anchors if needed
        if not pattern.startswith('.*'):
            pattern = '^' + pattern
        return pattern

    def extract_between_clause(self, text: str):  # Added from code 2
        """Extract a complete BETWEEN clause from text"""
        between_match = self.condition_patterns['between_extract'].search(text)
        if between_match:
            field = between_match.group(1)
            start_val = between_match.group(2)
            end_val = between_match.group(3)
            full_match = between_match.group(0)
            return field, start_val, end_val, full_match
        return None

    def find_matching_paren(self, text: str, start: int) -> int:  # Added from code 2
        """Find the matching closing parenthesis"""
        depth = 1
        i = start + 1
        while i < len(text) and depth > 0:
            if text[i] == '(':
                depth += 1
            elif text[i] == ')':
                depth -= 1
            i += 1
        return i - 1 if depth == 0 else -1

    def split_by_top_level_or(self, condition: str) -> List[str]:  # Added from code 2
        """Split by OR only at the top level (not inside parentheses)"""
        parts = []
        current = []
        paren_depth = 0
        i = 0
        
        while i < len(condition):
            if condition[i] == '(':
                paren_depth += 1
                current.append(condition[i])
            elif condition[i] == ')':
                paren_depth -= 1
                current.append(condition[i])
            elif paren_depth == 0 and condition[i:i+4].upper() == ' OR ':
                parts.append(''.join(current).strip())
                current = []
                i += 3  # Skip ' OR'
            else:
                current.append(condition[i])
            i += 1
        
        if current:
            parts.append(''.join(current).strip())
        
        return parts

    def split_by_top_level_and(self, condition: str) -> List[str]:  # Added from code 2
        """Split by AND only at the top level (not inside parentheses)"""
        parts = []
        current = []
        paren_depth = 0
        i = 0
        
        while i < len(condition):
            if condition[i] == '(':
                paren_depth += 1
                current.append(condition[i])
            elif condition[i] == ')':
                paren_depth -= 1
                current.append(condition[i])
            elif paren_depth == 0 and condition[i:i+5].upper() == ' AND ':
                parts.append(''.join(current).strip())
                current = []
                i += 4  # Skip ' AND'
            else:
                current.append(condition[i])
            i += 1
        
        if current:
            parts.append(''.join(current).strip())
        
        return parts