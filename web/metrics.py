import math
from collections import Counter


def percentile(values, pct) -> float | None:
    if not values:
        return None

    ordered = sorted(values)

    rank = math.ceil(pct / 100 * len(ordered))
    rank = max(1, rank)

    return ordered[rank - 1]


def summarize(store) -> dict:
    records = list(store)
    total = len(records)

    if total == 0:
        return {"total": 0}

    durations = [r["duration_ms"] for r in records]

    ttfts = [
        r["ttft_ms"]
        for r in records
        if r["ttft_ms"] is not None
    ]

    outcomes = Counter(r["outcome"] for r in records)

    error_rate = (
        outcomes["error"] + outcomes["timeout"]
    ) / total

    avg_tool_calls = (
        sum(r["tool_calls"] for r in records) / total
    )

    return {
        "total": total,
        "outcomes": dict(outcomes),
        "error_rate": round(error_rate, 3),
        "latency_p50_ms": percentile(durations, 50),
        "latency_p95_ms": percentile(durations, 95),
        "ttft_p50_ms": percentile(ttfts, 50),
        "ttft_p95_ms": percentile(ttfts, 95),
        "avg_tool_calls": round(avg_tool_calls, 2)
    }
