"""
Performance and Latency Tracker for GRL USB PD C2 UI Automation.
"""
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import orjson

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

@dataclass
class MetricRecord:
    panel_name: str
    duration_s: float
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

class PerformanceTracker:
    def __init__(self) -> None:
        self.records: list[MetricRecord] = []

    def record_panel_load(self, panel_name: str, duration_s: float, **kwargs: Any) -> None:
        self.records.append(MetricRecord(panel_name, duration_s, metadata=kwargs))

    def export_metrics(self, output_path: Path | None = None) -> Path:
        if output_path is None:
            output_path = ROOT_DIR / "Reports" / "performance_metrics.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = [
            {
                "panel": r.panel_name,
                "duration_seconds": round(r.duration_s, 4),
                "timestamp": r.timestamp,
                "metadata": r.metadata
            }
            for r in self.records
        ]
        with open(output_path, "wb") as f:
            f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
        return output_path

perf_tracker = PerformanceTracker()
