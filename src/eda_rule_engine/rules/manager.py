"""Rule management system for EDA Rule Engine"""

import json
import yaml
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

class RuleConfig(BaseModel):
    """Rule configuration model"""
    table: str
    column: Optional[str] = None
    rule_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

class Rule(BaseModel):
    """Rule model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    description: str = ""
    rule_type: str
    config: RuleConfig
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_run: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)

class RuleManager:
    """Manages validation rules"""
    
    def __init__(self, rules_file: str = ".eda-rules.yaml"):
        self.rules_file = rules_file
        self.rules: Dict[str, Rule] = {}
        self._load_rules()
    
    def _load_rules(self):
        """Load rules from file"""
        if os.path.exists(self.rules_file):
            try:
                with open(self.rules_file, 'r') as f:
                    rules_data = yaml.safe_load(f) or {}
                    for rule_id, rule_dict in rules_data.items():
                        # Convert datetime strings back to datetime objects
                        if 'created_at' in rule_dict and isinstance(rule_dict['created_at'], str):
                            rule_dict['created_at'] = datetime.fromisoformat(rule_dict['created_at'])
                        if 'updated_at' in rule_dict and isinstance(rule_dict['updated_at'], str):
                            rule_dict['updated_at'] = datetime.fromisoformat(rule_dict['updated_at'])
                        if 'last_run' in rule_dict and rule_dict['last_run']:
                            rule_dict['last_run'] = datetime.fromisoformat(rule_dict['last_run'])
                        
                        self.rules[rule_id] = Rule(**rule_dict)
            except Exception as e:
                logger.warning(f"Could not load rules file: {e}")
                self.rules = {}
        else:
            self.rules = {}
    
    def _save_rules(self):
        """Save rules to file"""
        rules_data = {}
        for rule_id, rule in self.rules.items():
            rule_dict = rule.model_dump()
            # Convert datetime objects to strings for YAML serialization
            rule_dict['created_at'] = rule_dict['created_at'].isoformat()
            rule_dict['updated_at'] = rule_dict['updated_at'].isoformat()
            if rule_dict['last_run']:
                rule_dict['last_run'] = rule_dict['last_run'].isoformat()
            rules_data[rule_id] = rule_dict
        
        with open(self.rules_file, 'w') as f:
            yaml.dump(rules_data, f, default_flow_style=False)
    
    def create_rule(
        self, 
        name: str, 
        rule_type: str, 
        config: Dict[str, Any], 
        description: str = "",
        tags: List[str] = None
    ) -> str:
        """Create a new validation rule"""
        
        # Validate rule type
        valid_types = [
            'value_range', 'value_template', 'data_continuity', 
            'statistical_comparison', 'cross_table_comparison', 'boolean_combination'
        ]
        if rule_type not in valid_types:
            raise ValueError(f"Invalid rule type: {rule_type}. Valid types: {valid_types}")
        
        # Create rule configuration
        rule_config = RuleConfig(
            table=config['table'],
            column=config.get('column'),
            rule_type=rule_type,
            parameters=config
        )
        
        # Create rule
        rule = Rule(
            name=name,
            description=description,
            rule_type=rule_type,
            config=rule_config,
            tags=tags or []
        )
        
        self.rules[rule.id] = rule
        self._save_rules()
        
        return rule.id
    
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get a rule by ID or name"""
        # Try to find by ID first
        if rule_id in self.rules:
            return self.rules[rule_id]
        
        # Try to find by name
        for rule in self.rules.values():
            if rule.name == rule_id:
                return rule
        
        return None
    
    def list_rules(self, status: Optional[str] = None, table: Optional[str] = None, tag: Optional[str] = None) -> List[Dict]:
        """List rules with optional filtering"""
        filtered_rules = []
        
        for rule in self.rules.values():
            # Apply filters
            if status and rule.status != status:
                continue
            if table and rule.config.table != table:
                continue
            if tag and tag not in rule.tags:
                continue
            
            filtered_rules.append({
                'id': rule.id,
                'name': rule.name,
                'type': rule.rule_type,
                'table': rule.config.table,
                'column': rule.config.column,
                'status': rule.status,
                'last_run': rule.last_run.isoformat() if rule.last_run else 'Never',
                'tags': rule.tags
            })
        
        return filtered_rules
    
    def update_rule(self, rule_id: str, **updates) -> bool:
        """Update a rule"""
        rule = self.get_rule(rule_id)
        if not rule:
            return False
        
        # Update allowed fields
        allowed_updates = ['name', 'description', 'status', 'tags']
        for key, value in updates.items():
            if key in allowed_updates and hasattr(rule, key):
                setattr(rule, key, value)
        
        rule.updated_at = datetime.now()
        self._save_rules()
        return True
    
    def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule"""
        rule = self.get_rule(rule_id)
        if not rule:
            return False
        
        del self.rules[rule.id]
        self._save_rules()
        return True
    
    def update_last_run(self, rule_id: str):
        """Update the last run timestamp for a rule"""
        rule = self.get_rule(rule_id)
        if rule:
            rule.last_run = datetime.now()
            self._save_rules()
    
    def get_rules_for_table(self, table: str) -> List[Rule]:
        """Get all rules for a specific table"""
        return [rule for rule in self.rules.values() if rule.config.table == table and rule.status == 'active']
    
    def get_rules_by_tag(self, tag: str) -> List[Rule]:
        """Get all rules with a specific tag"""
        return [rule for rule in self.rules.values() if tag in rule.tags and rule.status == 'active']
    
    def export_rules(self, file_path: str, format: str = 'yaml'):
        """Export rules to a file"""
        rules_data = {}
        for rule_id, rule in self.rules.items():
            rules_data[rule_id] = rule.model_dump()
        
        if format.lower() == 'json':
            with open(file_path, 'w') as f:
                json.dump(rules_data, f, indent=2, default=str)
        else:  # yaml
            with open(file_path, 'w') as f:
                yaml.dump(rules_data, f, default_flow_style=False)
    
    def import_rules(self, file_path: str, format: str = 'yaml'):
        """Import rules from a file"""
        try:
            if format.lower() == 'json':
                with open(file_path, 'r') as f:
                    rules_data = json.load(f)
            else:  # yaml
                with open(file_path, 'r') as f:
                    rules_data = yaml.safe_load(f)
            
            imported_count = 0
            for rule_id, rule_dict in rules_data.items():
                try:
                    # Convert string dates back to datetime objects
                    if 'created_at' in rule_dict and isinstance(rule_dict['created_at'], str):
                        rule_dict['created_at'] = datetime.fromisoformat(rule_dict['created_at'])
                    if 'updated_at' in rule_dict and isinstance(rule_dict['updated_at'], str):
                        rule_dict['updated_at'] = datetime.fromisoformat(rule_dict['updated_at'])
                    if 'last_run' in rule_dict and rule_dict['last_run']:
                        rule_dict['last_run'] = datetime.fromisoformat(rule_dict['last_run'])
                    
                    rule = Rule(**rule_dict)
                    self.rules[rule.id] = rule
                    imported_count += 1
                except Exception as e:
                    logger.warning(f"Could not import rule {rule_id}: {e}")
            
            self._save_rules()
            return imported_count
            
        except Exception as e:
            logger.error(f"Failed to import rules: {e}")
            raise