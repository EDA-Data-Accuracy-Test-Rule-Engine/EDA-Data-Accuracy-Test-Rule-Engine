"""SQL query generator for different rule types"""

import re
from typing import Tuple, Dict, Any
from ..rules.manager import Rule

class SQLGenerator:
    """Generates SQL queries for validation rules"""
    
    def __init__(self, database_type: str = 'sqlite'):
        self.database_type = database_type.lower()
    
    def generate_validation_sql(self, rule: Rule) -> Tuple[str, str]:
        """Generate validation SQL and count SQL for a rule"""
        
        if rule.rule_type == 'value_range':
            return self._generate_value_range_sql(rule)
        elif rule.rule_type == 'value_template':
            return self._generate_value_template_sql(rule)
        elif rule.rule_type == 'data_continuity':
            return self._generate_data_continuity_sql(rule)
        elif rule.rule_type == 'statistical_comparison':
            return self._generate_statistical_comparison_sql(rule)
        elif rule.rule_type == 'cross_table_comparison':
            return self._generate_cross_table_comparison_sql(rule)
        else:
            raise ValueError(f"Unsupported rule type: {rule.rule_type}")
    
    def _generate_value_range_sql(self, rule: Rule) -> Tuple[str, str]:
        """Generate SQL for value range validation"""
        table = rule.config.table
        column = rule.config.column
        params = rule.config.parameters
        
        min_val = params['min_value']
        max_val = params['max_value']
        
        # Query to find records OUTSIDE the valid range (failures)
        validation_sql = f"""
            SELECT *
            FROM {table}
            WHERE {column} IS NOT NULL 
            AND ({column} < {min_val} OR {column} > {max_val})
            LIMIT 1000
        """
        
        # Count total records that are not null
        count_sql = f"""
            SELECT COUNT(*) as total_count
            FROM {table}
            WHERE {column} IS NOT NULL
        """
        
        return validation_sql.strip(), count_sql.strip()
    
    def _generate_value_template_sql(self, rule: Rule) -> Tuple[str, str]:
        """Generate SQL for value template (regex) validation"""
        table = rule.config.table
        column = rule.config.column
        pattern = rule.config.parameters['pattern']
        
        # Database-specific regex syntax
        if self.database_type == 'postgresql':
            regex_condition = f"{column} !~ '{pattern}'"
        elif self.database_type == 'mysql':
            regex_condition = f"{column} NOT REGEXP '{pattern}'"
        else:  # SQLite - use LIKE patterns for basic email validation
            # Convert regex pattern to SQL LIKE pattern for basic cases
            if 'email' in pattern.lower() or '@' in pattern:
                # Simple email validation using LIKE pattern
                regex_condition = f"""({column} NOT LIKE '%@%.%' 
                                      OR {column} LIKE '%@%@%' 
                                      OR {column} LIKE '@%' 
                                      OR {column} LIKE '%@' 
                                      OR {column} LIKE '% %')"""
            else:
                # For other patterns, use simple string checks
                regex_condition = f"{column} NOT GLOB '*@*.*'"
        
        validation_sql = f"""
            SELECT id, name, {column}
            FROM {table}
            WHERE {column} IS NOT NULL 
            AND {regex_condition}
            LIMIT 1000
        """
        
        count_sql = f"""
            SELECT COUNT(*) as total_count
            FROM {table}
            WHERE {column} IS NOT NULL
        """
        
        return validation_sql.strip(), count_sql.strip()
    
    def _generate_data_continuity_sql(self, rule: Rule) -> Tuple[str, str]:
        """Generate SQL for data continuity validation"""
        table = rule.config.table
        column = rule.config.column
        params = rule.config.parameters
        
        # Example: Check for gaps in sequence
        if params.get('check_type') == 'sequence_gaps':
            validation_sql = f"""
                WITH sequence_check AS (
                    SELECT {column}, 
                           LAG({column}) OVER (ORDER BY {column}) as prev_value
                    FROM {table}
                    WHERE {column} IS NOT NULL
                    ORDER BY {column}
                )
                SELECT *
                FROM sequence_check
                WHERE prev_value IS NOT NULL 
                AND {column} - prev_value > 1
                LIMIT 1000
            """
        else:
            # Default: Check for NULL values in sequence
            validation_sql = f"""
                SELECT *
                FROM {table}
                WHERE {column} IS NULL
                LIMIT 1000
            """
        
        count_sql = f"""
            SELECT COUNT(*) as total_count
            FROM {table}
        """
        
        return validation_sql.strip(), count_sql.strip()
    
    def _generate_statistical_comparison_sql(self, rule: Rule) -> Tuple[str, str]:
        """Generate SQL for statistical comparison validation"""
        table = rule.config.table
        column = rule.config.column
        params = rule.config.parameters
        
        operation = params['operation'].upper()
        compare_table = params['compare_table']
        compare_column = params['compare_column']
        threshold = params.get('threshold', 0.05)  # 5% default threshold
        
        validation_sql = f"""
            WITH stats1 AS (
                SELECT {operation}({column}) as value1
                FROM {table}
                WHERE {column} IS NOT NULL
            ),
            stats2 AS (
                SELECT {operation}({compare_column}) as value2
                FROM {compare_table}
                WHERE {compare_column} IS NOT NULL
            )
            SELECT 
                stats1.value1,
                stats2.value2,
                ABS(stats1.value1 - stats2.value2) as difference,
                CASE 
                    WHEN stats2.value2 = 0 THEN 
                        CASE WHEN stats1.value1 = 0 THEN 1 ELSE 0 END
                    ELSE 
                        CASE WHEN ABS(stats1.value1 - stats2.value2) / stats2.value2 <= {threshold} THEN 1 ELSE 0 END
                END as passed
            FROM stats1, stats2
        """
        
        count_sql = f"""
            SELECT 1 as total_count
        """
        
        return validation_sql.strip(), count_sql.strip()
    
    def _generate_cross_table_comparison_sql(self, rule: Rule) -> Tuple[str, str]:
        """Generate SQL for cross-table comparison validation"""
        table = rule.config.table
        column = rule.config.column
        params = rule.config.parameters
        
        compare_table = params['compare_table']
        compare_column = params['compare_column']
        join_key = params.get('join_key', 'id')
        operation = params.get('operation', 'SUM')
        
        # Handle different join key names for different tables
        # For orders table, use 'id', for order_items table, use 'order_id'
        if table == 'orders' and compare_table == 'order_items':
            table1_key = 'id'
            table2_key = 'order_id'
        elif table == 'order_items' and compare_table == 'orders':
            table1_key = 'order_id'
            table2_key = 'id'
        else:
            table1_key = join_key
            table2_key = join_key
        
        validation_sql = f"""
            WITH table1_agg AS (
                SELECT {table1_key}, {operation}({column}) as agg_value1
                FROM {table}
                WHERE {column} IS NOT NULL
                GROUP BY {table1_key}
            ),
            table2_agg AS (
                SELECT {table2_key}, {operation}({compare_column}) as agg_value2
                FROM {compare_table}
                WHERE {compare_column} IS NOT NULL
                GROUP BY {table2_key}
            )
            SELECT 
                t1.{table1_key} as join_id,
                t1.agg_value1,
                t2.agg_value2,
                ABS(t1.agg_value1 - COALESCE(t2.agg_value2, 0)) as difference
            FROM table1_agg t1
            LEFT JOIN table2_agg t2 ON t1.{table1_key} = t2.{table2_key}
            WHERE t1.agg_value1 != COALESCE(t2.agg_value2, 0)
            LIMIT 1000
        """
        
        count_sql = f"""
            SELECT COUNT(DISTINCT {table1_key}) as total_count
            FROM {table}
            WHERE {column} IS NOT NULL
        """
        
        return validation_sql.strip(), count_sql.strip()
    
    def optimize_query(self, sql: str, table: str) -> str:
        """Optimize SQL query for better performance"""
        # Add basic optimizations
        optimized = sql
        
        # Add LIMIT if not present for large tables
        if 'LIMIT' not in sql.upper():
            optimized += '\nLIMIT 10000'
        
        # Add hints for index usage (database-specific)
        # This would be expanded based on database type
        
        return optimized