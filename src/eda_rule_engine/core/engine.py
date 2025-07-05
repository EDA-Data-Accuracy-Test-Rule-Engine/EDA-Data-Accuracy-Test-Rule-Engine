"""Core rule execution engine for EDA Rule Engine"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from ..database.manager import DatabaseManager
from ..rules.manager import RuleManager, Rule
from ..parsers.sql_generator import SQLGenerator

logger = logging.getLogger(__name__)

class RuleExecutionResult:
    """Result of a rule execution"""
    
    def __init__(self, rule_name: str, rule_id: str):
        self.rule_name = rule_name
        self.rule_id = rule_id
        self.start_time = time.time()
        self.end_time = None
        self.total_records = 0
        self.passed_records = 0
        self.failed_records = 0
        self.pass_rate = 0.0
        self.execution_time = 0.0
        self.passed = False
        self.error = None
        self.failed_samples = []
    
    def finish(self):
        """Mark execution as finished and calculate metrics"""
        self.end_time = time.time()
        self.execution_time = self.end_time - self.start_time
        
        if self.total_records > 0:
            self.pass_rate = (self.passed_records / self.total_records) * 100
            self.passed = self.pass_rate >= 100  # All records must pass for rule to pass
        else:
            self.pass_rate = 0.0
            self.passed = False
    
    def to_dict(self) -> Dict:
        """Convert result to dictionary"""
        return {
            'rule_name': self.rule_name,
            'rule_id': self.rule_id,
            'passed': self.passed,
            'total_records': self.total_records,
            'passed_records': self.passed_records,
            'failed_records': self.failed_records,
            'pass_rate': self.pass_rate,
            'execution_time': self.execution_time,
            'error': self.error,
            'failed_samples': self.failed_samples
        }

class RuleEngine:
    """Core engine for executing validation rules"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.rule_manager = RuleManager()
        self.sql_generator = SQLGenerator()
    
    def execute_rule(self, rule_id: str, database: Optional[str] = None) -> Dict:
        """Execute a single validation rule"""
        rule = self.rule_manager.get_rule(rule_id)
        if not rule:
            raise ValueError(f"Rule '{rule_id}' not found")
        
        # Get database connection
        if not database:
            connections = self.db_manager.list_connections()
            if not connections:
                raise ValueError("No database connections configured")
            database = connections[0]['name']  # Use first available connection
        
        result = RuleExecutionResult(rule.name, rule.id)
        
        try:
            # Generate SQL query for the rule
            sql_query, count_query = self.sql_generator.generate_validation_sql(rule)
            
            logger.info(f"Executing rule '{rule.name}' on database '{database}'")
            logger.debug(f"Generated SQL: {sql_query}")
            
            # Execute count query to get total records
            count_result = self.db_manager.execute_query(database, count_query)
            result.total_records = count_result[0]['total_count'] if count_result else 0
            
            # Execute validation query
            validation_result = self.db_manager.execute_query(database, sql_query)
            
            # Process results based on rule type
            self._process_rule_result(rule, validation_result, result)
            
            # Update rule last run timestamp
            self.rule_manager.update_last_run(rule.id)
            
        except Exception as e:
            logger.error(f"Error executing rule '{rule.name}': {e}")
            result.error = str(e)
        
        result.finish()
        
        # Record result to history
        from ..core.reporter import Reporter
        reporter = Reporter()
        reporter.record_execution_result(result.to_dict())
        
        return result.to_dict()
    
    def execute_batch_rules(
        self, 
        table: Optional[str] = None, 
        tag: Optional[str] = None,
        database: Optional[str] = None,
        max_workers: int = 4
    ) -> List[Dict]:
        """Execute multiple rules in parallel"""
        
        # Get rules to execute
        if table:
            rules = self.rule_manager.get_rules_for_table(table)
        elif tag:
            rules = self.rule_manager.get_rules_by_tag(tag)
        else:
            rules = [rule for rule in self.rule_manager.rules.values() if rule.status == 'active']
        
        if not rules:
            return []
        
        results = []
        
        # Execute rules in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_rule = {
                executor.submit(self.execute_rule, rule.id, database): rule 
                for rule in rules
            }
            
            for future in as_completed(future_to_rule):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    rule = future_to_rule[future]
                    logger.error(f"Error executing rule '{rule.name}': {e}")
                    error_result = RuleExecutionResult(rule.name, rule.id)
                    error_result.error = str(e)
                    error_result.finish()
                    results.append(error_result.to_dict())
        
        return results
    
    def _process_rule_result(self, rule: Rule, query_result: List[Dict], result: RuleExecutionResult):
        """Process query results based on rule type"""
        
        if rule.rule_type == 'value_range':
            self._process_value_range_result(rule, query_result, result)
        elif rule.rule_type == 'value_template':
            self._process_value_template_result(rule, query_result, result)
        elif rule.rule_type == 'data_continuity':
            self._process_data_continuity_result(rule, query_result, result)
        elif rule.rule_type == 'statistical_comparison':
            self._process_statistical_comparison_result(rule, query_result, result)
        elif rule.rule_type == 'cross_table_comparison':
            self._process_cross_table_comparison_result(rule, query_result, result)
        else:
            raise ValueError(f"Unsupported rule type: {rule.rule_type}")
    
    def _process_value_range_result(self, rule: Rule, query_result: List[Dict], result: RuleExecutionResult):
        """Process value range validation results"""
        if query_result:
            # Query returns records that are OUT OF RANGE (failed)
            result.failed_records = len(query_result)
            result.passed_records = result.total_records - result.failed_records
            result.failed_samples = query_result[:5]  # Store first 5 failed records
    
    def _process_value_template_result(self, rule: Rule, query_result: List[Dict], result: RuleExecutionResult):
        """Process value template (regex) validation results"""
        if query_result:
            # Query returns records that DON'T MATCH pattern (failed)
            result.failed_records = len(query_result)
            result.passed_records = result.total_records - result.failed_records
            result.failed_samples = query_result[:5]
    
    def _process_data_continuity_result(self, rule: Rule, query_result: List[Dict], result: RuleExecutionResult):
        """Process data continuity validation results"""
        if query_result:
            # Query returns gaps or inconsistencies
            result.failed_records = len(query_result)
            result.passed_records = result.total_records - result.failed_records
            result.failed_samples = query_result[:5]
    
    def _process_statistical_comparison_result(self, rule: Rule, query_result: List[Dict], result: RuleExecutionResult):
        """Process statistical comparison results"""
        if query_result:
            comparison_result = query_result[0]
            # Assume query returns a boolean result or comparison metrics
            if 'passed' in comparison_result:
                if comparison_result['passed']:
                    result.passed_records = result.total_records
                    result.failed_records = 0
                else:
                    result.passed_records = 0
                    result.failed_records = result.total_records
                    result.failed_samples = [comparison_result]
    
    def _process_cross_table_comparison_result(self, rule: Rule, query_result: List[Dict], result: RuleExecutionResult):
        """Process cross-table comparison results"""
        if query_result:
            # Query returns records where comparison failed
            result.failed_records = len(query_result)
            result.passed_records = result.total_records - result.failed_records
            result.failed_samples = query_result[:5]
    
    def validate_rule_configuration(self, rule: Rule) -> List[str]:
        """Validate rule configuration and return list of errors"""
        errors = []
        
        # Check if table exists
        try:
            connections = self.db_manager.list_connections()
            if connections:
                db_name = connections[0]['name']
                table_info = self.db_manager.get_table_info(db_name, rule.config.table)
                if not table_info['columns']:
                    errors.append(f"Table '{rule.config.table}' not found or has no columns")
                
                # Check if column exists (if specified)
                if rule.config.column:
                    column_names = [col['column_name'] for col in table_info['columns']]
                    if rule.config.column not in column_names:
                        errors.append(f"Column '{rule.config.column}' not found in table '{rule.config.table}'")
        except Exception as e:
            errors.append(f"Could not validate table/column: {e}")
        
        # Validate rule-specific parameters
        if rule.rule_type == 'value_range':
            params = rule.config.parameters
            if 'min_value' not in params or 'max_value' not in params:
                errors.append("Value range rules require 'min_value' and 'max_value' parameters")
            elif params.get('min_value', 0) >= params.get('max_value', 0):
                errors.append("min_value must be less than max_value")
        
        elif rule.rule_type == 'value_template':
            if 'pattern' not in rule.config.parameters:
                errors.append("Value template rules require 'pattern' parameter")
        
        return errors
    
    def get_execution_statistics(self, days: int = 7) -> Dict:
        """Get execution statistics for the last N days"""
        # This would typically query a results database
        # For now, return mock statistics
        return {
            'total_executions': 0,
            'average_execution_time': 0.0,
            'success_rate': 0.0,
            'most_failed_rules': []
        }