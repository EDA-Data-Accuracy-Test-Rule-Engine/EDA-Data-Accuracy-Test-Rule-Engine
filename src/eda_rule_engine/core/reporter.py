"""Reporting system for EDA Rule Engine"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import os

class Reporter:
    """Generate reports and analytics for rule executions"""
    
    def __init__(self, results_file: str = ".eda-results.json"):
        self.results_file = results_file
        self.results_history = self._load_results_history()
    
    def _load_results_history(self) -> List[Dict]:
        """Load historical results from file"""
        if os.path.exists(self.results_file):
            try:
                with open(self.results_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return []
        return []
    
    def _save_results_history(self):
        """Save results history to file"""
        with open(self.results_file, 'w') as f:
            json.dump(self.results_history, f, indent=2, default=str)
    
    def record_execution_result(self, result: Dict):
        """Record a rule execution result"""
        result['timestamp'] = datetime.now().isoformat()
        self.results_history.append(result)
        
        # Keep only last 1000 results to prevent file from growing too large
        if len(self.results_history) > 1000:
            self.results_history = self.results_history[-1000:]
        
        self._save_results_history()
    
    def generate_summary_report(self, database: Optional[str] = None, days: int = 7) -> Dict:
        """Generate a summary report for the specified period"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter results by date and database
        filtered_results = []
        for result in self.results_history:
            try:
                result_date = datetime.fromisoformat(result.get('timestamp', ''))
                if result_date >= cutoff_date:
                    filtered_results.append(result)
            except:
                continue
        
        if not filtered_results:
            return {
                'overall_score': 0.0,
                'total_rules': 0,
                'avg_pass_rate': 0.0,
                'total_executions': 0,
                'top_issues': []
            }
        
        # Calculate metrics
        total_executions = len(filtered_results)
        total_rules = len(set(r['rule_id'] for r in filtered_results))
        
        pass_rates = [r['pass_rate'] for r in filtered_results if 'pass_rate' in r]
        avg_pass_rate = sum(pass_rates) / len(pass_rates) if pass_rates else 0.0
        
        # Calculate overall score (weighted by execution time and success rate)
        overall_score = avg_pass_rate * 0.8 + (total_executions / (days * 10)) * 0.2
        overall_score = min(100.0, overall_score)
        
        # Find top issues (rules with lowest pass rates)
        rule_stats = {}
        for result in filtered_results:
            rule_id = result['rule_id']
            rule_name = result['rule_name']
            if rule_id not in rule_stats:
                rule_stats[rule_id] = {
                    'rule_name': rule_name,
                    'total_executions': 0,
                    'total_pass_rate': 0.0,
                    'failure_count': 0
                }
            
            rule_stats[rule_id]['total_executions'] += 1
            rule_stats[rule_id]['total_pass_rate'] += result.get('pass_rate', 0.0)
            if not result.get('passed', False):
                rule_stats[rule_id]['failure_count'] += 1
        
        # Calculate average pass rates and failure rates
        top_issues = []
        for rule_id, stats in rule_stats.items():
            avg_pass_rate = stats['total_pass_rate'] / stats['total_executions']
            failure_rate = (stats['failure_count'] / stats['total_executions']) * 100
            
            top_issues.append({
                'rule_name': stats['rule_name'],
                'rule_id': rule_id,
                'avg_pass_rate': avg_pass_rate,
                'failure_rate': failure_rate,
                'executions': stats['total_executions']
            })
        
        # Sort by failure rate (highest first)
        top_issues.sort(key=lambda x: x['failure_rate'], reverse=True)
        
        return {
            'overall_score': overall_score,
            'total_rules': total_rules,
            'avg_pass_rate': avg_pass_rate,
            'total_executions': total_executions,
            'top_issues': top_issues,
            'period_days': days,
            'generated_at': datetime.now().isoformat()
        }
    
    def generate_trend_report(self, rule_id: str, days: int = 30) -> Dict:
        """Generate a trend report for a specific rule"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter results for specific rule
        rule_results = []
        for result in self.results_history:
            try:
                result_date = datetime.fromisoformat(result.get('timestamp', ''))
                if (result_date >= cutoff_date and 
                    result.get('rule_id') == rule_id):
                    rule_results.append(result)
            except:
                continue
        
        if not rule_results:
            return {
                'rule_id': rule_id,
                'trend_data': [],
                'average_pass_rate': 0.0,
                'trend_direction': 'stable'
            }
        
        # Group by day
        daily_stats = {}
        for result in rule_results:
            date_str = result['timestamp'][:10]  # YYYY-MM-DD
            if date_str not in daily_stats:
                daily_stats[date_str] = {
                    'date': date_str,
                    'executions': 0,
                    'total_pass_rate': 0.0,
                    'total_records': 0
                }
            
            daily_stats[date_str]['executions'] += 1
            daily_stats[date_str]['total_pass_rate'] += result.get('pass_rate', 0.0)
            daily_stats[date_str]['total_records'] += result.get('total_records', 0)
        
        # Calculate daily averages
        trend_data = []
        for date_str, stats in sorted(daily_stats.items()):
            avg_pass_rate = stats['total_pass_rate'] / stats['executions']
            trend_data.append({
                'date': date_str,
                'pass_rate': avg_pass_rate,
                'executions': stats['executions'],
                'total_records': stats['total_records']
            })
        
        # Calculate overall average and trend
        all_pass_rates = [d['pass_rate'] for d in trend_data]
        average_pass_rate = sum(all_pass_rates) / len(all_pass_rates) if all_pass_rates else 0.0
        
        # Simple trend calculation
        if len(trend_data) >= 2:
            recent_avg = sum(d['pass_rate'] for d in trend_data[-7:]) / min(7, len(trend_data))
            older_avg = sum(d['pass_rate'] for d in trend_data[:-7]) / max(1, len(trend_data) - 7)
            
            if recent_avg > older_avg + 1:
                trend_direction = 'improving'
            elif recent_avg < older_avg - 1:
                trend_direction = 'declining'
            else:
                trend_direction = 'stable'
        else:
            trend_direction = 'insufficient_data'
        
        return {
            'rule_id': rule_id,
            'trend_data': trend_data,
            'average_pass_rate': average_pass_rate,
            'trend_direction': trend_direction,
            'period_days': days
        }