import json
import time
from typing import Any


class JsonLogger:
    def __init__(self) -> None:
        pass

    def log(self, **kwargs: Any) -> None:
        # Ensure consistent serialization for CloudWatch Logs
        print(json.dumps(kwargs, separators=(",", ":"), default=str))

    def log_emf(
        self,
        *,
        namespace: str,
        dimensions: dict[str, str],
        metrics: dict[str, tuple[float, str]],
        fields: dict[str, Any],
    ) -> None:
        metric_defs = []
        for name, (_, unit) in metrics.items():
            metric_defs.append({"Name": name, "Unit": unit})

        payload = {
            "_aws": {
                "Timestamp": int(time.time() * 1000),
                "CloudWatchMetrics": [
                    {
                        "Namespace": namespace,
                        "Dimensions": [list(dimensions.keys())],
                        "Metrics": metric_defs,
                    }
                ],
            },
            **dimensions,
            **fields,
        }

        for name, (value, _) in metrics.items():
            payload[name] = value

        print(json.dumps(payload, separators=(",", ":"), default=str))


def timing_ms(start_time: float) -> int:
    return int((time.time() - start_time) * 1000)
