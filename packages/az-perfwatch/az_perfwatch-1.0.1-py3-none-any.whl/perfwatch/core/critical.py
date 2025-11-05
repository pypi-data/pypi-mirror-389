from perfwatch.core.profiler import FunctionProfile
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class CriticalAnalyzer:
    """
    Analyze FunctionProfile objects to detect critical functions and queries
    based on thresholds defined in configuration.
    """

    def __init__(self, function_threshold_ms: float = 100, query_threshold_ms: float = 50):
        self.function_threshold_ms = function_threshold_ms
        self.query_threshold_ms = query_threshold_ms

    def analyze(self, root_profile: FunctionProfile) -> Dict[str, List[Dict]]:
        """
        Analyze the FunctionProfile tree and return critical functions and queries.
        Returns:
            {
                "functions": [
                    {"name": "func_name", "time_ms": 123.4, "path": "parent->child->func_name"}
                ],
                "queries": [
                    {"sql": "SELECT ...", "time_ms": 45.3, "function": "func_name"}
                ]
            }
        """
        critical_functions = []
        critical_queries = []

        def _traverse(profile: FunctionProfile, path=""):
            current_path = f"{path}->{profile.func_name}" if path else profile.func_name

            if profile.duration_ms >= self.function_threshold_ms:
                critical_functions.append({
                    "name": profile.func_name,
                    "time_ms": profile.duration_ms,
                    "path": current_path
                })

            for q in profile.queries:
                if q["time_ms"] >= self.query_threshold_ms:
                    critical_queries.append({
                        "sql": q.get("sql", "N/A"),
                        "time_ms": q["time_ms"],
                        "function": profile.func_name,
                        "path": current_path
                    })

            for child in profile.children:
                _traverse(child, current_path)

        _traverse(root_profile)
        return {"functions": critical_functions, "queries": critical_queries}
    
    @classmethod
    def get_report(cls, func_thresh=None, query_thresh=None) -> str:
        """
        Get current runtime profiling report as a formatted string.
        """
        # Use profiler module to obtain the current root profile
        from perfwatch.core.profiler import get_root
        root = get_root()
        if root is None:
            return "No profiling data available."

        analyzer = cls(function_threshold_ms=func_thresh or 100, query_threshold_ms=query_thresh or 50)
        result = analyzer.analyze(root)

        lines = ["\n=== Critical Functions ==="]
        for f in result["functions"]:
            lines.append(f"{f['path']}: {f['time_ms']:.2f}ms")

        lines.append("\n=== Critical Queries ===")
        for q in result["queries"]:
            lines.append(f"{q['path']}: {q['sql']} ({q['time_ms']:.2f}ms)")

        return "\n".join(lines)


# Example helper function for CLI / dashboard
def print_critical(profile: FunctionProfile, func_thresh=100, query_thresh=50):
    analyzer = CriticalAnalyzer(func_thresh, query_thresh)
    result = analyzer.analyze(profile)

    logger.info("\n=== Critical Functions ===")
    for f in result["functions"]:
        logger.info("%s: %.2fms", f['path'], f['time_ms'])

    logger.info("\n=== Critical Queries ===")
    for q in result["queries"]:
        logger.info("%s: %s (%.2fms)", q['path'], q['sql'], q['time_ms'])
