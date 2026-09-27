"""
Manual demo run for GeoMind AI.

Usage:
    python scripts/demo_run.py

Exercises the full pipeline against a running server.
Assumes:
    uvicorn app.main:app --port 8000
is already running.
"""

import sys
import time
import httpx

BASE = "http://localhost:8000/api/v1"


def main():
    question = "Which areas have limited healthcare access?"

    print(f"[GeoMind] Submitting: {question}")
    r = httpx.post(f"{BASE}/query", json={"question": question}, timeout=10)
    r.raise_for_status()
    analysis_id = r.json()["analysis_id"]
    print(f"[GeoMind] analysis_id = {analysis_id}")

    for i in range(30):
        time.sleep(1)
        s = httpx.get(f"{BASE}/analysis/{analysis_id}", timeout=10).json()
        status = s["status"]
        print(f"[GeoMind] poll {i+1}: {status}")
        if status == "completed":
            print()
            print("=" * 60)
            print("HEADLINE:", s["insight"]["headline"])
            print("SUMMARY :", s["insight"]["summary"])
            print("FINDINGS:")
            for kf in s["insight"]["key_findings"]:
                print(f"  - {kf}")
            print()
            print("STATISTICS:", s["statistics"])
            print("FEATURES  :", len(s["map"]["features"]))
            print("PROVENANCE:", len(s["provenance"]))
            print("LIMITATIONS:", s["limitations"])
            print("=" * 60)
            return 0
        if status == "failed":
            print("[GeoMind] FAILED:", s)
            return 1

    print("[GeoMind] Timed out waiting for completion")
    return 1


if __name__ == "__main__":
    sys.exit(main())
