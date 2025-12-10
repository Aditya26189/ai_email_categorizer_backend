#!/usr/bin/env python3
"""
API Log Analyzer for AI Email Categorizer Backend
Analyzes CrashLens logs to provide insights into API usage, performance, and costs.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter, defaultdict

import click
from loguru import logger

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    console = type('Console', (), {'print': print})()
    rprint = print

console = Console() if RICH_AVAILABLE else type('Console', (), {'print': print})()


class APILogAnalyzer:
    """Analyzes API logs from the email categorizer backend."""
    
    def __init__(self, log_file_path: str):
        self.log_file_path = Path(log_file_path)
        self.events = []
        self.load_logs()
    
    def load_logs(self):
        """Load and parse log events from JSONL file."""
        if not self.log_file_path.exists():
            logger.error(f"Log file not found: {self.log_file_path}")
            return
        
        try:
            with open(self.log_file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            event = json.loads(line)
                            self.events.append(event)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Invalid JSON on line {line_num}: {e}")
            
            logger.info(f"Loaded {len(self.events)} log events")
            
        except Exception as e:
            logger.error(f"Error loading logs: {e}")
    
    def analyze_api_endpoints(self) -> Dict[str, Any]:
        """Analyze API endpoint usage statistics."""
        endpoint_stats = defaultdict(lambda: {
            'count': 0,
            'total_latency': 0,
            'min_latency': float('inf'),
            'max_latency': 0,
            'errors': 0,
            'success_rate': 0
        })
        
        for event in self.events:
            model = event.get('input', {}).get('model', 'unknown')
            latency = event.get('latency_ms', 0)
            retry_attempt = event.get('retry_attempt', 0)
            
            # Extract endpoint from model name
            endpoint = model.replace('api-', '').replace('-', '/')
            
            stats = endpoint_stats[endpoint]
            stats['count'] += 1
            stats['total_latency'] += latency
            stats['min_latency'] = min(stats['min_latency'], latency) if latency > 0 else stats['min_latency']
            stats['max_latency'] = max(stats['max_latency'], latency)
            
            if retry_attempt > 0:
                stats['errors'] += 1
        
        # Calculate averages and success rates
        for endpoint, stats in endpoint_stats.items():
            if stats['count'] > 0:
                stats['avg_latency'] = stats['total_latency'] / stats['count']
                stats['success_rate'] = ((stats['count'] - stats['errors']) / stats['count']) * 100
                if stats['min_latency'] == float('inf'):
                    stats['min_latency'] = 0
        
        return dict(endpoint_stats)
    
    def analyze_ai_operations(self) -> Dict[str, Any]:
        """Analyze AI model usage (classification and summarization)."""
        ai_stats = defaultdict(lambda: {
            'count': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_latency': 0,
            'avg_latency': 0
        })
        
        for event in self.events:
            model = event.get('input', {}).get('model', '')
            
            # Filter for AI operations
            if any(ai_model in model for ai_model in ['gemini', 'classifier', 'summarizer']):
                usage = event.get('usage', {})
                input_tokens = usage.get('prompt_tokens', 0)
                output_tokens = usage.get('completion_tokens', 0)
                latency = event.get('latency_ms', 0)
                
                stats = ai_stats[model]
                stats['count'] += 1
                stats['total_input_tokens'] += input_tokens
                stats['total_output_tokens'] += output_tokens
                stats['total_latency'] += latency
        
        # Calculate averages
        for model, stats in ai_stats.items():
            if stats['count'] > 0:
                stats['avg_latency'] = stats['total_latency'] / stats['count']
                stats['avg_input_tokens'] = stats['total_input_tokens'] / stats['count']
                stats['avg_output_tokens'] = stats['total_output_tokens'] / stats['count']
        
        return dict(ai_stats)
    
    def analyze_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze performance trends over the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_events = []
        for event in self.events:
            try:
                event_time = datetime.fromisoformat(event.get('startTime', '').replace('Z', '+00:00'))
                if event_time >= cutoff_time:
                    recent_events.append(event)
            except:
                continue
        
        if not recent_events:
            return {'message': f'No events found in the last {hours} hours'}
        
        # Calculate hourly statistics
        hourly_stats = defaultdict(lambda: {'count': 0, 'total_latency': 0, 'errors': 0})
        
        for event in recent_events:
            try:
                event_time = datetime.fromisoformat(event.get('startTime', '').replace('Z', '+00:00'))
                hour_key = event_time.strftime('%H:00')
                
                stats = hourly_stats[hour_key]
                stats['count'] += 1
                stats['total_latency'] += event.get('latency_ms', 0)
                
                if event.get('retry_attempt', 0) > 0:
                    stats['errors'] += 1
            except:
                continue
        
        # Calculate averages
        for hour, stats in hourly_stats.items():
            if stats['count'] > 0:
                stats['avg_latency'] = stats['total_latency'] / stats['count']
                stats['error_rate'] = (stats['errors'] / stats['count']) * 100
        
        return {
            'period': f'Last {hours} hours',
            'total_events': len(recent_events),
            'hourly_breakdown': dict(hourly_stats)
        }
    
    def print_endpoint_analysis(self):
        """Print API endpoint analysis in a formatted table."""
        stats = self.analyze_api_endpoints()
        
        if RICH_AVAILABLE:
            table = Table(title="API Endpoint Analysis")
            table.add_column("Endpoint", style="cyan")
            table.add_column("Requests", style="green")
            table.add_column("Avg Latency (ms)", style="yellow")
            table.add_column("Min/Max Latency", style="blue")
            table.add_column("Success Rate", style="magenta")
            table.add_column("Errors", style="red")
            
            for endpoint, data in sorted(stats.items(), key=lambda x: x[1]['count'], reverse=True):
                table.add_row(
                    endpoint,
                    str(data['count']),
                    f"{data['avg_latency']:.1f}",
                    f"{data['min_latency']:.0f}/{data['max_latency']:.0f}",
                    f"{data['success_rate']:.1f}%",
                    str(data['errors'])
                )
            
            console.print(table)
        else:
            print("\n=== API Endpoint Analysis ===")
            for endpoint, data in sorted(stats.items(), key=lambda x: x[1]['count'], reverse=True):
                print(f"{endpoint}: {data['count']} requests, {data['avg_latency']:.1f}ms avg, {data['success_rate']:.1f}% success")
    
    def print_ai_analysis(self):
        """Print AI operations analysis."""
        stats = self.analyze_ai_operations()
        
        if RICH_AVAILABLE:
            table = Table(title="AI Operations Analysis")
            table.add_column("Model", style="cyan")
            table.add_column("Operations", style="green")
            table.add_column("Avg Input Tokens", style="yellow")
            table.add_column("Avg Output Tokens", style="blue")
            table.add_column("Avg Latency (ms)", style="magenta")
            
            for model, data in sorted(stats.items(), key=lambda x: x[1]['count'], reverse=True):
                table.add_row(
                    model,
                    str(data['count']),
                    f"{data.get('avg_input_tokens', 0):.1f}",
                    f"{data.get('avg_output_tokens', 0):.1f}",
                    f"{data['avg_latency']:.1f}"
                )
            
            console.print(table)
        else:
            print("\n=== AI Operations Analysis ===")
            for model, data in sorted(stats.items(), key=lambda x: x[1]['count'], reverse=True):
                print(f"{model}: {data['count']} ops, {data['avg_latency']:.1f}ms avg")
    
    def print_performance_trends(self, hours: int = 24):
        """Print performance trends analysis."""
        trends = self.analyze_performance_trends(hours)
        
        if 'message' in trends:
            console.print(f"[yellow]{trends['message']}[/yellow]")
            return
        
        if RICH_AVAILABLE:
            table = Table(title=f"Performance Trends - {trends['period']}")
            table.add_column("Hour", style="cyan")
            table.add_column("Requests", style="green")
            table.add_column("Avg Latency (ms)", style="yellow")
            table.add_column("Error Rate", style="red")
            
            for hour, data in sorted(trends['hourly_breakdown'].items()):
                table.add_row(
                    hour,
                    str(data['count']),
                    f"{data['avg_latency']:.1f}",
                    f"{data['error_rate']:.1f}%"
                )
            
            console.print(table)
        else:
            print(f"\n=== Performance Trends - {trends['period']} ===")
            for hour, data in sorted(trends['hourly_breakdown'].items()):
                print(f"{hour}: {data['count']} requests, {data['avg_latency']:.1f}ms avg, {data['error_rate']:.1f}% errors")
    
    def print_summary(self):
        """Print overall summary statistics."""
        total_events = len(self.events)
        
        if total_events == 0:
            console.print("[yellow]No events found in log file[/yellow]")
            return
        
        # Calculate overall stats
        total_latency = sum(event.get('latency_ms', 0) for event in self.events)
        avg_latency = total_latency / total_events if total_events > 0 else 0
        
        errors = sum(1 for event in self.events if event.get('retry_attempt', 0) > 0)
        success_rate = ((total_events - errors) / total_events) * 100 if total_events > 0 else 0
        
        # Get time range
        timestamps = []
        for event in self.events:
            try:
                ts = datetime.fromisoformat(event.get('startTime', '').replace('Z', '+00:00'))
                timestamps.append(ts)
            except:
                continue
        
        time_range = ""
        if timestamps:
            timestamps.sort()
            start_time = timestamps[0].strftime('%Y-%m-%d %H:%M:%S')
            end_time = timestamps[-1].strftime('%Y-%m-%d %H:%M:%S')
            time_range = f"{start_time} to {end_time}"
        
        if RICH_AVAILABLE:
            summary_text = f"""
[green]Total Events:[/green] {total_events:,}
[yellow]Average Latency:[/yellow] {avg_latency:.1f}ms
[blue]Success Rate:[/blue] {success_rate:.1f}%
[red]Total Errors:[/red] {errors}
[cyan]Time Range:[/cyan] {time_range}
            """.strip()
            
            panel = Panel(summary_text, title="📊 API Usage Summary", border_style="blue")
            console.print(panel)
        else:
            print("\n=== API Usage Summary ===")
            print(f"Total Events: {total_events:,}")
            print(f"Average Latency: {avg_latency:.1f}ms")
            print(f"Success Rate: {success_rate:.1f}%")
            print(f"Total Errors: {errors}")
            print(f"Time Range: {time_range}")


@click.command()
@click.argument('log_file', type=click.Path(exists=True), default='logs/api_calls.jsonl')
@click.option('--summary', is_flag=True, help='Show summary statistics')
@click.option('--endpoints', is_flag=True, help='Show endpoint analysis')
@click.option('--ai-ops', is_flag=True, help='Show AI operations analysis')
@click.option('--trends', is_flag=True, help='Show performance trends')
@click.option('--hours', default=24, help='Hours to analyze for trends (default: 24)')
@click.option('--all', 'show_all', is_flag=True, help='Show all analyses')
def analyze_logs(log_file, summary, endpoints, ai_ops, trends, hours, show_all):
    """Analyze API logs from the AI Email Categorizer backend."""
    
    analyzer = APILogAnalyzer(log_file)
    
    if not analyzer.events:
        console.print("[red]No events found in log file[/red]")
        return
    
    # Show all analyses if --all flag is used or no specific flags are provided
    if show_all or not any([summary, endpoints, ai_ops, trends]):
        analyzer.print_summary()
        print()
        analyzer.print_endpoint_analysis()
        print()
        analyzer.print_ai_analysis()
        print()
        analyzer.print_performance_trends(hours)
    else:
        if summary:
            analyzer.print_summary()
        if endpoints:
            analyzer.print_endpoint_analysis()
        if ai_ops:
            analyzer.print_ai_analysis()
        if trends:
            analyzer.print_performance_trends(hours)


if __name__ == '__main__':
    analyze_logs()
