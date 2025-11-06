# ##################################################################
#
# Copyright 2025 Teradata. All rights reserved.
# TERADATA CONFIDENTIAL AND TRADE SECRET
#
# Primary Owner: Snigdha Biswas (snigdha.biswas@teradata.com)
# Secondary Owner: Aanchal Kavedia (aanchal.kavedia@teradata.com)
#
# Notes:
#   * This code is only for internal use.
#   * The code may perform modify, create, or delete operations
#     in database based on given query. Hence, limit the permissions
#     granted to the credentials.
#   * This file implements the functionality of generating filter JSON.
#
# ##################################################################

import re

class _FilterProcessor:
    """
        This class provides parsing of SQL filter expressions.
    """
    
    def __init__(self):
        """
        DESCRIPTION:
            Initialize FilterProcessor instance.

        PARAMETERS:
            None.

        RETURNS:
            None.

        RAISES:
            None.
        """
        pass
    
    def _process_filter(self, filter_expression):
        """
        DESCRIPTION:
            Parse SQL filter expression into structured JSON format.
            This method handles the main parsing logic for converting
            SQL WHERE clause expressions into JSON format.

        PARAMETERS:
            filter_expression:
                Required Argument.
                Specifies the SQL filter expression to parse.
                Types: str

        RETURNS:
            dict.

        RAISES:
            ValueError.

        EXAMPLES:
            >>> self._process_filter("age = 25")
            {'key': 'age', 'match': {'value': 25}}
            
            >>> self._process_filter("age > 25 AND name = 'John'")
            {'and': [{'key': 'age', 'range': {'gt': 25}}, {'key': 'name', 'match': {'value': 'John'}}]}
        """
        # Skip validation as it's already done in the main file
        if filter_expression is None:
            return None
        
        # Normalize expression for consistent parsing
        expr = filter_expression.strip().replace('==', '=').replace('!=', '<>')
        expr_lower = expr.lower()
        
        # Parse with proper operator precedence: NOT > AND > OR
        if expr_lower.startswith('not '):
            not_condition = expr[4:].strip()  # Remove "not " prefix
            # Handle parentheses in NOT conditions
            if not_condition.startswith('(') and not_condition.endswith(')'):
                not_condition = not_condition[1:-1].strip()
            parsed_condition = self._process_filter(not_condition)
            return {"not": [parsed_condition]} if parsed_condition else None
        elif ' or ' in expr_lower:
            return self._parse_logical_expression(expr, expr_lower, ' or ', 'or')
        elif ' and ' in expr_lower:
            return self._parse_logical_expression(expr, expr_lower, ' and ', 'and')
        else:
            return self._parse_condition(expr)
    
    def _parse_logical_expression(self, expr, expr_lower, separator, operator):
        """
        DESCRIPTION:
            Parse complex logical expressions with AND/OR operators into JSON format.
            Splits the expression by the logical operator and processes each part.

        PARAMETERS:
            expr:
                Required Argument.
                Specifies the original expression with proper case.
                Types: str

            expr_lower:
                Required Argument.
                Specifies the lowercase version of the expression.
                Types: str

            separator:
                Required Argument.
                Specifies the separator string (e.g., ' and ', ' or ').
                Types: str

            operator:
                Required Argument.
                Specifies the logical operator name ('and' or 'or').
                Types: str

        RETURNS:
            dict.

        RAISES:
            ValueError.

        EXAMPLES:
            >>> self._parse_logical_expression(
            ...     "col1 = 'A' AND col2 > 10", "col1 = 'a' and col2 > 10", " and ", "and"
            ... )
            {'and': [{'key': 'col1', 'match': {'value': 'A'}}, {'key': 'col2', 'range': {'gt': 10}}]}
        """
        conditions = []
        parts = expr_lower.split(separator)
        start_pos = 0
        
        for part in parts:
            if not (part := part.strip()):
                continue
            
            # Find original part position and extract it with proper case
            part_start = expr_lower.find(part, start_pos)
            if part_start != -1:
                original_part = expr[part_start:part_start + len(part)].strip()
                if original_part and (condition := self._parse_condition(original_part)):
                    conditions.append(condition)
                start_pos = part_start + len(part) + len(separator)
        
        return {operator: conditions} if len(conditions) > 1 else (conditions[0] if conditions else None)
    
    def _parse_condition(self, condition):
        """
        DESCRIPTION:
            Parse a single filter condition into JSON format.
            Identifies the operator and converts the condition to appropriate JSON structure.

        PARAMETERS:
            condition:
                Required Argument.
                Specifies the individual condition to parse (e.g., "age > 25").
                Types: str

        RETURNS:
            dict.

        RAISES:
            ValueError.

        EXAMPLES:
            >>> self._parse_condition("status = 'active'")
            {'key': 'status', 'match': {'value': 'active'}}
            
            >>> self._parse_condition("price >= 100.50")
            {'key': 'price', 'range': {'gte': 100.5}}
        """
        condition = condition.strip()
        if not condition:
            raise ValueError("Empty condition not allowed")
            
        lower_condition = condition.lower()
        
        # Operator definitions with format specifications
        # Order matters: longer operators first to avoid partial matches
        operators = [
            ('is not null', 'not null', 'match_boolean'),
            ('is null', 'null', 'match_boolean'), 
            ('not like', 'not like', 'match_like'),
            ('not in', 'except', 'match_list'),
            ('<=', 'lte', 'range'), ('>=', 'gte', 'range'),
            ('<>', 'not value', 'match'), ('!=', 'not value', 'match'),
            ('==', 'value', 'match'), ('like', 'like', 'match_like'),
            ('in', 'any', 'match_list'), ('=', 'value', 'match'),
            ('<', 'lt', 'range'), ('>', 'gt', 'range')
        ]
        
        # Optimized operator matching with word boundary support
        for op, json_op, format_type in operators:
            if op.isalpha():
                # Word operators need boundary checking to avoid partial matches
                pattern = rf'\b{re.escape(op)}\b'
                match = re.search(pattern, lower_condition, re.IGNORECASE)
                if match:
                    pos = match.start()
                    key = condition[:pos].strip()
                    value_part = condition[pos + len(op):].strip()
                    
                    if key:
                        return self._build_condition_json(key, value_part, json_op, format_type)
            else:
                # Symbol operators with precedence checking
                for pattern in [f' {op} ', op]:
                    pos = lower_condition.find(pattern)
                    if pos != -1:
                        # Avoid matching parts of compound operators (e.g., '<' in '<=')
                        if len(op) == 1 and pos > 0:
                            before = lower_condition[pos-1]
                            after = lower_condition[pos+1:pos+2] if pos+1 < len(lower_condition) else ''
                            if (before in '<>' and op in '<>') or (after in '=' and op in '<>='):
                                continue
                        
                        key = condition[:pos].strip()
                        value_part = condition[pos + len(pattern):].strip()
                        
                        if key:
                            return self._build_condition_json(key, value_part, json_op, format_type)
                        break
        
        # Provide comprehensive error message with supported operators
        raise ValueError(
            f"Unsupported filter condition: '{condition}'. "
            f"Supported operators: =, !=, <>, >, <, >=, <=, LIKE, NOT LIKE, "
            f"IN, NOT IN, IS NULL, IS NOT NULL. "
            f"Ensure proper spacing around operators."
        )
    
    def _build_condition_json(self, key, value_part, json_op, format_type):
        """
        DESCRIPTION:
            Build the JSON structure for a parsed condition.
            Constructs appropriate JSON format based on the condition type.

        PARAMETERS:
            key:
                Required Argument.
                Specifies the field name in the condition.
                Types: str

            value_part:
                Required Argument.
                Specifies the value portion of the condition.
                Types: str

            json_op:
                Required Argument.
                Specifies the JSON operator name.
                Types: str

            format_type:
                Required Argument.
                Specifies the format type ('range', 'match', 'match_boolean', etc.).
                Types: str

        RETURNS:
            dict.

        RAISES:
            None.
        """
        if format_type == 'range':
            return {"key": key, "range": {json_op: self._parse_value(value_part)}}
        elif format_type == 'match_boolean':
            return {"key": key, "match": {json_op: True}}
        elif format_type == 'match_list':
            # Parse IN clause values efficiently
            if not value_part:
                values = []
            else:
                value_part = value_part.strip('() ')
                values = [self._parse_value(part.strip()) for part in value_part.split(',') if part.strip()]
            return {"key": key, "match": {json_op: values}}
        elif format_type == 'match_like':
            value = self._parse_value(value_part)
            # Clean LIKE patterns by removing SQL wildcards for API compatibility
            clean_value = value.strip('%_') if isinstance(value, str) else value
            return {"key": key, "match": {json_op: clean_value}}
        else:  # 'match'
            # Handle empty string as special case for API
            if json_op == 'value' and (not value_part or value_part.strip('\'"') == ''):
                return {"key": key, "match": {"empty": True}}
            return {"key": key, "match": {json_op: self._parse_value(value_part)}}

    def _parse_value(self, value_str):
        """
        DESCRIPTION:
            Convert string value to appropriate Python type.
            Automatically detects and converts integers, floats, booleans,
            and strings with optimized parsing for common cases.

        PARAMETERS:
            value_str:
                Required Argument.
                Specifies the string value to convert.
                Types: str

        RETURNS:
            Converted value in appropriate Python type (int, float, bool, or str).

        RAISES:
            None.

        EXAMPLES:
            >>> self._parse_value("123")
            123
            >>> self._parse_value("true")
            True
        """
        if not value_str:
            return value_str
            
        # Remove surrounding quotes efficiently
        value = value_str.strip('\'"')
        
        # Quick empty check after quote removal
        if not value:
            return value
        
        # Optimized boolean conversion (case-insensitive)
        lower_value = value.lower()
        if lower_value == 'true':
            return True
        elif lower_value == 'false':
            return False
        
        # Optimized numeric conversion for common cases
        if value.isdigit():
            return int(value)
        elif value.startswith('-') and value[1:].isdigit():
            return int(value)
        elif '.' in value:
            try:
                return float(value)
            except ValueError:
                pass
        
        return value


# Create instance for module-level use
_filter_processor = _FilterProcessor()


def process_filter(filter_expression):
    """
    DESCRIPTION:
        Process SQL filter expression and convert it to JSON format.
        This is the main entry point for filter processing functionality.

    PARAMETERS:
        filter_expression:
            Required Argument.
            Specifies the SQL filter expression to convert.
            Types: str

    RETURNS:
        dict

    RAISES:
        ValueError

    EXAMPLES:
        >>> process_filter("age > 25")
        {'key': 'age', 'range': {'gt': 25}}
        
        >>> process_filter("name = 'John' AND age >= 18")
        {'and': [{'key': 'name', 'match': {'value': 'John'}}, {'key': 'age', 'range': {'gte': 18}}]}
    """
    return _filter_processor._process_filter(filter_expression)