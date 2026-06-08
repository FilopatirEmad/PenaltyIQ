#!/usr/bin/env python3
"""
Backend stress tester for PenaltyIQ.

What it does:
1) Concurrently tests /process-video -> /analyze flow with virtual users.
2) Tracks latency, throughput, success/error rate.
3) Runs edge-case tests (missing fields, invalid zone, corrupted video, large file).
4) Optionally samples host CPU/memory usage during test windows.

This script is black-box: it only uses public HTTP endpoints.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import statistics
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import httpx

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover
    psutil = None


VALID_ZONES = ("T1", "T2", "T3", "T4", "B1", "B2", "B3", "B4")


@dataclass
class RequestRecord:
    endpoint: str
    ok: bool
    status_code: int
    latency_s: float
    error: Optional[str] = None
    size_bytes: int = 0


@dataclass
class EndpointStats:
    endpoint: str
    total: int = 0
    ok: int = 0
    failed: int = 0
    latencies_s: list[float] = field(default_factory=list)

    def add(self, record: RequestRecord) -> None:
        self.total += 1
        if record.ok:
            self.ok += 1
        else:
            self.failed += 1
        self.latencies_s.append(record.latency_s)

    def as_dict(self, elapsed_s: float) -> dict[str, Any]:
        if not self.latencies_s:
            return {
                "endpoint": self.endpoint,
                "total": 0,
                "ok": 0,
                "failed": 0,
                "success_rate_pct": 0.0,
                "error_rate_pct": 0.0,
                "avg_ms": 0.0,
                "p95_ms": 0.0,
                "max_ms": 0.0,
                "throughput_rps": 0.0,
            }
        p95 = _percentile(self.latencies_s, 95)
        avg = statistics.mean(self.latencies_s)
        mx = max(self.latencies_s)
        return {
            "endpoint": self.endpoint,
            "total": self.total,
            "ok": self.ok,
            "failed": self.failed,
            "success_rate_pct": round(self.ok * 100.0 / self.total, 2),
            "error_rate_pct": round(self.failed * 100.0 / self.total, 2),
            "avg_ms": round(avg * 1000.0, 2),
            "p95_ms": round(p95 * 1000.0, 2),
            "max_ms": round(mx * 1000.0, 2),
            "throughput_rps": round(self.total / max(elapsed_s, 1e-9), 3),
        }


@dataclass
class SystemSample:
    timestamp_s: float
    cpu_pct: float
    mem_pct: float
    rss_mb: Optional[float] = None


class StressHarness:
    def __init__(
        self,
        base_url: str,
        video_path: Path,
        users: int,
        iterations_per_user: int,
        timeout_s: float,
        goal_zone: str,
        max_connections: int,
        monitor_pid: Optional[int],
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.video_path = video_path
        self.users = users
        self.iterations_per_user = iterations_per_user
        self.timeout_s = timeout_s
        self.goal_zone = goal_zone
        self.max_connections = max_connections
        self.monitor_pid = monitor_pid

        self.records: list[RequestRecord] = []
        self.system_samples: list[SystemSample] = []
        self._system_monitor_running = False
        self._process_handle = None
        if psutil is not None and monitor_pid is not None:
            try:
                self._process_handle = psutil.Process(monitor_pid)
            except Exception:
                self._process_handle = None

    async def run(self) -> dict[str, Any]:
        video_bytes = self.video_path.read_bytes()
        limits = httpx.Limits(max_keepalive_connections=self.max_connections, max_connections=self.max_connections)
        timeout = httpx.Timeout(self.timeout_s)

        start = time.perf_counter()
        monitor_task = asyncio.create_task(self._monitor_system()) if psutil is not None else None

        async with httpx.AsyncClient(base_url=self.base_url, timeout=timeout, limits=limits) as client:
            sem = asyncio.Semaphore(self.users)
            tasks = [
                asyncio.create_task(self._user_flow(client, sem, user_id, iter_idx, video_bytes))
                for user_id in range(self.users)
                for iter_idx in range(self.iterations_per_user)
            ]
            await asyncio.gather(*tasks)

        elapsed = time.perf_counter() - start
        self._system_monitor_running = False
        if monitor_task is not None:
            await monitor_task

        return self._build_report(elapsed)

    async def _user_flow(
        self,
        client: httpx.AsyncClient,
        semaphore: asyncio.Semaphore,
        user_id: int,
        iter_idx: int,
        video_bytes: bytes,
    ) -> None:
        async with semaphore:
            session_id = str(uuid.uuid4())
            process_record, process_payload = await self._call_process_video(
                client=client,
                video_bytes=video_bytes,
                session_id=session_id,
                goal_zone=self.goal_zone,
            )
            self.records.append(process_record)
            if not process_record.ok:
                return

            analyze_record = await self._call_analyze(
                client=client,
                process_payload=process_payload,
                session_id=session_id,
                goal_zone=self.goal_zone,
            )
            self.records.append(analyze_record)

    async def _call_process_video(
        self,
        client: httpx.AsyncClient,
        video_bytes: bytes,
        session_id: str,
        goal_zone: str,
    ) -> tuple[RequestRecord, Optional[dict[str, Any]]]:
        t0 = time.perf_counter()
        try:
            files = {
                "video": (self.video_path.name, video_bytes, "video/mp4"),
            }
            data = {
                "session_id": session_id,
                "goal_zone": goal_zone,
                "mode": "full",
            }
            resp = await client.post("/api/v1/process-video", files=files, data=data)
            latency = time.perf_counter() - t0
            ok = resp.status_code == 200
            payload = resp.json() if ok else None
            return (
                RequestRecord(
                    endpoint="/process-video",
                    ok=ok,
                    status_code=resp.status_code,
                    latency_s=latency,
                    error=None if ok else _safe_json(resp),
                    size_bytes=len(video_bytes),
                ),
                payload,
            )
        except Exception as exc:
            latency = time.perf_counter() - t0
            return (
                RequestRecord(
                    endpoint="/process-video",
                    ok=False,
                    status_code=0,
                    latency_s=latency,
                    error=repr(exc),
                    size_bytes=len(video_bytes),
                ),
                None,
            )

    async def _call_analyze(
        self,
        client: httpx.AsyncClient,
        process_payload: Optional[dict[str, Any]],
        session_id: str,
        goal_zone: str,
    ) -> RequestRecord:
        t0 = time.perf_counter()
        try:
            if process_payload is None:
                raise ValueError("Missing process payload")

            cal = process_payload.get("calibration", {}) or {}
            seg = cal.get("segments_m", {}) or {}
            analyze_req = {
                "session_id": session_id,
                "goal_zone": goal_zone,
                "fps": process_payload.get("fps", 60.0),
                "contact_frame_index": process_payload.get("contact_frame_index"),
                "calibration": {
                    "scale_m_per_px": cal["scale_m_per_px"],
                    "thigh_m": seg["thigh_m"],
                    "shank_m": seg["shank_m"],
                    "trunk_m": seg["trunk_m"],
                    "leg_m": seg["leg_m"],
                },
                "frames": process_payload.get("analysis_frames", []),
            }

            resp = await client.post("/api/v1/analyze", json=analyze_req)
            latency = time.perf_counter() - t0
            ok = resp.status_code == 200
            return RequestRecord(
                endpoint="/analyze",
                ok=ok,
                status_code=resp.status_code,
                latency_s=latency,
                error=None if ok else _safe_json(resp),
            )
        except Exception as exc:
            latency = time.perf_counter() - t0
            return RequestRecord(
                endpoint="/analyze",
                ok=False,
                status_code=0,
                latency_s=latency,
                error=repr(exc),
            )

    async def _monitor_system(self) -> None:
        self._system_monitor_running = True
        while self._system_monitor_running:
            try:
                cpu = psutil.cpu_percent(interval=None) if psutil is not None else 0.0
                mem = psutil.virtual_memory().percent if psutil is not None else 0.0
                rss_mb = None
                if self._process_handle is not None:
                    rss_mb = self._process_handle.memory_info().rss / (1024 * 1024)
                self.system_samples.append(
                    SystemSample(
                        timestamp_s=time.time(),
                        cpu_pct=float(cpu),
                        mem_pct=float(mem),
                        rss_mb=rss_mb,
                    )
                )
            except Exception:
                pass
            await asyncio.sleep(1.0)

    def _build_report(self, elapsed_s: float) -> dict[str, Any]:
        per_endpoint: dict[str, EndpointStats] = {}
        for rec in self.records:
            per_endpoint.setdefault(rec.endpoint, EndpointStats(endpoint=rec.endpoint)).add(rec)

        endpoint_rows = [stats.as_dict(elapsed_s) for stats in sorted(per_endpoint.values(), key=lambda s: s.endpoint)]
        total = len(self.records)
        failed = sum(1 for r in self.records if not r.ok)
        success = total - failed
        lats = [r.latency_s for r in self.records]
        report = {
            "config": {
                "base_url": self.base_url,
                "users": self.users,
                "iterations_per_user": self.iterations_per_user,
                "total_flows": self.users * self.iterations_per_user,
                "video_path": str(self.video_path),
                "video_size_mb": round(self.video_path.stat().st_size / 1_000_000, 3),
                "timeout_s": self.timeout_s,
                "max_connections": self.max_connections,
            },
            "overall": {
                "elapsed_s": round(elapsed_s, 3),
                "total_requests": total,
                "success_requests": success,
                "failed_requests": failed,
                "success_rate_pct": round((success * 100.0 / total) if total else 0.0, 2),
                "error_rate_pct": round((failed * 100.0 / total) if total else 0.0, 2),
                "avg_ms": round(statistics.mean(lats) * 1000.0, 2) if lats else 0.0,
                "p95_ms": round(_percentile(lats, 95) * 1000.0, 2) if lats else 0.0,
                "max_ms": round(max(lats) * 1000.0, 2) if lats else 0.0,
                "throughput_rps": round(total / max(elapsed_s, 1e-9), 3),
            },
            "per_endpoint": endpoint_rows,
            "resource_summary": _summarize_system_samples(self.system_samples),
            "top_errors": _top_errors(self.records),
            "bottleneck_hints": _infer_bottlenecks(
                endpoint_rows=endpoint_rows,
                system_summary=_summarize_system_samples(self.system_samples),
            ),
        }
        return report


async def run_edge_cases(
    base_url: str,
    valid_video_path: Path,
    timeout_s: float,
    large_video_path: Optional[Path],
) -> dict[str, Any]:
    video_bytes = valid_video_path.read_bytes()
    timeout = httpx.Timeout(timeout_s)
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=10)
    results: list[dict[str, Any]] = []

    async with httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout, limits=limits) as client:
        # 1) Missing fields on /process-video
        files = {"video": (valid_video_path.name, video_bytes, "video/mp4")}
        resp = await client.post("/api/v1/process-video", files=files, data={"goal_zone": "T1"})
        results.append(_edge_record("missing_session_id", "/process-video", resp))

        # 2) Corrupted video on /process-video
        corrupted = b"not-a-real-video-stream"
        files_corrupt = {"video": ("corrupted.mp4", corrupted, "video/mp4")}
        data_ok = {"session_id": str(uuid.uuid4()), "goal_zone": "T1", "mode": "full"}
        resp = await client.post("/api/v1/process-video", files=files_corrupt, data=data_ok)
        results.append(_edge_record("corrupted_video", "/process-video", resp))

        # 3) Invalid zone on /analyze (without valid frame payload, checks schema guard)
        invalid_analyze_payload = {
            "session_id": str(uuid.uuid4()),
            "goal_zone": "X9",
            "fps": 60.0,
            "calibration": {
                "scale_m_per_px": 0.001,
                "thigh_m": 0.4,
                "shank_m": 0.4,
                "trunk_m": 0.5,
                "leg_m": 0.8,
            },
            "frames": [],
        }
        resp = await client.post("/api/v1/analyze", json=invalid_analyze_payload)
        results.append(_edge_record("invalid_zone", "/analyze", resp))

        # 4) Missing fields on /analyze
        resp = await client.post("/api/v1/analyze", json={"session_id": str(uuid.uuid4())})
        results.append(_edge_record("missing_fields_analyze", "/analyze", resp))

        # 5) Large file on /process-video
        if large_video_path is not None and large_video_path.exists():
            lb = large_video_path.read_bytes()
            files_large = {"video": (large_video_path.name, lb, "video/mp4")}
            resp = await client.post(
                "/api/v1/process-video",
                files=files_large,
                data={"session_id": str(uuid.uuid4()), "goal_zone": "T1", "mode": "full"},
            )
            results.append(_edge_record("large_video_file", "/process-video", resp))
        else:
            results.append(
                {
                    "case": "large_video_file",
                    "endpoint": "/process-video",
                    "status_code": None,
                    "ok": False,
                    "detail": "Skipped: provide --large-video-path to run this case.",
                }
            )

    return {"edge_cases": results}


def _edge_record(case: str, endpoint: str, response: httpx.Response) -> dict[str, Any]:
    return {
        "case": case,
        "endpoint": endpoint,
        "status_code": response.status_code,
        "ok": response.status_code < 400,
        "detail": _safe_json(response),
    }


def _safe_json(resp: httpx.Response) -> str:
    try:
        return json.dumps(resp.json(), ensure_ascii=True)
    except Exception:
        return resp.text[:300]


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * (pct / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def _top_errors(records: list[RequestRecord], limit: int = 8) -> list[dict[str, Any]]:
    bucket: dict[str, int] = {}
    for rec in records:
        if rec.ok:
            continue
        key = f"{rec.endpoint}|{rec.status_code}|{rec.error or 'unknown'}"
        bucket[key] = bucket.get(key, 0) + 1
    ranked = sorted(bucket.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    return [{"signature": k, "count": v} for k, v in ranked]


def _summarize_system_samples(samples: list[SystemSample]) -> dict[str, Any]:
    if not samples:
        return {
            "samples": 0,
            "cpu_avg_pct": None,
            "cpu_peak_pct": None,
            "mem_avg_pct": None,
            "mem_peak_pct": None,
            "rss_avg_mb": None,
            "rss_peak_mb": None,
            "note": "psutil unavailable or monitoring disabled",
        }
    cpus = [s.cpu_pct for s in samples]
    mems = [s.mem_pct for s in samples]
    rss_vals = [s.rss_mb for s in samples if s.rss_mb is not None]
    return {
        "samples": len(samples),
        "cpu_avg_pct": round(statistics.mean(cpus), 2),
        "cpu_peak_pct": round(max(cpus), 2),
        "mem_avg_pct": round(statistics.mean(mems), 2),
        "mem_peak_pct": round(max(mems), 2),
        "rss_avg_mb": round(statistics.mean(rss_vals), 2) if rss_vals else None,
        "rss_peak_mb": round(max(rss_vals), 2) if rss_vals else None,
    }


def _infer_bottlenecks(endpoint_rows: list[dict[str, Any]], system_summary: dict[str, Any]) -> list[str]:
    hints: list[str] = []
    by_endpoint = {row["endpoint"]: row for row in endpoint_rows}
    proc = by_endpoint.get("/process-video")
    ana = by_endpoint.get("/analyze")

    if proc and ana and proc["p95_ms"] > ana["p95_ms"] * 1.5:
        hints.append("`/process-video` dominates latency; frame decode + pose + ball detection is likely bottleneck.")
    if ana and ana["error_rate_pct"] > 5.0:
        hints.append("High `/analyze` error rate; investigate payload quality and solver failure conditions.")
    if proc and proc["error_rate_pct"] > 5.0:
        hints.append("High `/process-video` error rate; check upload limits, video validity, and temporary file handling.")

    cpu_peak = system_summary.get("cpu_peak_pct")
    mem_peak = system_summary.get("mem_peak_pct")
    rss_peak = system_summary.get("rss_peak_mb")
    if cpu_peak is not None and cpu_peak >= 85.0:
        hints.append("CPU saturation detected (>=85% peak); worker scaling or background job queue is recommended.")
    if mem_peak is not None and mem_peak >= 90.0:
        hints.append("System memory pressure is high (>=90%); video/frame memory footprint may cause instability.")
    if rss_peak is not None and rss_peak >= 2000:
        hints.append("Backend process RSS exceeded 2GB; consider bounded queues and frame chunking.")

    if not hints:
        hints.append("No severe bottleneck heuristic triggered at current load level.")
    return hints


def _print_human_report(full_report: dict[str, Any]) -> None:
    print("\n=== Stress Test Report ===")
    print(json.dumps(full_report["config"], indent=2))
    print("\n--- Overall ---")
    print(json.dumps(full_report["overall"], indent=2))
    print("\n--- Per Endpoint ---")
    for row in full_report["per_endpoint"]:
        print(json.dumps(row, indent=2))
    print("\n--- Resource Summary ---")
    print(json.dumps(full_report["resource_summary"], indent=2))
    print("\n--- Top Errors ---")
    print(json.dumps(full_report["top_errors"], indent=2))
    print("\n--- Bottleneck Hints ---")
    for hint in full_report["bottleneck_hints"]:
        print(f"- {hint}")
    print("\n--- Edge Cases ---")
    print(json.dumps(full_report["edge_cases"], indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stress test PenaltyIQ backend endpoints.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Backend base URL")
    parser.add_argument("--video-path", required=True, help="Valid MP4/MOV sample video path")
    parser.add_argument("--large-video-path", default=None, help="Optional oversized video path for 413 testing")
    parser.add_argument("--users", type=int, default=5, help="Concurrent virtual users (1-50)")
    parser.add_argument("--iterations", type=int, default=2, help="Requests-per-user for full flow")
    parser.add_argument("--timeout", type=float, default=120.0, help="HTTP timeout seconds")
    parser.add_argument("--goal-zone", default="T1", choices=VALID_ZONES, help="Goal zone for main load flow")
    parser.add_argument("--max-connections", type=int, default=100, help="HTTP connection pool size")
    parser.add_argument("--monitor-pid", type=int, default=None, help="Optional backend PID for process RSS tracking")
    parser.add_argument("--output-json", default=None, help="Optional file path to save full JSON report")
    return parser.parse_args()


async def async_main(args: argparse.Namespace) -> int:
    users = max(1, min(args.users, 50))
    video_path = Path(args.video_path).expanduser().resolve()
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    large_video_path = None
    if args.large_video_path:
        large_video_path = Path(args.large_video_path).expanduser().resolve()

    harness = StressHarness(
        base_url=args.base_url,
        video_path=video_path,
        users=users,
        iterations_per_user=max(1, args.iterations),
        timeout_s=max(5.0, args.timeout),
        goal_zone=args.goal_zone,
        max_connections=max(10, args.max_connections),
        monitor_pid=args.monitor_pid,
    )
    load_report = await harness.run()
    edge_report = await run_edge_cases(
        base_url=args.base_url,
        valid_video_path=video_path,
        timeout_s=max(5.0, args.timeout),
        large_video_path=large_video_path,
    )

    full_report = {**load_report, **edge_report}
    _print_human_report(full_report)
    if args.output_json:
        out_path = Path(args.output_json).expanduser().resolve()
        out_path.write_text(json.dumps(full_report, indent=2), encoding="utf-8")
        print(f"\nSaved report JSON: {out_path}")
    return 0


def main() -> int:
    args = parse_args()
    return asyncio.run(async_main(args))


if __name__ == "__main__":
    raise SystemExit(main())

