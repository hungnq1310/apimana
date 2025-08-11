#!/usr/bin/env python3
"""
Benchmark Results Analysis Utilities

This module provides tools for analyzing and visualizing benchmark results
from Locust performance tests.
"""

import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

try:
    import pandas as pd
    import matplotlib.pyplot as plt
    ANALYSIS_AVAILABLE = True
except ImportError:
    ANALYSIS_AVAILABLE = False
    logger.warning("pandas and matplotlib not available. Install with: pip install pandas matplotlib")


class ResultsAnalyzer:
    """Analyze benchmark results and generate reports"""
    
    def __init__(self, results_dir: Optional[str] = None):
        """
        Initialize the analyzer
        
        Args:
            results_dir: Path to results directory, defaults to ./results
        """
        if results_dir is None:
            results_dir = str(Path(__file__).parent.parent / "results")
        self.results_dir = Path(results_dir)
        
        if not self.results_dir.exists():
            logger.warning(f"Results directory does not exist: {self.results_dir}")
    
    def list_results(self) -> List[Dict[str, Any]]:
        """
        List all available benchmark results
        
        Returns:
            List of result information dictionaries
        """
        results = []
        
        # Find all CSV stats files
        csv_files = list(self.results_dir.glob("*_stats.csv"))
        
        for csv_file in csv_files:
            try:
                # Parse filename to extract info
                filename = csv_file.stem
                parts = filename.replace("_stats", "").split("_")
                
                if len(parts) >= 3:
                    test_type = parts[1]
                    timestamp = "_".join(parts[2:])
                    
                    # Check if HTML report exists
                    html_file = csv_file.parent / f"{filename.replace('_stats', '')}.html"
                    
                    result_info = {
                        "test_type": test_type,
                        "timestamp": timestamp,
                        "csv_file": str(csv_file),
                        "html_file": str(html_file) if html_file.exists() else None,
                        "date": self._parse_timestamp(timestamp),
                        "file_size": csv_file.stat().st_size
                    }
                    
                    results.append(result_info)
                    
            except Exception as e:
                logger.error(f"Error parsing {csv_file}: {e}")
        
        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x["timestamp"], reverse=True)
        return results
    
    def _parse_timestamp(self, timestamp: str) -> Optional[datetime]:
        """Parse timestamp from filename"""
        try:
            return datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
        except ValueError:
            try:
                # Try alternative format
                return datetime.strptime(timestamp, "%Y%m%d_%H%M")
            except ValueError:
                logger.warning(f"Could not parse timestamp: {timestamp}")
                return None
    
    def analyze_result(self, csv_file: str) -> Dict[str, Any]:
        """
        Analyze a single benchmark result
        
        Args:
            csv_file: Path to the CSV results file
            
        Returns:
            Analysis results dictionary
        """
        analysis = {
            "file": csv_file,
            "summary": {},
            "endpoints": [],
            "errors": []
        }
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    name = row.get('Name', '')
                    
                    if name in ['Aggregated', 'Total']:
                        # Overall summary
                        analysis["summary"] = self._extract_summary(row)
                    else:
                        # Individual endpoint
                        endpoint_data = self._extract_endpoint_data(row)
                        if endpoint_data:
                            analysis["endpoints"].append(endpoint_data)
                        
        except Exception as e:
            analysis["error"] = str(e)
            logger.error(f"Error analyzing {csv_file}: {e}")
        
        return analysis
    
    def _extract_summary(self, row: Dict[str, str]) -> Dict[str, float]:
        """Extract summary metrics from CSV row"""
        return {
            "total_requests": int(row.get('Request Count', 0)),
            "failed_requests": int(row.get('Failure Count', 0)),
            "failure_rate": self._safe_divide(
                float(row.get('Failure Count', 0)), 
                float(row.get('Request Count', 1))
            ) * 100,
            "avg_response_time": float(row.get('Average Response Time', 0)),
            "min_response_time": float(row.get('Min Response Time', 0)),
            "max_response_time": float(row.get('Max Response Time', 0)),
            "requests_per_second": float(row.get('Requests/s', 0)),
            "median_response_time": float(row.get('Median Response Time', 0)),
            "percentile_95": float(row.get('95%ile', 0))
        }
    
    def _extract_endpoint_data(self, row: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Extract endpoint data from CSV row"""
        try:
            return {
                "name": row.get('Name', ''),
                "method": row.get('Type', 'Unknown'),
                "requests": int(row.get('Request Count', 0)),
                "failures": int(row.get('Failure Count', 0)),
                "failure_rate": self._safe_divide(
                    float(row.get('Failure Count', 0)), 
                    float(row.get('Request Count', 1))
                ) * 100,
                "avg_response_time": float(row.get('Average Response Time', 0)),
                "requests_per_second": float(row.get('Requests/s', 0)),
                "min_response_time": float(row.get('Min Response Time', 0)),
                "max_response_time": float(row.get('Max Response Time', 0))
            }
        except (ValueError, TypeError):
            logger.warning(f"Could not parse endpoint data for: {row.get('Name', 'Unknown')}")
            return None
    
    def _safe_divide(self, numerator: float, denominator: float) -> float:
        """Safely divide two numbers, returning 0 if denominator is 0"""
        return numerator / denominator if denominator != 0 else 0
    
    def generate_report(self, result_info: Dict[str, Any]) -> str:
        """
        Generate a text report for a benchmark result
        
        Args:
            result_info: Result information dictionary
            
        Returns:
            Formatted text report
        """
        analysis = self.analyze_result(result_info["csv_file"])
        
        report = []
        report.append("📊 Benchmark Report")
        report.append("=" * 50)
        report.append(f"Test Type: {result_info['test_type']}")
        report.append(f"Timestamp: {result_info['timestamp']}")
        if result_info['date']:
            report.append(f"Date: {result_info['date'].strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        if "error" in analysis:
            report.append(f"❌ Error analyzing results: {analysis['error']}")
            return "\n".join(report)
        
        # Summary
        summary = analysis["summary"]
        if summary:
            report.extend(self._generate_summary_section(summary))
        
        # Top endpoints
        endpoints = analysis["endpoints"]
        if endpoints:
            report.extend(self._generate_endpoints_section(endpoints))
        
        return "\n".join(report)
    
    def _generate_summary_section(self, summary: Dict[str, float]) -> List[str]:
        """Generate summary section of the report"""
        section = []
        section.append("📈 Overall Performance")
        section.append("-" * 30)
        section.append(f"Total Requests: {summary.get('total_requests', 0):,}")
        section.append(f"Failed Requests: {summary.get('failed_requests', 0):,}")
        section.append(f"Failure Rate: {summary.get('failure_rate', 0):.2f}%")
        section.append(f"Requests/sec: {summary.get('requests_per_second', 0):.2f}")
        section.append(f"Avg Response Time: {summary.get('avg_response_time', 0):.2f}ms")
        section.append(f"Min Response Time: {summary.get('min_response_time', 0):.2f}ms")
        section.append(f"Max Response Time: {summary.get('max_response_time', 0):.2f}ms")
        
        if summary.get('percentile_95'):
            section.append(f"95th Percentile: {summary.get('percentile_95', 0):.2f}ms")
        
        section.append("")
        
        # Performance rating
        rating = self._calculate_performance_rating(summary)
        section.append(f"Performance Rating: {rating}")
        section.append("")
        
        return section
    
    def _generate_endpoints_section(self, endpoints: List[Dict[str, Any]]) -> List[str]:
        """Generate endpoints section of the report"""
        section = []
        section.append("🎯 Top Endpoints by Request Count")
        section.append("-" * 40)
        
        sorted_endpoints = sorted(endpoints, key=lambda x: x["requests"], reverse=True)[:5]
        
        for endpoint in sorted_endpoints:
            section.append(f"{endpoint['method']} {endpoint['name']}")
            section.append(f"  Requests: {endpoint['requests']:,}")
            section.append(f"  Failures: {endpoint['failures']:,} ({endpoint['failure_rate']:.1f}%)")
            section.append(f"  RPS: {endpoint['requests_per_second']:.2f}")
            section.append(f"  Avg Time: {endpoint['avg_response_time']:.2f}ms")
            section.append("")
        
        return section
    
    def _calculate_performance_rating(self, summary: Dict[str, float]) -> str:
        """Calculate performance rating based on metrics"""
        rps = summary.get('requests_per_second', 0)
        avg_time = summary.get('avg_response_time', 0)
        failure_rate = summary.get('failure_rate', 0)
        
        if rps > 100 and avg_time < 200 and failure_rate < 1:
            return "🟢 Excellent"
        elif rps > 50 and avg_time < 500 and failure_rate < 5:
            return "🟡 Good"
        elif rps > 20 and avg_time < 1000 and failure_rate < 10:
            return "🟠 Fair"
        else:
            return "🔴 Poor"
    
    def compare_results(self, result_files: List[str]) -> str:
        """
        Compare multiple benchmark results
        
        Args:
            result_files: List of CSV file paths to compare
            
        Returns:
            Formatted comparison report
        """
        if not result_files:
            return "No results to compare"
        
        comparisons = []
        
        for file in result_files:
            analysis = self.analyze_result(file)
            if "summary" in analysis and analysis["summary"]:
                comparisons.append({
                    "file": Path(file).stem,
                    **analysis["summary"]
                })
        
        if not comparisons:
            return "No valid results to compare"
        
        return self._generate_comparison_report(comparisons)
    
    def _generate_comparison_report(self, comparisons: List[Dict[str, Any]]) -> str:
        """Generate comparison report"""
        report = []
        report.append("📊 Benchmark Comparison")
        report.append("=" * 80)
        
        # Headers
        headers = ["Test", "Total Req", "Failed", "Failure %", "RPS", "Avg Time (ms)"]
        report.append(f"{headers[0]:<25} {headers[1]:<12} {headers[2]:<8} {headers[3]:<10} {headers[4]:<8} {headers[5]:<12}")
        report.append("-" * 80)
        
        # Data rows
        for comp in comparisons:
            test_name = comp["file"][:23]
            total_req = f"{comp['total_requests']:,}"[:10]
            failed = f"{comp['failed_requests']:,}"[:6]
            failure_rate = f"{comp['failure_rate']:.1f}%"
            rps = f"{comp['requests_per_second']:.1f}"
            avg_time = f"{comp['avg_response_time']:.1f}"
            
            report.append(f"{test_name:<25} {total_req:<12} {failed:<8} {failure_rate:<10} {rps:<8} {avg_time:<12}")
        
        return "\n".join(report)
    
    def get_latest_result(self) -> Optional[Dict[str, Any]]:
        """Get the latest benchmark result"""
        results = self.list_results()
        return results[0] if results else None


def main():
    """CLI for results analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark Results Analyzer")
    parser.add_argument("--results-dir", help="Results directory path")
    parser.add_argument("--list", action="store_true", help="List all available results")
    parser.add_argument("--analyze", help="Analyze specific result file")
    parser.add_argument("--report", help="Generate report for result (by timestamp)")
    parser.add_argument("--compare", nargs="+", help="Compare multiple results")
    parser.add_argument("--latest", action="store_true", help="Analyze latest result")
    
    args = parser.parse_args()
    
    analyzer = ResultsAnalyzer(args.results_dir)
    
    if args.list:
        results = analyzer.list_results()
        if not results:
            print("No benchmark results found.")
            return
        
        print("📋 Available Benchmark Results:")
        print("-" * 70)
        print(f"{'Type':<15} {'Timestamp':<20} {'Date':<20} {'Size':<10}")
        print("-" * 70)
        
        for result in results:
            date_str = result["date"].strftime("%Y-%m-%d %H:%M") if result["date"] else "Unknown"
            size_str = f"{result['file_size']:,}B" if result['file_size'] else "Unknown"
            print(f"{result['test_type']:<15} {result['timestamp']:<20} {date_str:<20} {size_str:<10}")
        
    elif args.analyze:
        if Path(args.analyze).exists():
            analysis = analyzer.analyze_result(args.analyze)
            print(json.dumps(analysis, indent=2))
        else:
            print(f"File not found: {args.analyze}")
    
    elif args.report:
        results = analyzer.list_results()
        target_result = None
        
        for result in results:
            if args.report in result["timestamp"] or args.report == result["test_type"]:
                target_result = result
                break
        
        if target_result:
            report = analyzer.generate_report(target_result)
            print(report)
        else:
            print(f"Result not found: {args.report}")
    
    elif args.latest:
        latest = analyzer.get_latest_result()
        if latest:
            report = analyzer.generate_report(latest)
            print(report)
        else:
            print("No results found.")
    
    elif args.compare:
        comparison = analyzer.compare_results(args.compare)
        print(comparison)
    
    else:
        # Default: show latest result
        latest = analyzer.get_latest_result()
        if latest:
            print("🔍 Latest Benchmark Result:")
            print("")
            report = analyzer.generate_report(latest)
            print(report)
        else:
            print("No benchmark results found. Run a benchmark first!")


if __name__ == "__main__":
    main()
