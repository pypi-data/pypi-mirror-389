from typing import Dict, Any, List, Optional
from reasonchain.memory import SharedMemory
from datetime import datetime, timedelta
import json
import statistics

class Metrics:
    def __init__(self, shared_memory: SharedMemory):
        self.shared_memory = shared_memory
        self.metrics_key = "metrics"
        self.timers = {}
        
    def _get_metrics_store(self) -> Dict[str, Any]:
        """Get metrics store from shared memory"""
        return self.shared_memory.retrieve_entry(self.metrics_key) or {}
        
    def _save_metrics_store(self, store: Dict[str, Any]) -> None:
        """Save metrics store to shared memory"""
        self.shared_memory.add_entry(self.metrics_key, store)
        
    def start_timer(self, timer_id: str) -> None:
        """Start a timer for duration tracking"""
        self.timers[timer_id] = datetime.now()
        
    def end_timer(self, timer_id: str) -> float:
        """End a timer and return duration in seconds"""
        if timer_id not in self.timers:
            return 0.0
        start_time = self.timers.pop(timer_id)
        return (datetime.now() - start_time).total_seconds()
        
    def record_task_metrics(self, task_id: str, metrics: Dict[str, Any]) -> None:
        """Record comprehensive task metrics"""
        store = self._get_metrics_store()
        if "tasks" not in store:
            store["tasks"] = {}
            
        if task_id not in store["tasks"]:
            store["tasks"][task_id] = {
                "executions": [],
                "aggregates": {}
            }
            
        # Add timestamp to metrics
        metrics["timestamp"] = datetime.now().isoformat()
        
        # Record execution metrics
        store["tasks"][task_id]["executions"].append(metrics)
        
        # Update aggregates
        aggregates = {}
        executions = store["tasks"][task_id]["executions"]
        
        # Calculate basic statistics for numeric metrics
        for key in metrics:
            if isinstance(metrics[key], (int, float)):
                values = [e[key] for e in executions if key in e]
                if values:
                    aggregates[key] = {
                        "min": min(values),
                        "max": max(values),
                        "avg": statistics.mean(values),
                        "median": statistics.median(values),
                        "total": sum(values)
                    }
                    if len(values) > 1:
                        aggregates[key]["stddev"] = statistics.stdev(values)
                        
        # Calculate success rate
        success_values = [1 if e.get("status") == "success" else 0 for e in executions]
        if success_values:
            aggregates["success_rate"] = sum(success_values) / len(success_values)
            
        # Calculate time-based metrics
        timestamps = [datetime.fromisoformat(e["timestamp"]) for e in executions]
        if len(timestamps) > 1:
            time_diffs = [(t2 - t1).total_seconds() 
                         for t1, t2 in zip(timestamps[:-1], timestamps[1:])]
            aggregates["avg_time_between_executions"] = statistics.mean(time_diffs)
            
        # Update agent-specific aggregates
        agent_type = metrics.get("agent_type")
        if agent_type == "llm":
            token_values = [e.get("total_tokens", 0) for e in executions]
            if token_values:
                aggregates["total_tokens_used"] = sum(token_values)
                aggregates["avg_tokens_per_execution"] = statistics.mean(token_values)
                
            cost_values = [e.get("cost", 0) for e in executions]
            if cost_values:
                aggregates["total_cost"] = sum(cost_values)
                aggregates["avg_cost_per_execution"] = statistics.mean(cost_values)
                
        elif agent_type == "data_retrieval":
            doc_values = [e.get("documents_processed", 0) for e in executions]
            if doc_values:
                aggregates["total_documents_processed"] = sum(doc_values)
                aggregates["avg_documents_per_execution"] = statistics.mean(doc_values)
                
            score_values = [e.get("avg_relevance_score", 0) for e in executions]
            if score_values:
                aggregates["avg_relevance_score"] = statistics.mean(score_values)
                
        store["tasks"][task_id]["aggregates"] = aggregates
        self._save_metrics_store(store)
        
    def record_workflow_metrics(self, workflow_id: str, event_type: str, data: Dict[str, Any]) -> None:
        """Record workflow metrics with enhanced tracking
        
        Args:
            workflow_id: Unique identifier for the workflow
            event_type: Type of workflow event (started, completed, failed, etc.)
            data: Dictionary containing workflow metrics and metadata
        """
        store = self._get_metrics_store()
        if "workflows" not in store:
            store["workflows"] = {}
            
        if workflow_id not in store["workflows"]:
            store["workflows"][workflow_id] = {
                "executions": [],
                "aggregates": {},
                "status": event_type
            }
            
        # Add timestamp and event type to metrics
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            **data
        }
        
        # Record execution metrics
        store["workflows"][workflow_id]["executions"].append(metrics)
        store["workflows"][workflow_id]["status"] = event_type
        
        # Update aggregates
        executions = store["workflows"][workflow_id]["executions"]
        aggregates = {}
        
        # Calculate basic statistics
        for key in metrics:
            if isinstance(metrics[key], (int, float)):
                values = [e[key] for e in executions if key in e]
                if values:
                    aggregates[key] = {
                        "min": min(values),
                        "max": max(values),
                        "avg": statistics.mean(values),
                        "median": statistics.median(values),
                        "total": sum(values)
                    }
                    if len(values) > 1:
                        aggregates[key]["stddev"] = statistics.stdev(values)
                        
        # Calculate success rate
        success_values = [1 if e.get("event_type") == "completed" else 0 for e in executions]
        if success_values:
            aggregates["success_rate"] = sum(success_values) / len(success_values)
            
        # Calculate cost metrics
        cost_values = [e.get("total_cost", 0) for e in executions]
        if cost_values:
            aggregates["total_cost"] = sum(cost_values)
            aggregates["avg_cost_per_execution"] = statistics.mean(cost_values)
            
        store["workflows"][workflow_id]["aggregates"] = aggregates
        self._save_metrics_store(store)
        
    def get_task_metrics(self, task_id: str, time_range: Optional[timedelta] = None) -> Dict[str, Any]:
        """Get task metrics with optional time range filter"""
        store = self._get_metrics_store()
        if "tasks" not in store or task_id not in store["tasks"]:
            return {}
            
        task_data = store["tasks"][task_id]
        
        if time_range:
            cutoff = datetime.now() - time_range
            executions = [
                e for e in task_data["executions"]
                if datetime.fromisoformat(e["timestamp"]) > cutoff
            ]
        else:
            executions = task_data["executions"]
            
        return {
            "executions": executions,
            "aggregates": task_data["aggregates"],
            "latest": executions[-1] if executions else None
        }
        
    def get_workflow_metrics(self, workflow_id: str, time_range: Optional[timedelta] = None) -> Dict[str, Any]:
        """Get workflow metrics with optional time range filter"""
        store = self._get_metrics_store()
        if "workflows" not in store or workflow_id not in store["workflows"]:
            return {}
            
        workflow_data = store["workflows"][workflow_id]
        
        if time_range:
            cutoff = datetime.now() - time_range
            executions = [
                e for e in workflow_data["executions"]
                if datetime.fromisoformat(e["timestamp"]) > cutoff
            ]
        else:
            executions = workflow_data["executions"]
            
        return {
            "executions": executions,
            "aggregates": workflow_data["aggregates"],
            "latest": executions[-1] if executions else None
        }
        
    def get_historical_comparison(self, entity_id: str, metric_name: str, 
                                num_periods: int = 3, period: timedelta = timedelta(days=1)) -> List[Dict[str, Any]]:
        """Get historical comparison of a specific metric"""
        store = self._get_metrics_store()
        entity_type = "tasks" if entity_id in store.get("tasks", {}) else "workflows"
        
        if entity_type not in store or entity_id not in store[entity_type]:
            return []
            
        executions = store[entity_type][entity_id]["executions"]
        now = datetime.now()
        
        # Group executions by period
        periods = []
        for i in range(num_periods):
            period_end = now - (i * period)
            period_start = period_end - period
            
            period_executions = [
                e for e in executions
                if period_start < datetime.fromisoformat(e["timestamp"]) <= period_end
            ]
            
            if period_executions:
                values = [e.get(metric_name, 0) for e in period_executions]
                period_data = {
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat(),
                    "min": min(values),
                    "max": max(values),
                    "avg": statistics.mean(values),
                    "total": sum(values)
                }
                if len(values) > 1:
                    period_data["stddev"] = statistics.stdev(values)
                periods.append(period_data)
                
        return periods
        
    def analyze_bottlenecks(self, workflow_id: str, threshold: float = 0.9) -> List[Dict[str, Any]]:
        """Analyze workflow for performance bottlenecks"""
        store = self._get_metrics_store()
        if "workflows" not in store or workflow_id not in store["workflows"]:
            return []
            
        workflow_data = store["workflows"][workflow_id]
        bottlenecks = []
        
        for execution in workflow_data["executions"]:
            total_duration = execution.get("duration", 0)
            if total_duration > 0:
                for task_id, task_metrics in execution.get("task_metrics", {}).items():
                    task_duration = task_metrics.get("duration", 0)
                    if task_duration / total_duration > threshold:
                        bottlenecks.append({
                            "task_id": task_id,
                            "execution_timestamp": execution["timestamp"],
                            "duration_percentage": (task_duration / total_duration) * 100,
                            "duration": task_duration,
                            "metrics": task_metrics
                        })
                        
        return bottlenecks
        
    def analyze_costs(self, workflow_id: str, time_range: Optional[timedelta] = None) -> Dict[str, Any]:
        """Analyze workflow costs"""
        store = self._get_metrics_store()
        if "workflows" not in store or workflow_id not in store["workflows"]:
            return {}
            
        workflow_data = store["workflows"][workflow_id]
        
        if time_range:
            cutoff = datetime.now() - time_range
            executions = [
                e for e in workflow_data["executions"]
                if datetime.fromisoformat(e["timestamp"]) > cutoff
            ]
        else:
            executions = workflow_data["executions"]
            
        cost_analysis = {
            "total_cost": 0,
            "cost_by_agent_type": {},
            "cost_by_model": {},
            "cost_trend": []
        }
        
        for execution in executions:
            execution_cost = 0
            timestamp = execution["timestamp"]
            
            for task_id, task_metrics in execution.get("task_metrics", {}).items():
                task_cost = task_metrics.get("cost", 0)
                agent_type = task_metrics.get("agent_type", "unknown")
                model_name = task_metrics.get("model_name", "unknown")
                
                execution_cost += task_cost
                
                # Update cost by agent type
                if agent_type not in cost_analysis["cost_by_agent_type"]:
                    cost_analysis["cost_by_agent_type"][agent_type] = 0
                cost_analysis["cost_by_agent_type"][agent_type] += task_cost
                
                # Update cost by model
                if model_name not in cost_analysis["cost_by_model"]:
                    cost_analysis["cost_by_model"][model_name] = 0
                cost_analysis["cost_by_model"][model_name] += task_cost
                
            cost_analysis["total_cost"] += execution_cost
            cost_analysis["cost_trend"].append({
                "timestamp": timestamp,
                "cost": execution_cost
            })
            
        return cost_analysis
