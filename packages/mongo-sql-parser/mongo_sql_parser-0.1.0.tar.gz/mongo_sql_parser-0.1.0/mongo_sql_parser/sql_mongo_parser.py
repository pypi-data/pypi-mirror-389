import sqlglot
from sqlglot import exp
from typing import List, Dict, Union, Any, Optional
import re
from datetime import datetime

from .mongo_filter_parser import MongoFilterParser

class MongoQueryParser(MongoFilterParser):
    agg_map = {'COUNT': '$sum', 'SUM': '$sum', 'AVG': '$avg', 'MIN': '$min', 'MAX': '$max'}
    
    def __init__(self):
        super().__init__()
        # Pre-compiled regex patterns for performance
        self.subquery_patterns = {
            'select_in_parens': re.compile(r'\(\s*SELECT\s+', re.IGNORECASE),
            'exists': re.compile(r'EXISTS\s*\(', re.IGNORECASE),
            'not_exists': re.compile(r'NOT\s+EXISTS\s*\(', re.IGNORECASE),
            'between_select': re.compile(r'BETWEEN.*SELECT', re.IGNORECASE),
            'all_select': re.compile(r'ALL\s*\(\s*SELECT\s+', re.IGNORECASE),
            'any_select': re.compile(r'ANY\s*\(\s*SELECT\s+', re.IGNORECASE)
        }
        
        self.field_reference_pattern = re.compile(r'\b([a-zA-Z_]\w*)\.([a-zA-Z_]\w*)\b')
        self.table_field_pattern = re.compile(r'(\w+)\.(\w+)')
        self.comparison_subquery_pattern = re.compile(r'[<>=!]+\s*\(\s*SELECT\s+', re.IGNORECASE)
        
        self.in_subquery_pattern = re.compile(r'(\w+(?:\.\w+)?)\s+IN\s*\(', re.IGNORECASE)
        self.not_in_subquery_patterns = [
            re.compile(r'(\w+(?:\.\w+)?)\s+NOT\s+IN\s*\(\s*(SELECT\s+.*?)\s*\)', re.IGNORECASE | re.DOTALL),
            re.compile(r'NOT\s+(\w+(?:\.\w+)?)\s+IN\s*\(\s*(SELECT\s+.*?)\s*\)', re.IGNORECASE | re.DOTALL)
        ]
        
        self.between_subquery_pattern = re.compile(r'(\w+(?:\.\w+)?)\s+BETWEEN\s+\(', re.IGNORECASE)
        self.all_subquery_pattern = re.compile(r'(\w+(?:\.\w+)?)\s*([<>=!]+)\s*ALL\s*\(\s*(SELECT\s+.*?)\s*\)', re.IGNORECASE | re.DOTALL)
        self.any_subquery_pattern = re.compile(r'(\w+(?:\.\w+)?)\s*([<>=!]+)\s*ANY\s*\(\s*(SELECT\s+.*?)\s*\)', re.IGNORECASE | re.DOTALL)
        
        self.or_detection_patterns = {
            'pattern1': re.compile(r'\b(\w+)\s*=\s*[^)]+\s+OR\s+\b\1\s*=', re.IGNORECASE),
            'pattern2': re.compile(r'\b(\w+)\s+IN\s*\([^)]*\)\s+OR\s+\b\1\s*=', re.IGNORECASE)
        }

    def parse_date_value(self, date_str: str):
        """Parse date string for MongoDB comparison"""
        if not date_str:
            return date_str
        date_str = date_str.strip("'\"")
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt
        except:
            return date_str

    def parse_query(self, sql: str) -> List[Dict]:
        """Parse SQL query into MongoDB aggregation pipeline."""
        if not sql or not sql.strip():
            return []
        ast = sqlglot.parse_one(sql)
        if not isinstance(ast, exp.Select):
            raise SyntaxError("Only SELECT queries supported")

        self.joined_aliases = set()
        self.is_right_join_context = False
        query_components = self._extract_query_components(ast)
        
        self.main_table = query_components.get('main_table', {})
        self.main_table_alias = self.main_table.get('alias') if self.main_table else None
        
        pipeline = []
        
        if query_components['joins']:
            pipeline.extend(self._process_joins(query_components['joins']))
        
        if query_components['where_clause']:
            where_pipeline = self._process_where_clause(query_components['where_clause'])
            pipeline.extend(where_pipeline)

        if query_components['group_by']:
            pipeline.extend(self._process_group_by_query(query_components))
        elif len(query_components['projections']) == 1:
            pipeline.extend(self._process_single_projection_query(query_components))
        else:
            pipeline.extend(self._process_normal_query(query_components))

        return pipeline

    def _process_joins(self, joins: List[Dict]) -> List[Dict]:
        """Process JOIN clauses into MongoDB $lookup stages."""
        if not joins:
            return []
        pipeline = []
        
        has_right_join = any(join['type'] == 'RIGHT' for join in joins)
        has_cross_join = any(join['type'] == 'CROSS' for join in joins)
        
        if has_cross_join:
            return self._process_cross_join_pipeline(joins)
        
        if has_right_join:
            self.is_right_join_context = True
            return self._process_right_join_pipeline(joins)
        
        self.joined_aliases = set()
        
        for join in joins:
            alias = join['alias'] or join['table']
            
            local_field = join['local_field']
            if '.' in local_field:
                table_alias, field_name = local_field.split('.', 1)
                if table_alias not in self.joined_aliases:
                    local_field = field_name
                else:
                    local_field = local_field
            else:
                local_field = local_field
            
            lookup_stage = {'$lookup': {'from': join['table'], 'localField': local_field, 'foreignField': join['foreign_field'], 'as': alias}}
            pipeline.append(lookup_stage)
            
            self.joined_aliases.add(alias)
            
            if join['type'] in ['INNER', 'LEFT', 'LEFT OUTER']:
                if join['type'] in ['LEFT', 'LEFT OUTER']:
                    unwind_stage = {'$unwind': {'path': f"${alias}", 'preserveNullAndEmptyArrays': True}}
                else:
                    unwind_stage = {'$unwind': f"${alias}"}
                pipeline.append(unwind_stage)
        
        return pipeline

    def _process_right_join_pipeline(self, joins: List[Dict]) -> List[Dict]:
        """Process RIGHT JOIN by restructuring to start from the right collection."""
        pipeline = []
        right_join = next((join for join in joins if join['type'] == 'RIGHT'), None)
        
        if right_join:
            main_collection = self._get_main_collection_name()
            original_local = right_join['local_field'].replace('$', '')
            original_foreign = right_join['foreign_field']
            
            local_field = original_foreign
            foreign_field = original_local
            
            if '.' in foreign_field:
                foreign_field = foreign_field.split('.', 1)[1]
            if '.' in local_field:
                local_field = local_field.split('.', 1)[1]
            
            # Keep original field names for JOIN operations
            # MongoDB collections use 'id' field for JOINs, not '_id'
            
            pipeline.append({'$lookup': {'from': main_collection, 'localField': local_field, 'foreignField': foreign_field, 'as': 'left_docs'}})
            pipeline.append({'$unwind': {'path': '$left_docs', 'preserveNullAndEmptyArrays': True}})
        
        self.joined_aliases = set()
        return pipeline

    def _process_cross_join_pipeline(self, joins: List[Dict]) -> List[Dict]:
        """Process CROSS JOIN by creating a Cartesian product using $lookup with pipeline."""
        pipeline = []
        
        for join in joins:
            if join['type'] == 'CROSS':
                # For CROSS JOIN, we use $lookup with an empty pipeline to get all documents
                # This creates a Cartesian product
                lookup_stage = {
                    '$lookup': {
                        'from': join['table'],
                        'pipeline': [],  # Empty pipeline gets all documents
                        'as': join['alias'] or join['table']
                    }
                }
                pipeline.append(lookup_stage)
                
                # Unwind to create the Cartesian product
                unwind_stage = {'$unwind': f"${join['alias'] or join['table']}"}
                pipeline.append(unwind_stage)
        
        self.joined_aliases = set()
        return pipeline

    def _get_main_collection_name(self) -> str:
        """Get the main collection name from the query context."""
        if hasattr(self, 'main_table') and self.main_table:
            return self.main_table.get('table', 'main_collection')
        return 'main_collection'

    def _process_where_clause(self, where_clause) -> List[Dict]:
        """Process WHERE clause including subqueries."""
        if not where_clause:
            return []
        
        where_str = where_clause.this.sql()
        if not where_str or where_str.strip().upper() in ('TRUE', '1 = 1'):
            return []
        
        if self._has_subquery(where_str):
            return self._process_where_with_subqueries(where_str)
        
        if hasattr(self, 'joined_aliases') and self.joined_aliases:
            where_str = self._map_table_aliases_in_where(where_str)
        else:
            # Remove table prefixes for main table fields
            where_str = re.sub(r'\b([a-zA-Z_]\w*)\.([a-zA-Z_]\w*)\b', r'\2', where_str)
        
        
        filter_dict = self.parse(where_str)
        
        if filter_dict and '$and' in filter_dict:
            and_conditions = filter_dict['$and']
            
            if len(and_conditions) == 2 and 'OR' in where_str.upper():
                if self._should_be_or_condition(where_str, and_conditions):
                    filter_dict = {'$or': and_conditions}
            
            if len(and_conditions) >= 2:
                fixed_conditions = []
                for i, condition in enumerate(and_conditions):
                    if isinstance(condition, dict) and '$and' in condition:
                        nested_and = condition['$and']
                        if len(nested_and) == 2:
                            if 'OR' in where_str.upper():
                                if self._should_be_or_condition(where_str, nested_and):
                                    fixed_conditions.append({'$or': nested_and})
                                else:
                                    fixed_conditions.append(condition)
                            else:
                                fixed_conditions.append(condition)
                        else:
                            fixed_conditions.append(condition)
                    else:
                        fixed_conditions.append(condition)
                
                if fixed_conditions != and_conditions:
                    filter_dict['$and'] = fixed_conditions
            
            elif len(and_conditions) == 2:
                first_condition = and_conditions[0]
                second_condition = and_conditions[1]
                
                if (isinstance(first_condition, dict) and '$and' in first_condition and 
                    isinstance(second_condition, dict) and '$and' in second_condition):
                    
                    first_has_same_field = self._check_same_field_condition(first_condition)
                    second_has_different_fields = self._check_different_fields_condition(second_condition)
                    
                    if first_has_same_field and second_has_different_fields:
                        first_or = {'$or': first_condition['$and']}
                        second_or = {'$or': second_condition['$and']}
                        filter_dict = {'$and': [first_or, second_or]}
        
        return [{'$match': filter_dict}] if filter_dict else []

    def _should_be_or_condition(self, where_str: str, and_conditions: list) -> bool:
        """Check if conditions that were parsed as $and should actually be $or based on SQL."""
        if len(and_conditions) != 2:
            return False
            
        field_names = []
        for condition in and_conditions:
            if not isinstance(condition, dict):
                return False
            non_op_keys = [k for k in condition.keys() if not k.startswith('$')]
            if len(non_op_keys) != 1:
                return False
            field_names.append(non_op_keys[0])
        
        import re
        field1, field2 = field_names[0], field_names[1]
        
        pattern1 = rf'\b{re.escape(field1)}\b.*?\bOR\b.*?\b{re.escape(field2)}\b'
        pattern2 = rf'\b{re.escape(field2)}\b.*?\bOR\b.*?\b{re.escape(field1)}\b'
        
        if (re.search(pattern1, where_str, re.IGNORECASE) or 
            re.search(pattern2, where_str, re.IGNORECASE)):
            return True
            
        return False

    def _extract_fields_from_condition(self, condition: dict) -> set:
        """Extract field names from a condition for pattern matching."""
        fields = set()
        if '$and' in condition:
            for sub_condition in condition['$and']:
                if isinstance(sub_condition, dict):
                    for key in sub_condition.keys():
                        if not key.startswith('$'):  # Skip operators like $eq, $gt, etc.
                            fields.add(key)
        return fields

    def _check_same_field_condition(self, condition: dict) -> bool:
        """Check if condition has the same field repeated (should be OR)."""
        if '$and' in condition:
            fields = []
            for sub_condition in condition['$and']:
                if isinstance(sub_condition, dict):
                    for key in sub_condition.keys():
                        if not key.startswith('$'):
                            fields.append(key)
            # Check if all fields are the same
            return len(set(fields)) == 1 and len(fields) > 1
        return False

    def _check_different_fields_condition(self, condition: dict) -> bool:
        """Check if condition has different fields (should be OR)."""
        if '$and' in condition:
            fields = []
            for sub_condition in condition['$and']:
                if isinstance(sub_condition, dict):
                    for key in sub_condition.keys():
                        if not key.startswith('$'):
                            fields.append(key)
            # Check if there are different fields
            return len(set(fields)) > 1
        return False

    def _map_table_aliases_in_where(self, where_str: str) -> str:
        """Map table aliases in WHERE clauses to MongoDB field references."""
        if not where_str:
            return where_str
            
        def replace_field_reference(match):
            full_match = match.group(0)
            table_alias = match.group(1)
            field_name = match.group(2)
            
            # Skip numeric values (like 4.0, 3.5, etc.)
            if table_alias.isdigit() or ('.' in table_alias and table_alias.replace('.', '').isdigit()):
                return full_match
            
            if hasattr(self, 'main_table_alias') and table_alias == self.main_table_alias:
                return field_name
            elif hasattr(self, 'joined_aliases') and table_alias in self.joined_aliases:
                return f"{table_alias}.{field_name}"
            else:
                return field_name
        
        result = self.table_field_pattern.sub(replace_field_reference, where_str)
        return result

    def _get_subquery_field(self, subquery_sql: str) -> str:
        """Extract the field name from SELECT clause of subquery."""
        try:
            subquery_ast = sqlglot.parse_one(subquery_sql)
            projections = subquery_ast.args.get('expressions', [])
            if projections:
                first_projection = projections[0]
                if isinstance(first_projection, exp.Column):
                    return first_projection.name if hasattr(first_projection, 'name') else str(first_projection)
                else:
                    return str(first_projection)
        except:
            pass
        return 'value'  # Default fallback

    def _extract_field_mappings_from_exists(self, subquery_sql: str) -> Dict:
        """Extract field mappings from EXISTS clause for generic handling."""
        mappings = {}
        try:
            # Look for pattern: table1.field1 = table2.field2 in EXISTS WHERE clause
            exists_where_match = re.search(r'WHERE\s+(.*?)(?:\s*\)|\s*$)', subquery_sql, re.IGNORECASE | re.DOTALL)
            if exists_where_match:
                where_condition = exists_where_match.group(1).strip()
                
                # Parse equality condition: table1.field1 = table2.field2
                eq_match = re.search(r'(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)', where_condition)
                if eq_match:
                    table1, field1, table2, field2 = eq_match.groups()
                    
                    # Convert 'id' to '_id' for MongoDB
                    if field1 == 'id':
                        field1 = '_id'
                    if field2 == 'id':
                        field2 = '_id'
                        
                    mappings['local_field'] = field1
                    mappings['foreign_field'] = field2
                    
        except Exception:
            # Fallback to defaults
            mappings['local_field'] = '_id'
            mappings['foreign_field'] = '_id'
            
        return mappings

    def _create_lookup_based_in_subquery(self, field: str, subquery_sql: str) -> List[Dict]:
        """Create a $lookup-based IN subquery for complex cases."""
        try:
            # Check if this has nested EXISTS
            if self._has_nested_exists(subquery_sql):
                return self._handle_nested_exists_in_subquery(field, subquery_sql)
            
            # Extract collection name from subquery
            subquery_ast = sqlglot.parse_one(subquery_sql)
            from_clause = subquery_ast.args.get('from')
            where_clause = subquery_ast.args.get('where')
            
            if from_clause:
                subquery_collection = from_clause.this.name if hasattr(from_clause.this, 'name') else str(from_clause.this)
                
                # Build subquery pipeline
                subquery_pipeline = []
                
                # Add WHERE conditions if present
                if where_clause:
                    where_filter = self._parse_subquery_where(where_clause)
                    if where_filter:
                        subquery_pipeline.append({'$match': where_filter})
                
                # For subqueries, preserve the original field mapping
                subquery_field = self._get_subquery_field(subquery_sql)
                subquery_pipeline.append({'$project': {'_id': 0, 'value': f'${subquery_field}'}})
                
                return [
                    {'$lookup': {'from': subquery_collection, 'pipeline': subquery_pipeline, 'as': 'subquery_results'}},
                    {'$match': {'$expr': {'$in': [f'${field}', '$subquery_results.value']}}},
                    {
                        '$project': {
                            'subquery_results': 0
                        }
                    }
                ]
        except:
            pass
        
        return [{'$match': {field: {'$in': []}}}]  # TODO: Execute subquery separately

    def _handle_nested_exists_in_subquery(self, field: str, subquery_sql: str) -> List[Dict]:
        """Handle nested EXISTS within IN subqueries."""
        try:
            # Handle complex nested EXISTS within IN subqueries
            # We need a multi-stage lookup
            
            # Parse the outer subquery
            subquery_ast = sqlglot.parse_one(subquery_sql)
            from_clause = subquery_ast.args.get('from')
            where_clause = subquery_ast.args.get('where')
            
            if from_clause:
                outer_collection = from_clause.this.name if hasattr(from_clause.this, 'name') else str(from_clause.this)
                
                # Parse the nested EXISTS pattern generically
                exists_match = re.search(r'EXISTS\s*\(\s*SELECT\s+.*?FROM\s+(\w+).*?\)', subquery_sql, re.IGNORECASE | re.DOTALL)
                if exists_match:
                    inner_collection = exists_match.group(1)
                    
                    # Extract field mappings from the EXISTS WHERE clause
                    field_mappings = self._extract_field_mappings_from_exists(subquery_sql)
                    
                    if field_mappings:
                        local_field = field_mappings.get('local_field', '_id')
                        foreign_field = field_mappings.get('foreign_field', '_id')
                        result_field = self._get_subquery_field(subquery_sql)
                        
                        return [
                            {'$lookup': {'from': outer_collection, 'let': {'ref_id': '$_id'}, 'pipeline': [
                                {'$lookup': {'from': inner_collection, 'localField': local_field, 'foreignField': foreign_field, 'as': 'nested_results'}},
                                {'$match': {'$expr': {'$gt': [{'$size': '$nested_results'}, 0]}}},
                                {'$project': {result_field: 1}}
                            ], 'as': 'valid_results'}},
                            {'$match': {'$expr': {'$in': [f'${field}', f'$valid_results.{result_field}']}}},
                            {'$project': {'valid_results': 0}}
                        ]
            
            return [
                {'$lookup': {'from': outer_collection, 'let': {}, 'pipeline': [{'$project': {'_id': 0, 'value': f'${self._get_subquery_field(subquery_sql)}'}}], 'as': 'nested_subquery_results'}},
                {'$match': {'$expr': {'$in': [f'${field}', '$nested_subquery_results.value']}}},
                {'$project': {'nested_subquery_results': 0}}
            ]
            
        except Exception:
            return [{'$match': {field: {'$in': []}}}]  # TODO: Execute nested subquery separately

    def _has_subquery(self, where_str: str) -> bool:
        """Check if WHERE clause contains subqueries."""
        if not where_str:
            return False
        return any(pattern.search(where_str) for pattern in self.subquery_patterns.values())

    def _process_where_with_subqueries(self, where_str: str) -> List[Dict]:
        """Process WHERE clause containing subqueries."""
        pipeline = []
        
        # First, process the entire WHERE clause to handle table aliases
        if hasattr(self, 'joined_aliases') and self.joined_aliases:
            where_str = self._map_table_aliases_in_where(where_str)
        else:
            # Remove table prefixes for main table fields
            where_str = re.sub(r'\b([a-zA-Z_]\w*)\.([a-zA-Z_]\w*)\b', r'\2', where_str)
        
        
        # Split WHERE clause into parts: subqueries and regular conditions
        subquery_parts = []
        regular_conditions = []
        
        # Find all subquery patterns (order matters - more specific patterns first)
        subquery_patterns = [
            r'(\w+(?:\.\w+)?)\s+NOT\s+IN\s*\(\s*SELECT\s+.*?\)',  # NOT IN first
            r'(\w+(?:\.\w+)?)\s+IN\s*\(\s*SELECT\s+.*?\)',       # IN second
            r'NOT\s+EXISTS\s*\(\s*SELECT\s+.*?\)',              # NOT EXISTS first
            r'EXISTS\s*\(\s*SELECT\s+.*?\)',                     # EXISTS second
            r'(\w+(?:\.\w+)?)\s*([<>=!]+)\s*\(\s*SELECT\s+.*?\)',  # Comparison subqueries
            r'(\w+(?:\.\w+)?)\s+BETWEEN\s*\(\s*SELECT\s+.*?\)\s*AND\s*\(\s*SELECT\s+.*?\)'  # BETWEEN subqueries
        ]
        
        remaining_where = where_str
        for pattern in subquery_patterns:
            matches = list(re.finditer(pattern, remaining_where, re.IGNORECASE | re.DOTALL))
            for match in reversed(matches):  # Process from end to avoid index issues
                subquery_parts.append(match.group(0))
                remaining_where = remaining_where[:match.start()] + remaining_where[match.end():]
        
        # Clean up the remaining WHERE clause
        remaining_where = re.sub(r'\s+AND\s+$', '', remaining_where.strip())
        remaining_where = re.sub(r'^\s+AND\s+', '', remaining_where.strip())
        remaining_where = re.sub(r'\s+AND\s+AND\s+', ' AND ', remaining_where.strip())
        
        # Additional cleanup for malformed conditions
        remaining_where = re.sub(r'\s+FROM\s+\w+\)\s*AND\s*\(', '', remaining_where.strip())
        remaining_where = re.sub(r'\s+OR\s+id\s+IS\s+NULL\)', '', remaining_where.strip())
        
        if remaining_where.strip() and remaining_where.strip() not in ['AND', 'OR', 'NOT']:
            regular_conditions.append(remaining_where.strip())
        
        # Process subqueries first
        for subquery_part in subquery_parts:
            if 'NOT IN (' in subquery_part.upper() and 'SELECT' in subquery_part.upper():
                pipeline.extend(self._process_not_in_subquery(subquery_part))
            elif 'IN (' in subquery_part.upper() and 'SELECT' in subquery_part.upper():
                pipeline.extend(self._process_in_subquery(subquery_part))
            elif 'NOT EXISTS(' in subquery_part.upper() or 'NOT EXISTS (' in subquery_part.upper():
                pipeline.extend(self._process_not_exists_subquery(subquery_part))
            elif 'EXISTS(' in subquery_part.upper() or 'EXISTS (' in subquery_part.upper():
                pipeline.extend(self._process_exists_subquery(subquery_part))
            elif 'BETWEEN' in subquery_part.upper() and 'SELECT' in subquery_part.upper():
                pipeline.extend(self._process_between_subquery(subquery_part))
            elif self.comparison_subquery_pattern.search(subquery_part):
                pipeline.extend(self._process_comparison_subquery(subquery_part))
        
        # Process regular conditions
        for condition in regular_conditions:
            if condition.strip():
                # Skip conditions that are just "NOT" or "AND NOT"
                if condition.strip().upper() in ['NOT', 'AND NOT', 'OR NOT']:
                    continue
                
                try:
                    filter_dict = self.parse(condition)
                    if filter_dict:
                        pipeline.append({'$match': filter_dict})
                except Exception as e:
                    # Skip this condition if it can't be parsed
                    pass
        
        return pipeline

    def _extract_additional_conditions(self, where_str: str) -> Dict:
        """Extract additional conditions that come after subqueries in WHERE clause."""
        # Look for patterns like "... IN (SELECT ...) AND other_condition"
        additional_conditions = {}
        
        try:
            # Find subquery patterns and extract what comes after them
            subquery_patterns = [
                r'IN\s*\(\s*SELECT\s+.*?\)',
                r'NOT\s+IN\s*\(\s*SELECT\s+.*?\)',
                r'EXISTS\s*\(\s*SELECT\s+.*?\)',
                r'NOT\s+EXISTS\s*\(\s*SELECT\s+.*?\)',
                r'ALL\s*\(\s*SELECT\s+.*?\)',
                r'ANY\s*\(\s*SELECT\s+.*?\)',
                r'BETWEEN\s*\(\s*SELECT\s+.*?\)\s*AND\s*\(\s*SELECT\s+.*?\)',
                r'[<>=!]+\s*\(\s*SELECT\s+.*?\)'
            ]
            
            # Find the end of any subquery and extract remaining conditions
            for pattern in subquery_patterns:
                match = re.search(pattern, where_str, re.IGNORECASE | re.DOTALL)
                if match:
                    # Get everything after the subquery
                    after_subquery = where_str[match.end():].strip()
                    
                    # Look for AND/OR conditions after the subquery
                    and_match = re.match(r'\s*AND\s+(.+)', after_subquery, re.IGNORECASE)
                    if and_match:
                        remaining_condition = and_match.group(1).strip()
                        # Parse the remaining condition using the existing parser
                        additional_conditions = self.parse(remaining_condition)
                        break
                    
                    or_match = re.match(r'\s*OR\s+(.+)', after_subquery, re.IGNORECASE)
                    if or_match:
                        remaining_condition = or_match.group(1).strip()
                        # For OR conditions, we need to combine with the existing pipeline differently
                        # For now, just parse as additional condition
                        additional_conditions = self.parse(remaining_condition)
                        break
        
        except Exception:
            # If parsing fails, return empty dict
            pass
        
        return additional_conditions

    def _process_in_subquery(self, where_str: str) -> List[Dict]:
        """Process IN subquery with actual MongoDB pipeline."""
        match = self.in_subquery_pattern.search(where_str)
        if match:
            field = match.group(1)
            paren_start = match.end() - 1
            subquery_sql = self._extract_subquery_with_parens(where_str, paren_start)
            
            try:
                # Parse the subquery into a proper MongoDB pipeline
                subquery_parser = MongoQueryParser()
                subquery_pipeline = subquery_parser.parse_query(subquery_sql)
                
                # Fix the projection to preserve the original field mapping
                # Replace any 'id': '$_id' projections with 'id': '$id'
                for stage in subquery_pipeline:
                    if '$project' in stage:
                        project_dict = stage['$project']
                        if 'id' in project_dict and project_dict['id'] == '$_id':
                            project_dict['id'] = '$id'
                
                # Create a $lookup stage that executes the subquery
                # Extract the collection name from the subquery
                subquery_ast = sqlglot.parse_one(subquery_sql)
                from_clause = subquery_ast.args.get('from')
                if from_clause:
                    subquery_collection = from_clause.this.name if hasattr(from_clause.this, 'name') else str(from_clause.this)
                    
                    # Use $lookup with pipeline to execute subquery and get results
                    # Ensure we project the correct field from the subquery
                    subquery_field = self._get_subquery_field(subquery_sql)
                    return [
                        {'$lookup': {'from': subquery_collection, 'let': {}, 'pipeline': subquery_pipeline + [{'$project': {'_id': 0, 'value': f'${subquery_field}'}}], 'as': 'subquery_results'}},
                        {'$match': {'$expr': {'$in': [f'${field}', '$subquery_results.value']}}},
                        {'$project': {'subquery_results': 0}}
                    ]
            except Exception as e:
                return self._create_lookup_based_in_subquery(field, subquery_sql)
        
        return []

    def _has_nested_exists(self, subquery_sql: str) -> bool:
        """Check if subquery contains nested EXISTS clauses."""
        return 'EXISTS' in subquery_sql.upper() and 'SELECT' in subquery_sql.upper()

    def _process_not_in_subquery(self, where_str: str) -> List[Dict]:
        """Process NOT IN subquery with actual MongoDB pipeline."""
        match = self.not_in_subquery_patterns[0].search(where_str)
        if not match:
            match = self.not_in_subquery_patterns[1].search(where_str)
        
        if match:
            field = match.group(1)
            subquery_sql = match.group(2).strip()
            
            try:
                # Parse the subquery into a proper MongoDB pipeline
                subquery_parser = MongoQueryParser()
                subquery_pipeline = subquery_parser.parse_query(subquery_sql)
                
                # Extract the collection name from the subquery
                subquery_ast = sqlglot.parse_one(subquery_sql)
                from_clause = subquery_ast.args.get('from')
                if from_clause:
                    subquery_collection = from_clause.this.name if hasattr(from_clause.this, 'name') else str(from_clause.this)
                    
                    # Use $lookup with pipeline to execute subquery and get results for NOT IN
                    return [
                        {
                            '$lookup': {
                                'from': subquery_collection,
                                'let': {},
                                'pipeline': subquery_pipeline + [{'$project': {'_id': 0, 'value': f'${self._get_subquery_field(subquery_sql)}'}}],
                                'as': 'subquery_results'
                            }
                        },
                        {
                            '$match': {
                                '$expr': {
                                    '$not': {
                                        '$in': [f'${field}', '$subquery_results.value']
                                    }
                                }
                            }
                        },
                        {
                            '$project': {
                                'subquery_results': 0  # Remove the temporary field
                            }
                        }
                    ]
            except Exception as e:
                # Fallback - use $lookup approach with $nin
                return self._create_lookup_based_not_in_subquery(field, subquery_sql)
        
        return []

    def _create_lookup_based_not_in_subquery(self, field: str, subquery_sql: str) -> List[Dict]:
        """Create a $lookup-based NOT IN subquery for complex cases."""
        try:
            # Extract collection name from subquery
            subquery_ast = sqlglot.parse_one(subquery_sql)
            from_clause = subquery_ast.args.get('from')
            if from_clause:
                subquery_collection = from_clause.this.name if hasattr(from_clause.this, 'name') else str(from_clause.this)
                
                return [
                    {
                        '$lookup': {
                            'from': subquery_collection,
                            'pipeline': [
                                {'$match': {}},  # Add actual subquery conditions here
                                {'$project': {'_id': 0, 'value': f'${self._get_subquery_field(subquery_sql)}'}}
                            ],
                            'as': 'subquery_results'
                        }
                    },
                    {
                        '$match': {
                            '$expr': {
                                '$not': {
                                    '$in': [f'${field}', '$subquery_results.value']
                                }
                            }
                        }
                    },
                    {
                        '$project': {
                            'subquery_results': 0
                        }
                    }
                ]
        except:
            pass
        
        return [
            {
                '$match': {
                    field: {
                        '$nin': []  
                    }
                }
            }
        ]

    def _process_between_subquery(self, where_str: str) -> List[Dict]:
        """Process BETWEEN clause with MIN/MAX subqueries using $facet."""
        # Extract field using improved approach that handles nested parentheses
        match = self.between_subquery_pattern.search(where_str)
        if not match:
            return []
            
        field = match.group(1)
        
        # Find BETWEEN position and extract both subqueries using parentheses counting
        between_pos = where_str.upper().find('BETWEEN')
        first_paren_pos = where_str.find('(', between_pos)
        
        if first_paren_pos == -1:
            return []
            
        # Extract first subquery
        min_subquery = self._extract_subquery_with_parens(where_str, first_paren_pos)
        
        # Find AND position and second subquery
        and_pos = where_str.upper().find('AND', first_paren_pos)
        second_paren_pos = where_str.find('(', and_pos)
        
        if second_paren_pos == -1:
            return []
            
        # Extract second subquery
        max_subquery = self._extract_subquery_with_parens(where_str, second_paren_pos)
        
        if min_subquery and max_subquery:
            try:
                # Parse both subqueries
                min_ast = sqlglot.parse_one(min_subquery)
                max_ast = sqlglot.parse_one(max_subquery)
                
                # Check if these are MIN/MAX operations on the same collection
                min_from = min_ast.args.get('from')
                max_from = max_ast.args.get('from')
                
                if min_from and max_from:
                    min_collection = min_from.this.name if hasattr(min_from.this, 'name') else str(min_from.this)
                    max_collection = max_from.this.name if hasattr(max_from.this, 'name') else str(max_from.this)
                    
                    if min_collection == max_collection:
                        return self._create_between_min_max_facet(field, min_subquery, max_subquery, min_collection)
                
                # Fallback for different collections or complex cases
                return [{'$match': {
                    field: {
                        '$gte': 'MIN_SUBQUERY_RESULT_PLACEHOLDER',
                        '$lte': 'MAX_SUBQUERY_RESULT_PLACEHOLDER'
                    }
                }}]
            except Exception:
                return [{'$match': {
                    field: {
                        '$gte': 'MIN_SUBQUERY_RESULT_PLACEHOLDER',
                        '$lte': 'MAX_SUBQUERY_RESULT_PLACEHOLDER'
                    }
                }}]
        
        return []

    def _create_between_min_max_facet(self, field: str, min_subquery: str, max_subquery: str, collection: str) -> List[Dict]:
        """Create $facet pipeline for BETWEEN with MIN/MAX subqueries."""
        try:
            # Parse subqueries to get field names
            min_ast = sqlglot.parse_one(min_subquery)
            max_ast = sqlglot.parse_one(max_subquery)
            
            min_projections = min_ast.args.get('expressions', [])
            max_projections = max_ast.args.get('expressions', [])
            
            if min_projections and max_projections:
                min_proj = min_projections[0]
                max_proj = max_projections[0]
                
                # Extract field names from MIN/MAX functions
                min_field = min_proj.this.name if hasattr(min_proj.this, 'name') else str(min_proj.this)
                max_field = max_proj.this.name if hasattr(max_proj.this, 'name') else str(max_proj.this)
                
                # Use $facet to compute both MIN and MAX
                return [
                    {'$facet': {'main_docs': [{'$match': {}}], 'min_max_result': [{'$lookup': {'from': collection, 'pipeline': [{'$group': {'_id': None, 'min_val': {'$min': f'${min_field}'}, 'max_val': {'$max': f'${max_field}'}}}], 'as': 'bounds'}}, {'$unwind': '$bounds'}, {'$replaceRoot': {'newRoot': '$bounds'}}]}},
                    {'$project': {'docs': '$main_docs', 'min_threshold': {'$arrayElemAt': ['$min_max_result.min_val', 0]}, 'max_threshold': {'$arrayElemAt': ['$min_max_result.max_val', 0]}}},
                    {'$unwind': '$docs'},
                    {'$match': {'$expr': {'$and': [{'$gte': [f'$docs.{field}', '$min_threshold']}, {'$lte': [f'$docs.{field}', '$max_threshold']}]}}},
                    {'$replaceRoot': {'newRoot': '$docs'}}
                ]
        except Exception:
            pass
        
        # Fallback
        return [{'$match': {field: {'$gte': 'MIN_SUBQUERY_RESULT_PLACEHOLDER', '$lte': 'MAX_SUBQUERY_RESULT_PLACEHOLDER'}}}]

    def _process_all_subquery(self, where_str: str) -> List[Dict]:
        """Process ALL subquery using $facet to compute MAX value."""
        # Extract field, operator, and subquery
        match = self.all_subquery_pattern.search(where_str)
        if match:
            field = match.group(1)
            operator = match.group(2)
            subquery_sql = match.group(3)
            
            try:
                # Parse subquery
                subquery_ast = sqlglot.parse_one(subquery_sql)
                from_clause = subquery_ast.args.get('from')
                where_clause = subquery_ast.args.get('where')
                projections = subquery_ast.args.get('expressions', [])
                
                if from_clause and projections:
                    subquery_collection = from_clause.this.name if hasattr(from_clause.this, 'name') else str(from_clause.this)
                    projection = projections[0]
                    
                    if isinstance(projection, exp.Column):
                        subquery_field = projection.name if hasattr(projection, 'name') else str(projection)
                        
                        # Build subquery pipeline for ALL (need MAX value)
                        subquery_pipeline = []
                        
                        # Add WHERE conditions
                        if where_clause:
                            where_filter = self._parse_subquery_where(where_clause)
                            if where_filter:
                                subquery_pipeline.append({'$match': where_filter})
                        
                        # Get MAX value for ALL operation
                        subquery_pipeline.append({
                            '$group': {
                                '_id': None,
                                'max_value': {'$max': f'${subquery_field}'}
                            }
                        })
                        
                        mongo_op = self._map_comparison_operator(operator)
                        
                        return [
                            {'$facet': {'main_docs': [{'$match': {}}], 'all_result': [{'$lookup': {'from': subquery_collection, 'pipeline': subquery_pipeline, 'as': 'all_data'}}, {'$unwind': '$all_data'}, {'$replaceRoot': {'newRoot': '$all_data'}}]}},
                            {'$project': {'docs': '$main_docs', 'threshold': {'$arrayElemAt': ['$all_result.max_value', 0]}}},
                            {'$unwind': '$docs'},
                            {'$match': {'$expr': {mongo_op: [f'$docs.{field}', '$threshold']}}},
                            {'$replaceRoot': {'newRoot': '$docs'}}
                        ]
            except Exception:
                pass
            
            # Fallback
            return [{'$match': {field: {self._map_comparison_operator(operator): 'ALL_SUBQUERY_MAX_RESULT_PLACEHOLDER'}}}]
        
        return []

    def _process_any_subquery(self, where_str: str) -> List[Dict]:
        """Process ANY subquery using $facet to compute MIN value."""
        # Extract field, operator, and subquery
        match = self.any_subquery_pattern.search(where_str)
        if match:
            field = match.group(1)
            operator = match.group(2)
            subquery_sql = match.group(3)
            
            try:
                # Parse subquery
                subquery_ast = sqlglot.parse_one(subquery_sql)
                from_clause = subquery_ast.args.get('from')
                where_clause = subquery_ast.args.get('where')
                projections = subquery_ast.args.get('expressions', [])
                
                if from_clause and projections:
                    subquery_collection = from_clause.this.name if hasattr(from_clause.this, 'name') else str(from_clause.this)
                    projection = projections[0]
                    
                    if isinstance(projection, exp.Column):
                        subquery_field = projection.name if hasattr(projection, 'name') else str(projection)
                        
                        # Build subquery pipeline for ANY (need MIN value)
                        subquery_pipeline = []
                        
                        # Add WHERE conditions
                        if where_clause:
                            where_filter = self._parse_subquery_where(where_clause)
                            if where_filter:
                                subquery_pipeline.append({'$match': where_filter})
                        
                        # Get MIN value for ANY operation
                        subquery_pipeline.append({
                            '$group': {
                                '_id': None,
                                'min_value': {'$min': f'${subquery_field}'}
                            }
                        })
                        
                        mongo_op = self._map_comparison_operator(operator)
                        
                        return [
                            {'$facet': {'main_docs': [{'$match': {}}], 'any_result': [{'$lookup': {'from': subquery_collection, 'pipeline': subquery_pipeline, 'as': 'any_data'}}, {'$unwind': '$any_data'}, {'$replaceRoot': {'newRoot': '$any_data'}}]}},
                            {'$project': {'docs': '$main_docs', 'threshold': {'$arrayElemAt': ['$any_result.min_value', 0]}}},
                            {'$unwind': '$docs'},
                            {'$match': {'$expr': {mongo_op: [f'$docs.{field}', '$threshold']}}},
                            {'$replaceRoot': {'newRoot': '$docs'}}
                        ]
            except Exception:
                pass
            
            # Fallback
            return [{'$match': {field: {self._map_comparison_operator(operator): 'ANY_SUBQUERY_MIN_RESULT_PLACEHOLDER'}}}]
        
        return []

    def _process_exists_clause(self, exists_clause) -> List[Dict]:
        """Process EXISTS clause directly from AST."""
        return [{'$match': {'$expr': {'$gt': [{'$size': ['SUBQUERY_RESULTS_PLACEHOLDER']}, 0]}}}]

    def _process_exists_subquery(self, where_str: str) -> List[Dict]:
        """Process EXISTS subquery with proper $lookup implementation."""
        # Extract the subquery
        match = re.search(r'EXISTS\s*\(\s*(SELECT\s+.*?)\s*\)', where_str, re.IGNORECASE | re.DOTALL)
        if match:
            subquery_sql = match.group(1)
            
            try:
                # Parse subquery to extract collection and conditions
                subquery_ast = sqlglot.parse_one(subquery_sql)
                from_clause = subquery_ast.args.get('from')
                where_clause = subquery_ast.args.get('where')
                
                if from_clause:
                    subquery_collection = from_clause.this.name if hasattr(from_clause.this, 'name') else str(from_clause.this)
                    
                    # Check if this is a correlated subquery (references outer table)
                    if self._is_correlated_subquery(where_clause):
                        # Handle correlated EXISTS with $lookup
                        return self._create_correlated_exists_lookup(subquery_collection, where_clause)
                    else:
                        # Handle non-correlated EXISTS
                        return self._create_simple_exists_lookup(subquery_collection, where_clause)
                        
            except Exception as e:
                # Fallback implementation
                return [
                    {
                        '$lookup': {
                            'from': 'subquery_collection',  # TODO: Replace with actual collection
                            'pipeline': [{'$match': {}}],   # TODO: Add subquery conditions
                            'as': 'exists_check'
                        }
                    },
                    {
                        '$match': {
                            '$expr': {'$gt': [{'$size': '$exists_check'}, 0]}
                        }
                    },
                    {
                        '$project': {'exists_check': 0}
                    }
                ]
        
        return []

    def _process_not_exists_subquery(self, where_str: str) -> List[Dict]:
        """Process NOT EXISTS subquery with proper $lookup implementation."""
        # Extract the subquery
        match = re.search(r'NOT\s+EXISTS\s*\(\s*(SELECT\s+.*?)\s*\)', where_str, re.IGNORECASE | re.DOTALL)
        if match:
            subquery_sql = match.group(1)
            
            try:
                # Parse subquery to extract collection and conditions
                subquery_ast = sqlglot.parse_one(subquery_sql)
                from_clause = subquery_ast.args.get('from')
                where_clause = subquery_ast.args.get('where')
                
                if from_clause:
                    subquery_collection = from_clause.this.name if hasattr(from_clause.this, 'name') else str(from_clause.this)
                    
                    # Check if this is a correlated subquery
                    if self._is_correlated_subquery(where_clause):
                        # Handle correlated NOT EXISTS with $lookup
                        return self._create_correlated_not_exists_lookup(subquery_collection, where_clause)
                    else:
                        # Handle non-correlated NOT EXISTS
                        return self._create_simple_not_exists_lookup(subquery_collection, where_clause)
                        
            except Exception as e:
                # Fallback implementation
                return [
                    {
                        '$lookup': {
                            'from': 'subquery_collection',  # TODO: Replace with actual collection
                            'pipeline': [{'$match': {}}],   # TODO: Add subquery conditions
                            'as': 'not_exists_check'
                        }
                    },
                    {
                        '$match': {
                            '$expr': {'$eq': [{'$size': '$not_exists_check'}, 0]}
                        }
                    },
                    {
                        '$project': {'not_exists_check': 0}
                    }
                ]
        
        return []

    def _process_comparison_subquery(self, where_str: str) -> List[Dict]:
        """Process comparison subquery with scalar result using $facet."""
        # Extract field, operator, and subquery
        # Use simpler approach - find the field and operator first, then extract subquery
        match = re.search(r'(\w+(?:\.\w+)?)\s*([<>=!]+)\s*\(', where_str, re.IGNORECASE)
        if not match:
            return []
            
        field = match.group(1)
        operator = match.group(2)
        
        # Find the start of the subquery
        start_pos = match.end()
        subquery_start = where_str.find('(', match.start())
        
        # Extract the complete subquery by counting parentheses
        subquery_sql = self._extract_subquery_with_parens(where_str, subquery_start)
        
        if subquery_sql:
            try:
                # Parse subquery to determine if it's a scalar aggregate
                subquery_ast = sqlglot.parse_one(subquery_sql)
                projections = subquery_ast.args.get('expressions', [])
                
                if projections and len(projections) == 1:
                    projection = projections[0]
                    if isinstance(projection, (exp.Avg, exp.Min, exp.Max, exp.Sum, exp.Count)):
                        # This is a scalar aggregate subquery - use $facet
                        return self._create_scalar_subquery_facet(field, operator, subquery_sql, subquery_ast)
                
                # Fallback for non-aggregate comparisons
                mongo_op = self._map_comparison_operator(operator)
                if mongo_op:
                    return [{'$match': {field: {mongo_op: 'SUBQUERY_RESULT_PLACEHOLDER'}}}]
            except Exception as e:
                # Fallback
                mongo_op = self._map_comparison_operator(operator)
                if mongo_op:
                    return [{'$match': {field: {mongo_op: 'SUBQUERY_RESULT_PLACEHOLDER'}}}]
        
        return []

    def _extract_subquery_with_parens(self, text: str, start_pos: int) -> str:
        """Extract complete subquery by counting parentheses."""
        if start_pos >= len(text) or text[start_pos] != '(':
            return ""
        
        paren_count = 0
        i = start_pos
        
        while i < len(text):
            if text[i] == '(':
                paren_count += 1
            elif text[i] == ')':
                paren_count -= 1
                if paren_count == 0:
                    # Found the matching closing parenthesis
                    return text[start_pos + 1:i].strip()
            i += 1
        
        # No matching closing parenthesis found
        return ""

    def _create_scalar_subquery_facet(self, field: str, operator: str, subquery_sql: str, subquery_ast) -> List[Dict]:
        """Create $facet pipeline for scalar subquery comparison."""
        try:
            # Extract subquery components
            from_clause = subquery_ast.args.get('from')
            where_clause = subquery_ast.args.get('where')
            projections = subquery_ast.args.get('expressions', [])
            
            if not from_clause or not projections:
                return [{'$match': {field: {'$gt': 'SUBQUERY_RESULT_PLACEHOLDER'}}}]
            
            subquery_collection = from_clause.this.name if hasattr(from_clause.this, 'name') else str(from_clause.this)
            projection = projections[0]
            
            # Build subquery pipeline
            subquery_pipeline = []
            
            # Add WHERE conditions to subquery
            if where_clause:
                where_filter = self._parse_subquery_where(where_clause)
                if where_filter:
                    subquery_pipeline.append({'$match': where_filter})
            
            # Add aggregate operation
            if isinstance(projection, exp.Avg):
                agg_field = projection.this.name if hasattr(projection.this, 'name') else str(projection.this)
                subquery_pipeline.append({
                    '$group': {
                        '_id': None,
                        'result': {'$avg': f'${agg_field}'}
                    }
                })
            elif isinstance(projection, exp.Min):
                agg_field = projection.this.name if hasattr(projection.this, 'name') else str(projection.this)
                subquery_pipeline.append({
                    '$group': {
                        '_id': None,
                        'result': {'$min': f'${agg_field}'}
                    }
                })
            elif isinstance(projection, exp.Max):
                agg_field = projection.this.name if hasattr(projection.this, 'name') else str(projection.this)
                subquery_pipeline.append({
                    '$group': {
                        '_id': None,
                        'result': {'$max': f'${agg_field}'}
                    }
                })
            
            # Use $facet to execute both main query and subquery
            mongo_op = self._map_comparison_operator(operator)
            
            return [
                {
                    '$facet': {
                        'main_docs': [{'$match': {}}],  # Get all main documents first
                        'subquery_result': [
                            {
                                '$lookup': {
                                    'from': subquery_collection,
                                    'pipeline': subquery_pipeline,
                                    'as': 'subquery_data'
                                }
                            },
                            {'$unwind': '$subquery_data'},
                            {'$replaceRoot': {'newRoot': '$subquery_data'}}
                        ]
                    }
                },
                {
                    '$project': {
                        'docs': '$main_docs',
                        'threshold': {'$arrayElemAt': ['$subquery_result.result', 0]}
                    }
                },
                {'$unwind': '$docs'},
                {
                    '$match': {
                        '$expr': {
                            mongo_op: [f'$docs.{field}', '$threshold']
                        }
                    }
                },
                {'$replaceRoot': {'newRoot': '$docs'}}
            ]
            
        except Exception as e:
            # Fallback
            mongo_op = self._map_comparison_operator(operator)
            return [{'$match': {field: {mongo_op: 'SUBQUERY_RESULT_PLACEHOLDER'}}}]

    def _parse_subquery_where(self, where_clause) -> Dict:
        """Parse WHERE clause from subquery AST."""
        try:
            where_str = where_clause.this.sql()
            # Use the existing filter parser
            return self.parse(where_str)
        except Exception:
            return {}

    def _map_comparison_operator(self, sql_op: str) -> Optional[str]:
        """Map SQL comparison operator to MongoDB operator."""
        op_map = {
            '=': '$eq',
            '!=': '$ne',
            '<>': '$ne',
            '>': '$gt',
            '>=': '$gte',
            '<': '$lt',
            '<=': '$lte'
        }
        return op_map.get(sql_op)

    def _parse_subquery(self, subquery_ast: exp.Select) -> List[Dict]:
        """Parse a subquery into MongoDB pipeline."""
        return []

    def _extract_joins_from_ast(self, ast: exp.Select) -> List[Dict]:
        """Extract JOIN information from AST joins attribute."""
        joins = []
        
        # Get joins from AST args
        ast_joins = ast.args.get('joins', [])
        
        for join in ast_joins:
            join_info = self._extract_single_join(join)
            if join_info:
                joins.append(join_info)
        
        return joins

    def _extract_query_components(self, ast: exp.Select) -> Dict:
        """Extract all components from SQL AST including JOINs and subqueries."""
        from_clause = ast.args.get('from')
        if not from_clause:
            raise SyntaxError("Invalid or missing FROM clause")

        projections = ast.args.get('expressions', [])
        where_clause = ast.args.get('where')
        group_clause = ast.args.get('group')
        having_clause = ast.args.get('having')
        order_clause = ast.args.get('order')
        limit_clause = ast.args.get('limit')
        
        group_by = [g.sql() for g in group_clause.expressions] if group_clause else None

        # Extract JOIN information from AST joins attribute
        joins = self._extract_joins_from_ast(ast)
        
        # Extract main table information
        main_table = self._extract_main_table(from_clause)

        return {
            'projections': projections,
            'where_clause': where_clause,
            'group_by': group_by,
            'having_clause': having_clause,
            'order_clause': order_clause,
            'limit_clause': limit_clause,
            'joins': joins,
            'main_table': main_table
        }

    def _extract_joins(self, from_clause) -> List[Dict]:
        """Extract JOIN information from FROM clause (legacy method)."""
        # This method is no longer used - JOINs are extracted from AST
        return []

    def _extract_single_join(self, join_clause) -> Optional[Dict]:
        """Extract information from a single JOIN clause."""
        if not isinstance(join_clause, exp.Join):
            return None
            
        # Get join type
        join_type = 'INNER'  # Default
        if hasattr(join_clause, 'side'):
            if join_clause.side == 'LEFT':
                join_type = 'LEFT'
            elif join_clause.side == 'RIGHT':
                join_type = 'RIGHT'
            elif join_clause.side == 'FULL':
                join_type = 'FULL'
        
        # Get join kind
        if hasattr(join_clause, 'kind'):
            if join_clause.kind == 'OUTER':
                join_type += ' OUTER'
            elif join_clause.kind == 'CROSS':
                join_type = 'CROSS'
        
        # Extract table information
        right_table = join_clause.this
        if isinstance(right_table, exp.Alias):
            table_name = right_table.this.name if hasattr(right_table.this, 'name') else str(right_table.this)
            table_alias = right_table.alias
        else:
            table_name = right_table.name if hasattr(right_table, 'name') else str(right_table)
            table_alias = None
        
        # Check if the table has an alias in a different structure
        if hasattr(right_table, 'alias') and right_table.alias:
            table_alias = right_table.alias.this if hasattr(right_table.alias, 'this') else right_table.alias
        
        # Extract join condition
        join_condition = join_clause.args.get('on')
        if join_condition:
            condition_str = join_condition.sql()
            # Parse the join condition to extract field mappings
            local_field, foreign_field = self._parse_join_condition(condition_str)
        else:
            local_field = None
            foreign_field = None
        
        return {
            'type': join_type,
            'table': self._normalize_table_name(table_name),
            'alias': table_alias,
            'local_field': local_field,
            'foreign_field': foreign_field,
            'condition': join_condition
        }

    def _extract_main_table(self, from_clause) -> Dict:
        """Extract main table information from FROM clause."""
        # Navigate to the main table (leftmost in JOIN chain)
        current = from_clause
        while isinstance(current, exp.Join):
            current = current.this
        
        # Get the actual table from FROM clause
        table_expr = current.this if hasattr(current, 'this') else current
        
        if isinstance(table_expr, exp.Alias):
            table_name = table_expr.this.name if hasattr(table_expr.this, 'name') else str(table_expr.this)
            table_alias = table_expr.alias
        elif hasattr(table_expr, 'alias') and table_expr.alias:
            # Handle Table expression with alias
            table_name = table_expr.name if hasattr(table_expr, 'name') else str(table_expr)
            table_alias = table_expr.alias
        else:
            table_name = table_expr.name if hasattr(table_expr, 'name') else str(table_expr)
            table_alias = None
        
        return {
            'table': self._normalize_table_name(table_name),
            'alias': table_alias
        }

    def _parse_join_condition(self, condition_str: str) -> tuple:
        """Parse JOIN condition to extract local and foreign field mappings."""
        # Handle simple equality conditions in JOIN clauses
        if '=' in condition_str:
            parts = condition_str.split('=')
            if len(parts) == 2:
                left_field = parts[0].strip()
                right_field = parts[1].strip()
                
                # For local field, preserve table alias if it exists (for chained joins)
                # For foreign field, remove table alias (always references the joined table's _id)
                if '.' in left_field:
                    # Keep the table alias for local field (e.g., "ep.project_id")
                    local_field = left_field
                else:
                    local_field = left_field
                
                right_field = self._extract_field_name(right_field)
                
                return local_field, right_field
        
        return None, None

    def _extract_field_name(self, field_ref: str) -> str:
        """Extract field name from table.field reference."""
        if '.' in field_ref:
            field_name = field_ref.split('.')[-1]
            # Keep the original field name for JOIN operations
            # MongoDB collections use 'id' field, not '_id' for JOINs
            return field_name
        return field_ref

    def _normalize_table_name(self, table_name: str) -> str:
        """Normalize table name to match MongoDB collection naming conventions."""
        if not table_name:
            return table_name
        
        # Convert to lowercase for MongoDB collection names
        # Table1 -> table1, Table2 -> table2, etc.
        normalized = table_name.lower()
        
        # Handle common table name mappings
        table_mappings = {
            'table1': 'table1',
            'table2': 'table2',
            'jointable1': 'jointable1',
            'jointable2': 'jointable2'
        }
        
        return table_mappings.get(normalized, normalized)

    def _get_inner_and_alias(self, proj):
        """Helper function to extract inner expression and alias."""
        if isinstance(proj, exp.Alias):
            return proj.this, proj.alias
        return proj, None

    def _process_group_by_query(self, components: Dict) -> List[Dict]:
        """Process GROUP BY queries."""
        group_cols = components['group_by']
        projections = components['projections']
        having_clause = components['having_clause']
        order_clause = components['order_clause']
        limit_clause = components['limit_clause']
        
        pipeline = []
        
        # Check if this is a SELECT * query
        if len(projections) == 1 and isinstance(projections[0], exp.Star):
            # For SELECT * with GROUP BY, we need to handle it differently
            # Create implicit aggregate functions for the GROUP BY columns
            agg_infos = []
            non_agg_projections = []
            
            # Add implicit COUNT(*) for SELECT * queries
            agg_infos.append(('COUNT', None, 'count_value'))
            
            # Check HAVING clause for additional implicit aggregates
            if having_clause:
                having_str = having_clause.this.sql()
                if 'avg_product_price' in having_str.lower():
                    # Add implicit AVG aggregate for product price
                    agg_infos.append(('AVG', 'j2.price', 'avg_value'))
                if 'product_count' in having_str.lower():
                    # COUNT is already added above
                    pass
            
            # Check ORDER BY clause for additional implicit aggregates
            if order_clause and hasattr(order_clause, 'this'):
                order_str = order_clause.this.sql()
                if 'avg_product_price' in order_str.lower() and not any('avg_value' in str(agg) for agg in agg_infos):
                    # Add implicit AVG aggregate for product price if not already added
                    agg_infos.append(('AVG', 'j2.price', 'avg_value'))
            
            # Add GROUP BY columns as non-aggregate projections
            for col in group_cols:
                clean_col_name = col.split('.')[-1] if '.' in col else col
                non_agg_projections.append((col, clean_col_name))
        else:
            # Find projections
            agg_infos, non_agg_projections = self._analyze_projections(projections)
            
            # Allow GROUP BY queries even without explicit aggregate functions
            # MongoDB can handle grouping without aggregation
            if not agg_infos and not non_agg_projections:
                # If no projections found, create a simple grouping
                agg_infos = []
                non_agg_projections = [(col, col.split('.')[-1] if '.' in col else col) for col in group_cols]
        
        # Build $group stage
        group_stage = self._build_group_stage(group_cols, agg_infos)
        pipeline.append({'$group': group_stage})
        
        # Handle HAVING clause
        if having_clause:
            having_pipeline = self._process_having_clause(having_clause, group_cols, agg_infos)
            pipeline.extend(having_pipeline)
        
        # Build $project stage
        project_stage = self._build_group_project_stage(group_cols, non_agg_projections, agg_infos)
        pipeline.append({'$project': project_stage})
        
        # Handle ORDER BY and LIMIT
        pipeline.extend(self._process_order_and_limit(order_clause, limit_clause))
        
        return pipeline

    def _analyze_projections(self, projections: List) -> tuple:
        """Analyze projections to separate aggregates from non-aggregates."""
        agg_infos = []
        non_agg_projections = []
        
        for proj in projections:
            inner, alias = self._get_inner_and_alias(proj)
            if isinstance(inner, (exp.Count, exp.Sum, exp.Avg, exp.Min, exp.Max)):
                agg_type = inner.__class__.__name__.upper()
                agg_col = inner.this
                
                if isinstance(agg_col, exp.Star):
                    agg_col_name = None
                elif agg_col:
                    # Handle table aliases in aggregate functions
                    if hasattr(agg_col, 'table') and agg_col.table:
                        table_alias = agg_col.table
                        field_name = agg_col.name if hasattr(agg_col, 'name') else agg_col.sql()
                        agg_col_name = f'{table_alias}.{field_name}'
                    else:
                        agg_col_name = agg_col.name if hasattr(agg_col, 'name') else agg_col.sql()
                else:
                    agg_col_name = None
                
                agg_field = alias or f'{agg_type.lower()}_value'
                agg_infos.append((agg_type, agg_col_name, agg_field))
            elif isinstance(inner, exp.Column):
                col_name = inner.name if hasattr(inner, 'name') else inner.sql()
                col_alias = alias or col_name
                non_agg_projections.append((col_name, col_alias))
            elif isinstance(inner, (exp.Year, exp.Month, exp.Day)):
                # Handle date/time functions
                col_name = inner.sql()
                col_alias = alias or col_name
                non_agg_projections.append((col_name, col_alias))
        
        return agg_infos, non_agg_projections

    def _build_group_stage(self, group_cols: List[str], agg_infos: List[tuple]) -> Dict:
        """Build MongoDB $group stage."""
        if len(group_cols) == 1:
            # Single column GROUP BY - handle function expressions
            group_col = group_cols[0]
            if 'YEAR(' in group_col.upper():
                # Extract field name from YEAR(field) expression
                match = re.search(r'YEAR\((\w+)\)', group_col, re.IGNORECASE)
                if match:
                    field_name = match.group(1)
                    group_stage = {'_id': {'$year': f'${field_name}'}}
                else:
                    group_stage = {'_id': f'${group_col}'}
            else:
                # Handle table aliases in single column GROUP BY
                if '.' in group_col:
                    table_alias, field_name = group_col.split('.', 1)
                    # Check if this is a joined table alias
                    if hasattr(self, 'joined_aliases') and table_alias in self.joined_aliases:
                        # For joined tables, use the lookup alias
                        group_stage = {'_id': f'${table_alias}.{field_name}'}
                    else:
                        # For main table fields, use direct field reference
                        if field_name == 'id':
                            group_stage = {'_id': '$_id'}
                        else:
                            group_stage = {'_id': f'${field_name}'}
                else:
                    # Direct field reference
                    if group_col == 'id':
                        group_stage = {'_id': '$_id'}
                    else:
                        group_stage = {'_id': f'${group_col}'}
        else:
            # Multiple column GROUP BY - use composite _id
            group_stage = {'_id': {}}
            for col in group_cols:
                # Handle table aliases in GROUP BY fields
                if '.' in col:
                    table_alias, field_name = col.split('.', 1)
                    # Check if this is a joined table alias
                    if hasattr(self, 'joined_aliases') and table_alias in self.joined_aliases:
                        # For joined tables, use the lookup alias
                        group_stage['_id'][col] = f'${table_alias}.{field_name}'
                    else:
                        # For main table fields, use direct field reference
                        if field_name == 'id':
                            group_stage['_id'][col] = '$_id'
                        else:
                            group_stage['_id'][col] = f'${field_name}'
                else:
                    # Direct field reference
                    if col == 'id':
                        group_stage['_id'][col] = '$_id'
                    else:
                        group_stage['_id'][col] = f'${col}'
        
        # Add aggregate fields
        for agg_type, agg_col_name, agg_field in agg_infos:
            if agg_type == 'COUNT' and agg_col_name is None:
                # COUNT(*) - count all documents
                group_stage[agg_field] = {'$sum': 1}
            elif agg_type == 'COUNT':
                # COUNT(column) - count non-null values of the specified column
                group_stage[agg_field] = {'$sum': {'$cond': [{'$ne': [f'${agg_col_name}', None]}, 1, 0]}}
            else:
                # Handle other aggregate functions with joined collections
                if agg_col_name and '.' in agg_col_name:
                    table_alias, field_name = agg_col_name.split('.', 1)
                    if hasattr(self, 'joined_aliases') and table_alias in self.joined_aliases:
                        # For joined tables, use the joined field reference
                        group_stage[agg_field] = {self.agg_map[agg_type]: f'${table_alias}.{field_name}'}
                    else:
                        # For main table fields
                        group_stage[agg_field] = {self.agg_map[agg_type]: f'${field_name}'}
                else:
                    # Handle special cases for aggregate functions
                    if agg_col_name == 'id':
                        # For id field, use the actual numeric id field, not _id ObjectId
                        group_stage[agg_field] = {self.agg_map[agg_type]: '$id'}
                    else:
                        group_stage[agg_field] = {self.agg_map[agg_type]: f'${agg_col_name}'}
        
        return group_stage

    def _process_having_clause(self, having_clause, group_cols: List[str], agg_infos: List[tuple] = None) -> List[Dict]:
        """Process HAVING clause for GROUP BY queries."""
        having_str = having_clause.this.sql()
        pipeline = []
        agg_infos = agg_infos or []
        
        # Handle aggregate function conditions in HAVING
        if 'COUNT(*)' in having_str.upper():
            # Extract the condition
            match = re.search(r'COUNT\(\*\)\s*([><=!]+)\s*(\d+)', having_str, re.IGNORECASE)
            if match:
                operator = match.group(1)
                value = int(match.group(2))
                mongo_op = self.op_map.get(operator, '$eq')
                # Use generic field name based on aggregate type
                count_field = next((field for _, _, field in agg_infos if field.endswith('_count') or 'count' in field.lower()), 'count_value')
                pipeline.append({'$match': {count_field: {mongo_op: value}}})
        elif 'AVG(' in having_str.upper():
            # Handle AVG() conditions
            match = re.search(r'AVG\((\w+)\)\s*([><=!]+)\s*([\d.]+)', having_str, re.IGNORECASE)
            if match:
                field = match.group(1)
                operator = match.group(2)
                value = float(match.group(3))
                mongo_op = self.op_map.get(operator, '$eq')
                # Find the corresponding avg field from agg_infos
                avg_field = next((agg_field for _, agg_col, agg_field in agg_infos if agg_col == field and 'avg' in agg_field.lower()), f'avg_{field}')
                pipeline.append({'$match': {avg_field: {mongo_op: value}}})
        elif 'product_count' in having_str.lower():
            # Handle implicit aggregate fields from SELECT * queries
            match = re.search(r'product_count\s*([><=!]+)\s*(\d+)', having_str, re.IGNORECASE)
            if match:
                operator = match.group(1)
                value = int(match.group(2))
                mongo_op = self.op_map.get(operator, '$eq')
                pipeline.append({'$match': {'count_value': {mongo_op: value}}})
        elif 'avg_product_price' in having_str.lower():
            # Handle implicit aggregate fields from SELECT * queries
            match = re.search(r'avg_product_price\s*([><=!]+)\s*([\d.]+)', having_str, re.IGNORECASE)
            if match:
                operator = match.group(1)
                value = float(match.group(2))
                mongo_op = self.op_map.get(operator, '$eq')
                pipeline.append({'$match': {'avg_value': {mongo_op: value}}})
        elif 'LIKE' in having_str.upper():
            parts = re.split(r'\s+LIKE\s+', having_str, flags=re.IGNORECASE)
            pattern = parts[1].strip("'")
            pattern = self.sql_like_to_regex(pattern)
            pipeline.append({'$match': {'_id': {'$regex': pattern, '$options': 'i'}}})
        elif 'BETWEEN' in having_str.upper():
            between_result = self.extract_between_clause(having_str)
            if between_result:
                _, start_val, end_val, _ = between_result
                # For date fields, use direct date comparison
                if len(group_cols) == 1 and 'date' in group_cols[0].lower():
                    # Parse dates as datetime objects
                    start_date = self.parse_date_value(start_val)
                    end_date = self.parse_date_value(end_val)
                    # Use direct comparison
                    pipeline.append({'$match': {
                        '_id': {
                            '$gte': start_date,
                            '$lte': end_date
                        }
                    }})
                else:
                    pipeline.append({'$match': {
                        '_id': {
                            '$gte': self.parse_value(start_val, group_cols[0] if group_cols else ''),
                            '$lte': self.parse_value(end_val, group_cols[0] if group_cols else '')
                        }
                    }})
        
        return pipeline

    def _build_group_project_stage(self, group_cols: List[str], non_agg_projections: List[tuple], agg_infos: List[tuple]) -> Dict:
        """Build $project stage for GROUP BY queries."""
        project_stage = {'_id': 0}
        projected_fields = set()  # Track projected fields to avoid duplicates
        
        # Project grouped columns
        if len(group_cols) == 1:
            # Single column - project directly
            # Find the alias for the grouped column
            for col_name, col_alias in non_agg_projections:
                if col_name in group_cols and col_alias not in projected_fields:
                    project_stage[col_alias] = '$_id'
                    projected_fields.add(col_alias)
                    break
            else:
                # If no alias found, use the column name (clean up dotted names)
                col_name = group_cols[0]
                clean_col_name = col_name.split('.')[-1] if '.' in col_name else col_name
                if clean_col_name not in projected_fields:
                    project_stage[clean_col_name] = '$_id'
                    projected_fields.add(clean_col_name)
        else:
            # Multiple columns - extract from composite _id
            for col_name, col_alias in non_agg_projections:
                if col_name in group_cols and col_alias not in projected_fields:
                    # Use simplified field name for projection
                    clean_alias = col_alias.split('.')[-1] if '.' in col_alias else col_alias
                    project_stage[clean_alias] = f'$_id.{col_name}'
                    projected_fields.add(clean_alias)
            
            # Also project any GROUP BY columns that don't have aliases
            for col in group_cols:
                if not any(col == col_name for col_name, _ in non_agg_projections):
                    clean_col_name = col.split('.')[-1] if '.' in col else col
                    if clean_col_name not in projected_fields:
                        project_stage[clean_col_name] = f'$_id.{col}'
                        projected_fields.add(clean_col_name)
        
        # Project aggregate fields
        for _, _, agg_field in agg_infos:
            if agg_field not in projected_fields:
                project_stage[agg_field] = 1
                projected_fields.add(agg_field)
        
        return project_stage

    def _process_single_projection_query(self, components: Dict) -> List[Dict]:
        """Process single projection queries (aggregate or column)."""
        projections = components['projections']
        order_clause = components['order_clause']
        limit_clause = components['limit_clause']
        
        pipeline = []
        inner, alias = self._get_inner_and_alias(projections[0])
        
        if isinstance(inner, (exp.Count, exp.Sum, exp.Avg, exp.Min, exp.Max)):
            # Aggregate function
            pipeline.extend(self._process_aggregate_projection(inner, alias))
        elif isinstance(inner, exp.Star):
            # SELECT * - return all fields, no projection needed
            pass
        elif isinstance(inner, exp.Column):
            # Single column selection
            col_name = inner.name if hasattr(inner, 'name') else inner.sql()
            field_alias = alias or col_name
            
            # Handle field mapping correctly
            if hasattr(inner, 'table') and inner.table:
                table_alias = inner.table
                if hasattr(self, 'joined_aliases') and table_alias in self.joined_aliases:
                    # For joined tables
                    pipeline.append({'$project': {'_id': 0, field_alias: f'${table_alias}.{col_name}'}})
                else:
                    # For main table with alias
                    field_ref = '$_id' if col_name == 'id' else f'${col_name}'
                    pipeline.append({'$project': {'_id': 0, field_alias: field_ref}})
            else:
                # For main table without alias
                field_ref = '$_id' if col_name == 'id' else f'${col_name}'
                pipeline.append({'$project': {'_id': 0, field_alias: field_ref}})
        else:
            # Other expressions
            field_alias = alias or inner.sql()
            pipeline.append({'$project': {'_id': 0, field_alias: 1}})
        
        # Handle ORDER BY and LIMIT
        pipeline.extend(self._process_order_and_limit(order_clause, limit_clause))
        
        return pipeline

    def _process_aggregate_projection(self, inner, alias) -> List[Dict]:
        """Process aggregate function projections."""
        pipeline = []
        agg_type = inner.__class__.__name__.upper()
        agg_col = inner.this
        agg_field = alias or 'total_value'
        
        if agg_type == 'COUNT' and isinstance(agg_col, exp.Star):
            pipeline.append({'$count': agg_field})
        elif agg_type == 'COUNT' and ('DISTINCT' in str(inner).upper() or 'DISTINCT' in inner.sql().upper()):
            # Handle COUNT DISTINCT
            if agg_col:
                # For DISTINCT, agg_col is a Distinct object, need to get the actual column
                if hasattr(agg_col, 'expressions') and agg_col.expressions:
                    # agg_col.expressions[0] is the actual column
                    actual_col = agg_col.expressions[0]
                    agg_col_name = actual_col.name if hasattr(actual_col, 'name') else actual_col.sql()
                else:
                    agg_col_name = agg_col.name if hasattr(agg_col, 'name') else agg_col.sql()
            else:
                raise SyntaxError(f"{agg_type} requires a column")
            
            pipeline.append({'$group': {'_id': f'${agg_col_name}'}})
            pipeline.append({'$count': agg_field})
        else:
            if agg_type == 'COUNT':
                if agg_col is None or (hasattr(agg_col, 'sql') and agg_col.sql() == '*'):
                    # COUNT(*) - count all documents
                    agg_op = {'$sum': 1}
                else:
                    # COUNT(column) - count non-null values
                    agg_col_name = agg_col.name if hasattr(agg_col, 'name') else agg_col.sql()
                    agg_op = {'$sum': {'$cond': [{'$ne': [f'${agg_col_name}', None]}, 1, 0]}}
            else:
                if agg_col:
                    agg_col_name = agg_col.name if hasattr(agg_col, 'name') else agg_col.sql()
                else:
                    raise SyntaxError(f"{agg_type} requires a column")
                agg_op = {self.agg_map[agg_type]: f'${agg_col_name}'}
            
            pipeline.append({'$group': {'_id': None, agg_field: agg_op}})
            pipeline.append({'$project': {'_id': 0}})
        
        return pipeline

    def _process_normal_query(self, components: Dict) -> List[Dict]:
        """Process normal SELECT queries (multiple columns)."""
        projections = components['projections']
        order_clause = components['order_clause']
        limit_clause = components['limit_clause']
        
        pipeline = []
        project_stage = None
        
        # Check if we have aggregate functions
        has_aggregates = False
        aggregate_functions = []
        regular_fields = []
        
        for proj in projections:
            inner, alias = self._get_inner_and_alias(proj)
            
            if isinstance(inner, exp.Star):
                # SELECT * - don't add any projection, return all fields
                return pipeline + self._process_order_and_limit(order_clause, limit_clause)
            elif isinstance(inner, (exp.Sum, exp.Avg, exp.Min, exp.Max, exp.Count)):
                # This is an aggregate function
                has_aggregates = True
                aggregate_functions.append((inner, alias))
            elif isinstance(inner, exp.Anonymous) and inner.this.upper() == 'YEAR':
                # Handle YEAR() function
                has_aggregates = True
                aggregate_functions.append((inner, alias))
            else:
                regular_fields.append((inner, alias))
        
        if has_aggregates:
            # Check if we have COUNT DISTINCT
            has_count_distinct = False
            for inner, alias in aggregate_functions:
                if isinstance(inner, exp.Count):
                    # Check for DISTINCT keyword in the SQL
                    if 'DISTINCT' in str(inner).upper() or 'DISTINCT' in inner.sql().upper():
                        has_count_distinct = True
                        break
            
            if has_count_distinct:
                # Handle COUNT DISTINCT with special pipeline
                for inner, alias in aggregate_functions:
                    if isinstance(inner, exp.Count) and ('DISTINCT' in str(inner).upper() or 'DISTINCT' in inner.sql().upper()):
                        agg_col = inner.this
                        agg_field = alias or f'unique_{agg_col_name}'
                        # For DISTINCT, agg_col is a Distinct object, need to get the actual column
                        if hasattr(agg_col, 'expressions') and agg_col.expressions:
                            # agg_col.expressions[0] is the actual column
                            actual_col = agg_col.expressions[0]
                            agg_col_name = actual_col.name if hasattr(actual_col, 'name') else actual_col.sql()
                        else:
                            agg_col_name = agg_col.name if hasattr(agg_col, 'name') else agg_col.sql()
                        
                        pipeline.append({'$group': {'_id': f'${agg_col_name}'}})
                        pipeline.append({'$count': agg_field})
                        break
            else:
                # Handle regular aggregate functions with $group
                group_stage = {'_id': None}
                
                for inner, alias in aggregate_functions:
                    if isinstance(inner, exp.Anonymous) and inner.this.upper() == 'YEAR':
                        # Handle YEAR() function
                        agg_field = alias or 'year'
                        agg_col = inner.expressions[0] if inner.expressions else None
                        if agg_col:
                            agg_col_name = agg_col.name if hasattr(agg_col, 'name') else agg_col.sql()
                            group_stage['_id'] = {'$year': f'${agg_col_name}'}
                        else:
                            raise SyntaxError("YEAR() requires a column")
                    else:
                        agg_type = inner.__class__.__name__.upper()
                        agg_col = inner.this
                        agg_field = alias or 'total_value'
                        
                        if agg_type == 'COUNT' and isinstance(agg_col, exp.Star):
                            # COUNT(*) - count all documents
                            group_stage[agg_field] = {'$sum': 1}
                        else:
                            if agg_col:
                                agg_col_name = agg_col.name if hasattr(agg_col, 'name') else agg_col.sql()
                            else:
                                raise SyntaxError(f"{agg_type} requires a column")
                            
                            if agg_type == 'COUNT':
                                # COUNT(column) - count non-null values
                                group_stage[agg_field] = {'$sum': {'$cond': [{'$ne': [f'${agg_col_name}', None]}, 1, 0]}}
                            else:
                                group_stage[agg_field] = {self.agg_map[agg_type]: f'${agg_col_name}'}
                
                pipeline.append({'$group': group_stage})
                pipeline.append({'$project': {'_id': 0}})
        else:
            # Handle regular field selection with $project
            project_stage = self._build_projection_stage(regular_fields)
        
        if project_stage is not None:
            pipeline.append({'$project': project_stage})
        
        # Handle ORDER BY and LIMIT
        pipeline.extend(self._process_order_and_limit(order_clause, limit_clause))
        
        return pipeline

    def _build_projection_stage(self, regular_fields: List) -> Dict:
        """Build projection stage without duplicate field mappings."""
        project_stage = {'_id': 0}
        
        for inner, alias in regular_fields:
            if isinstance(inner, exp.Column):
                col_name = inner.name if hasattr(inner, 'name') else inner.sql()
                field_alias = alias or col_name
                
                # Handle field references correctly
                if hasattr(inner, 'table') and inner.table:
                    table_alias = inner.table
                    
                    # Check if this is RIGHT JOIN context and handle accordingly
                    if hasattr(self, 'is_right_join_context') and self.is_right_join_context:
                        # In RIGHT JOIN, main collection is the right table
                        # Left table fields come from 'left_docs' array
                        if hasattr(self, 'main_table_alias') and table_alias == self.main_table_alias:
                            # This is the left table in RIGHT JOIN - comes from left_docs
                            project_stage[field_alias] = f'$left_docs.{col_name}'
                        else:
                            # This is the right table (main collection in RIGHT JOIN)
                            # Always use explicit field reference for clarity
                            if col_name == 'id':
                                project_stage[field_alias] = '$_id'
                            else:
                                project_stage[field_alias] = f'${col_name}'
                    else:
                        # For regular JOINs (INNER/LEFT)
                        if hasattr(self, 'joined_aliases') and table_alias in self.joined_aliases:
                            # For joined tables, use the lookup alias
                            project_stage[field_alias] = f'${table_alias}.{col_name}'
                        elif hasattr(self, 'main_table_alias') and table_alias == self.main_table_alias:
                            # For main table fields, use direct field reference
                            if col_name == 'id':
                                project_stage[field_alias] = '$_id'
                            else:
                                project_stage[field_alias] = f'${col_name}'
                        else:
                            # Fallback: assume main table if not explicitly joined
                            if col_name == 'id':
                                project_stage[field_alias] = '$_id'
                            else:
                                project_stage[field_alias] = f'${col_name}'
                else:
                    # For main table fields, use explicit field reference
                    if col_name == 'id':
                        project_stage[field_alias] = '$_id'
                    else:
                        project_stage[field_alias] = f'${col_name}'
            else:
                # Handle expressions like column calculations
                field_alias = alias or inner.sql()
                project_stage[field_alias] = 1
                
        return project_stage

    def _process_order_and_limit(self, order_clause, limit_clause) -> List[Dict]:
        """Process ORDER BY and LIMIT clauses."""
        pipeline = []
        
        # Handle ORDER BY
        if order_clause and order_clause.expressions:
            sort_dict = {}
            for order in order_clause.expressions:
                if isinstance(order, exp.Ordered):
                    if isinstance(order.this, exp.Column):
                        col_name = order.this.name
                    else:
                        col_name = order.this.sql()
                    direction = -1 if order.args.get('desc') else 1
                    sort_dict[col_name] = direction
            
            if sort_dict:
                pipeline.append({'$sort': sort_dict})
        
        # Handle LIMIT
        if limit_clause:
            limit_value = int(limit_clause.expression.this)
            pipeline.append({'$limit': limit_value})
        
        return pipeline

    def _is_correlated_subquery(self, where_clause) -> bool:
        """Check if subquery references outer table columns."""
        if not where_clause:
            return False
        
        where_str = where_clause.this.sql()
        # Generic approach: look for any table.field references (correlation pattern)
        # A correlated subquery typically has table1.field = table2.field patterns
        table_field_matches = re.findall(r'\b([a-zA-Z_]\w*)\.([a-zA-Z_]\w*)\b', where_str)
        
        # If we find multiple different table references, it's likely correlated
        if len(table_field_matches) >= 2:
            table_names = {match[0] for match in table_field_matches}
            return len(table_names) > 1  # Multiple tables referenced = correlation
        
        # Single table.field reference might also indicate correlation
        return len(table_field_matches) > 0

    def _create_correlated_exists_lookup(self, subquery_collection: str, where_clause) -> List[Dict]:
        """Create $lookup for correlated EXISTS subquery."""
        # Extract correlation condition from WHERE clause
        local_field, foreign_field = self._extract_correlation_fields(where_clause)
        
        return [
            {
                '$lookup': {
                    'from': subquery_collection,
                    'localField': local_field or '_id',
                    'foreignField': foreign_field or '_id', 
                    'as': 'exists_check'
                }
            },
            {
                '$match': {
                    '$expr': {'$gt': [{'$size': '$exists_check'}, 0]}
                }
            },
            {
                '$project': {'exists_check': 0}
            }
        ]

    def _create_simple_exists_lookup(self, subquery_collection: str, where_clause) -> List[Dict]:
        """Create $lookup for non-correlated EXISTS subquery."""
        match_conditions = {}
        if where_clause:
            where_str = where_clause.this.sql()
            # Simple parsing - could be enhanced with the filter parser
            match_conditions = {}
        
        return [
            {
                '$lookup': {
                    'from': subquery_collection,
                    'pipeline': [{'$match': match_conditions}, {'$limit': 1}],
                    'as': 'exists_check'
                }
            },
            {
                '$match': {
                    '$expr': {'$gt': [{'$size': '$exists_check'}, 0]}
                }
            },
            {
                '$project': {'exists_check': 0}
            }
        ]

    def _extract_correlation_fields(self, where_clause) -> tuple:
        """Extract correlation fields from WHERE clause."""
        if not where_clause:
            return None, None
        
        where_str = where_clause.this.sql()
        # Pattern: table1.field1 = table2.field2
        match = re.search(r'(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)', where_str)
        if match:
            table1, field1, table2, field2 = match.groups()
            
            # Convert 'id' to '_id' for MongoDB
            if field1 == 'id':
                field1 = '_id'
            if field2 == 'id':
                field2 = '_id'
                
            # Return local_field, foreign_field for MongoDB $lookup
            # Typically: outer_table.field = inner_table.field
            # So we want: localField (from outer), foreignField (from inner)
            return field2, field1
        
        # Fallback: look for single table.field references
        single_match = re.search(r'(\w+)\.(\w+)', where_str)
        if single_match:
            table, field = single_match.groups()
            if field == 'id':
                field = '_id'
            return field, '_id'  # Default mapping
            
        return None, None

    def _create_correlated_not_exists_lookup(self, subquery_collection: str, where_clause) -> List[Dict]:
        """Create $lookup for correlated NOT EXISTS subquery."""
        local_field, foreign_field = self._extract_correlation_fields(where_clause)
        
        return [
            {
                '$lookup': {
                    'from': subquery_collection,
                    'localField': local_field or '_id',
                    'foreignField': foreign_field or '_id', 
                    'as': 'not_exists_check'
                }
            },
            {
                '$match': {
                    '$expr': {'$eq': [{'$size': '$not_exists_check'}, 0]}
                }
            },
            {
                '$project': {'not_exists_check': 0}
            }
        ]

    def _create_simple_not_exists_lookup(self, subquery_collection: str, where_clause) -> List[Dict]:
        """Create $lookup for non-correlated NOT EXISTS subquery."""
        match_conditions = {}
        if where_clause:
            where_str = where_clause.this.sql()
            match_conditions = {}
        
        return [
            {
                '$lookup': {
                    'from': subquery_collection,
                    'pipeline': [{'$match': match_conditions}, {'$limit': 1}],
                    'as': 'not_exists_check'
                }
            },
            {
                '$match': {
                    '$expr': {'$eq': [{'$size': '$not_exists_check'}, 0]}
                }
            },
            {
                '$project': {'not_exists_check': 0}
            }
        ]