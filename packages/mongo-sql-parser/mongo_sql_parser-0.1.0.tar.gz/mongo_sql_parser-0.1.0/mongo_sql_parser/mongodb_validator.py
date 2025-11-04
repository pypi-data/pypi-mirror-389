"""
MongoDB Expression Validator - Validates MongoDB shell queries for security and correctness.

This validator can be extended with custom response handlers for service-specific implementations.
"""
import json
import logging as lg
import re
from typing import Dict, Any, Callable, Optional


class MongoExpressionValidator:
    """
    Validates MongoDB shell expressions to ensure they are safe read-only queries.
    
    Can be extended with custom response handlers by subclassing or providing
    callback functions for service-specific implementations.
    """
    
    def __init__(self, response_handler: Optional[Callable[[str], Any]] = None):
        """
        Initialize the validator.
        
        Args:
            response_handler: Optional function that takes an error code and returns
                           a response. If None, returns simple string codes.
        """
        self.response_handler = response_handler or (lambda code: code)
    
    def validate(self, config: Dict[str, Any]) -> Any:
        """
        Validate a MongoDB shell query.
        
        Args:
            config: Dictionary containing:
                   - query: MongoDB shell query string
                   - ruleSubType: Optional validation subtype
                   
        Returns:
            Validation result (handled by response_handler or error code string)
        """
        try:
            query = config["query"].strip()
            rule_sub_type = config.get("ruleSubType", "")

            if not query.startswith("db."):
                return self.response_handler('sql_select_error')

            # Block write ops at top level
            write_operations = [
                '.insert(', '.update(', '.deleteone(', '.deletemany(',
                '.remove(', '.save(', '.replaceone(', '.updateone(',
                '.updatemany(', '.findoneandupdate(', '.findoneandreplace(',
                '.findoneanddelete(', '.bulkwrite('
            ]
            query_lower = query.lower()
            for op in write_operations:
                if op in query_lower:
                    lg.warning(f"Write operation detected: {op}")
                    return self.response_handler('sql_select_error')

            parts = query.split(".", 2)
            if len(parts) < 3:
                return self.response_handler('sql_validator_error')
            command_part = parts[2]

            if command_part.startswith("find("):
                return self._validate_find_query(command_part, rule_sub_type, query)
            elif command_part.startswith("aggregate("):
                return self._validate_aggregate_query(command_part, rule_sub_type)
            else:
                return self.response_handler('sql_select_error')
        except Exception as err:
            lg.error(f"MongoDB validation error: {str(err)}", exc_info=True)
            return self.response_handler('sql_validator_error')

    # ----------------- Core parsing helpers -----------------
    def _extract_parentheses_content(self, command_part):
        start_idx = command_part.find("(") + 1
        end_idx = command_part.rfind(")")
        if start_idx <= 0 or end_idx < start_idx:
            return None
        return command_part[start_idx:end_idx].strip()

    def _extract_first_arg_inside_parentheses(self, command_part):
        inner = self._extract_parentheses_content(command_part)
        if inner is None:
            return None
        inner = inner.strip()
        if not inner:
            return ""
        depth_round = depth_square = depth_curly = 0
        in_string = False
        string_char = None
        escaped = False
        for i, ch in enumerate(inner):
            if escaped:
                escaped = False
                continue
            if ch == '\\':
                escaped = True
                continue
            if in_string:
                if ch == string_char:
                    in_string = False
                continue
            if ch in ('"', "'"):
                in_string = True
                string_char = ch
                continue
            if ch == '(':
                depth_round += 1
            elif ch == ')':
                depth_round -= 1
            elif ch == '[':
                depth_square += 1
            elif ch == ']':
                depth_square -= 1
            elif ch == '{':
                depth_curly += 1
            elif ch == '}':
                depth_curly -= 1
            elif ch == ',' and depth_round == 0 and depth_square == 0 and depth_curly == 0:
                return inner[:i].strip()
        return inner.strip()

    def _split_top_level_args(self, args_str):
        if args_str is None:
            return []
        args = []
        start = 0
        depth_round = depth_square = depth_curly = 0
        in_string = False
        string_char = None
        escaped = False
        for i, ch in enumerate(args_str):
            if escaped:
                escaped = False
                continue
            if ch == '\\':
                escaped = True
                continue
            if in_string:
                if ch == string_char:
                    in_string = False
                continue
            if ch in ('"', "'"):
                in_string = True
                string_char = ch
                continue
            if ch == '(':
                depth_round += 1
            elif ch == ')':
                depth_round -= 1
            elif ch == '[':
                depth_square += 1
            elif ch == ']':
                depth_square -= 1
            elif ch == '{':
                depth_curly += 1
            elif ch == '}':
                depth_curly -= 1
            elif ch == ',' and depth_round == 0 and depth_square == 0 and depth_curly == 0:
                args.append(args_str[start:i].strip())
                start = i + 1
        last = args_str[start:].strip()
        if last:
            args.append(last)
        return args

    # ----------------- Normalization and JSON helpers -----------------
    def _is_valid_json(self, json_str):
        try:
            json.loads(json_str)
            return True
        except json.JSONDecodeError:
            return False

    def _normalize_mongodb_json(self, json_str):
        # ISODate -> string
        iso_date_pattern = r'ISODate\("([^"]+)"\)'
        json_str = re.sub(iso_date_pattern, r'"\1"', json_str)
        # ObjectId -> string
        objectid_pattern = r'ObjectId\("([^"]+)"\)'
        json_str = re.sub(objectid_pattern, r'"\1"', json_str)

        # Quote unquoted keys
        def process_unquoted_keys(text):
            result = []
            i = 0
            in_string = False
            escape_next = False
            while i < len(text):
                ch = text[i]
                if escape_next:
                    escape_next = False
                    result.append(ch)
                    i += 1
                    continue
                if ch == '\\':
                    escape_next = True
                    result.append(ch)
                    i += 1
                    continue
                if ch in ('"', "'"):
                    in_string = not in_string
                    result.append(ch)
                    i += 1
                    continue
                if in_string:
                    result.append(ch)
                    i += 1
                    continue
                match = re.match(r'([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:', text[i:])
                if match:
                    if i == 0 or text[i-1] not in ('"', "'"):
                        key = match.group(1)
                        result.append(f'"{key}":')
                        i += len(match.group(0))
                        continue
                result.append(ch)
                i += 1
            return ''.join(result)

        json_str = process_unquoted_keys(json_str)

        # Quote $field references as values
        def process_field_references(text):
            result = []
            i = 0
            in_string = False
            escape_next = False
            while i < len(text):
                ch = text[i]
                if escape_next:
                    escape_next = False
                    result.append(ch)
                    i += 1
                    continue
                if ch == '\\':
                    escape_next = True
                    result.append(ch)
                    i += 1
                    continue
                if ch in ('"', "'"):
                    in_string = not in_string
                    result.append(ch)
                    i += 1
                    continue
                if in_string:
                    result.append(ch)
                    i += 1
                    continue
                if ch == ':' and i + 1 < len(text):
                    match = re.match(r':\s*(\$[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)', text[i:])
                    if match:
                        field_ref = match.group(1)
                        after = i + len(match.group(0))
                        if after >= len(text) or text[after] != '"':
                            result.append(f': "{field_ref}"')
                            i += len(match.group(0))
                            continue
                result.append(ch)
                i += 1
            return ''.join(result)

        json_str = process_field_references(json_str)

        # Convert single-quoted strings to double-quoted
        single_quoted_string_pattern = r"'([^'\\]*(?:\\.[^'\\]*)*)'"
        def replace_single_quotes(m):
            inner = m.group(1).replace('"', '\\"')
            return f'"{inner}"'
        json_str = re.sub(single_quoted_string_pattern, replace_single_quotes, json_str)

        return json_str

    def _parse_json_array(self, json_str):
        try:
            normalized_json = self._normalize_mongodb_json(json_str)
            lg.debug(f"Normalized JSON (first 500 chars): {normalized_json[:500]}")
            parsed = json.loads(normalized_json)
            return parsed if isinstance(parsed, list) else None
        except json.JSONDecodeError as e:
            lg.error(f"JSON decode error: {str(e)}")
            lg.error(f"Original input (first 500 chars): {json_str[:500]}")
            return None

    # ----------------- Aggregate and Find validation -----------------
    def _validate_find_query(self, command_part, rule_sub_type, full_query):
        args_inside = self._extract_parentheses_content(command_part)
        if args_inside is None:
            return self.response_handler('sql_validator_error')

        top_level_args = self._split_top_level_args(args_inside)
        filter_arg = top_level_args[0] if len(top_level_args) >= 1 else ""
        projection_arg = top_level_args[1] if len(top_level_args) >= 2 else ""

        if filter_arg.strip():
            normalized_filter = self._normalize_mongodb_json(filter_arg)
            if not self._is_valid_json(normalized_filter):
                lg.error(f"Invalid find() filter JSON. Original: {filter_arg[:120]}, Normalized: {normalized_filter[:120]}")
                return self.response_handler('sql_validator_error')
        if projection_arg.strip():
            normalized_projection = self._normalize_mongodb_json(projection_arg)
            if not self._is_valid_json(normalized_projection):
                lg.error(f"Invalid find() projection JSON. Original: {projection_arg[:120]}, Normalized: {normalized_projection[:120]}")
                return self.response_handler('sql_validator_error')

        # Disallow write chains after find()
        find_pattern = "find("
        find_end = full_query.find(find_pattern)
        if find_end != -1:
            paren_end = full_query.find(")", find_end)
            if paren_end != -1:
                after_find = full_query[paren_end + 1:]
                restricted_chains = [
                    '.update(', '.delete(', '.remove(', '.insert(',
                    '.save(', '.replaceOne(', '.updateOne(',
                    '.updateMany(', '.findOneAndUpdate('
                ]
                after_find_lower = after_find.lower()
                for restricted in restricted_chains:
                    if restricted in after_find_lower:
                        lg.warning(f"Write operation chained after find(): {restricted}")
                        return self.response_handler('sql_select_error')

        return self.response_handler('sql_validator_success')

    def _validate_aggregate_query(self, command_part, rule_sub_type):
        first_arg = self._extract_first_arg_inside_parentheses(command_part)
        if first_arg is None:
            return self.response_handler('sql_validator_error')

        pipeline = self._parse_json_array(first_arg)
        if pipeline is None:
            return self.response_handler('sql_validator_error')

        # Block $out/$merge
        if self._has_write_stage(pipeline, '$out') or self._has_write_stage(pipeline, '$merge'):
            lg.warning("Write stage detected in pipeline: $out/$merge")
            return self.response_handler('sql_select_error')

        # For single value validator, check for aggregation functions
        # This is service-specific and can be overridden
        if rule_sub_type == 'single_value_validator':
            if not self._has_aggregation_functions(pipeline):
                return self.response_handler('sql_agg_error')

        return self.response_handler('sql_validator_success')

    # ----------------- Utility checks -----------------
    def _has_write_stage(self, pipeline, stage_name):
        if not isinstance(pipeline, list):
            return False
        for stage in pipeline:
            if isinstance(stage, dict) and stage_name in stage:
                return True
        return False

    def _has_aggregation_functions(self, pipeline):
        pipeline_str = json.dumps(pipeline).lower()
        aggregation_functions = ['$sum', '$count', '$avg', '$min', '$max']
        return any(func in pipeline_str for func in aggregation_functions)

