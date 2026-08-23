# benchmarks/run_audit.py
"""Run the full algorithm audit corpus through the QVM pipeline.

Usage:
    python -m benchmarks.run_audit            # fast suite (skip SLOW modules)
    python -m benchmarks.run_audit --all      # include variational training
"""
import importlib
import pkgutil
import sys
import time

from benchmarks import harness


def discover():
    import benchmarks.algos as pkg
    mods = []
    for m in pkgutil.iter_modules(pkg.__path__):
        mod = importlib.import_module(f"benchmarks.algos.{m.name}")
        mods.append(mod)
    return sorted(mods, key=lambda m: m.NAME)


def main(include_slow=False):
    rows = []
    t_all = time.time()
    for mod in discover():
        if getattr(mod, "SLOW", False) and not include_slow:
            continue
        res = harness.run_case(mod)
        flag = ""
        for stage in ("import", "simulate"):
            if str(res[stage]).startswith("FAIL"):
                flag = "💥"
        if res["validate"].startswith("FAIL") or res["match"].startswith(("MISMATCH",)):
            flag = flag or "⚠️"
        rows.append(res)
        print(f"{flag} {res['id']:<26} {res['framework']:<10} "
              f"imp={res['import']:<8} sim={res['simulate']:<28} "
              f"match={res['match']:<24} val={res['validate']:<22} [{res['time_s']:.2f}s]")

    n = len(rows)
    fails_import = [r for r in rows if r["import"].startswith("FAIL")]
    fails_sim = [r for r in rows if r["simulate"].startswith("FAIL")]
    fails_match = [r for r in rows if r["match"].startswith(("MISMATCH", "ERR"))]
    fails_val = [r for r in rows if r["validate"].startswith("FAIL")]

    print("\n" + "=" * 78)
    print(f"AUDIT COMPLETE: {n} cases in {time.time()-t_all:.1f}s | "
          f"clean={n - len(fails_import) - len(fails_sim) - len(fails_match) - len(fails_val)} "
          f"import✗={len(fails_import)} sim✗={len(fails_sim)} "
          f"match✗={len(fails_match)} validate✗={len(fails_val)}")
    for label, group in [("IMPORT", fails_import), ("SIMULATE", fails_sim),
                         ("MATCH", fails_match), ("VALIDATE", fails_val)]:
        for r in group:
            stage = {"IMPORT": r["import"], "SIMULATE": r["simulate"],
                     "MATCH": r["match"], "VALIDATE": r["validate"]}[label]
            print(f"  ✗ [{label}] {r['id']}: {stage}")
    return rows


if __name__ == "__main__":
    main(include_slow="--all" in sys.argv)
