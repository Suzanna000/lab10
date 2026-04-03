from __future__ import annotations

import argparse
import concurrent.futures
import sys
import time
import httpx
import psutil


def bench_http(url: str, requests: int, workers: int) -> float:
	def one(client: httpx.Client) -> None:
		r = client.get(url)
		r.raise_for_status()

	t0 = time.perf_counter()
	with httpx.Client() as client:
		with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
			list(pool.map(lambda _: one(client), range(requests)))
	return time.perf_counter() - t0


def rss_mb(pid: int) -> float | None:
	if psutil is None:
		return None
	try:
		p = psutil.Process(pid)
		return p.memory_info().rss / (1024 * 1024)
	except (psutil.NoSuchProcess, psutil.AccessDenied):
		return None


def main() -> None:
	parser = argparse.ArgumentParser()
	parser.add_argument("--go-url", default="http://127.0.0.1:8080/health")
	parser.add_argument("--py-url", default="http://127.0.0.1:8000/health")
	parser.add_argument("-n", "--requests", type=int, default=800)
	parser.add_argument("-w", "--workers", type=int, default=40)
	parser.add_argument("--go-pid", type=int, default=0)
	parser.add_argument("--py-pid", type=int, default=0)
	args = parser.parse_args()

	def run(name: str, url: str) -> None:
		try:
			dt = bench_http(url, args.requests, args.workers)
			rps = args.requests / dt
			print(f"{name}: {args.requests} reqs in {dt:.3f}s (~{rps:.0f} rps) {url=}")
		except httpx.ConnectError:
			print(f"{name}: unreachable {url}", file=sys.stderr)

	run("Gin", args.go_url)
	run("FastAPI", args.py_url)

	if args.go_pid or args.py_pid:
		if psutil is None:
			print("Install psutil for RSS: pip install psutil", file=sys.stderr)
			return
		if args.go_pid:
			m = rss_mb(args.go_pid)
			print(f"RSS go (pid {args.go_pid}): {m:.1f} MiB" if m is not None else f"pid {args.go_pid} not found")
		if args.py_pid:
			m = rss_mb(args.py_pid)
			print(f"RSS python (pid {args.py_pid}): {m:.1f} MiB" if m is not None else f"pid {args.py_pid} not found")


if __name__ == "__main__":
	main()
