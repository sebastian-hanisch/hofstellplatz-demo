"""Fehler-Einbau-Test: baut einzelne Fehler in die Module ein und prueft, ob die Tests (ohne AppTests)
sie finden.

Aufruf (im Projektordner): ./venv/Scripts/python.exe tools/mutation_check.py [Teilstring des Dateinamens] [--jobs N] [--indices 1,5-9] [--with-app] [--dry-run]
Jeder Mutant ersetzt genau eine Stelle; Ueberlebende sind entweder gleichwertig (kein sichtbarer
Unterschied) oder eine Luecke der Tests. Die Kopie liegt je Mutant in einem temporaeren Ordner;
PYTHONDONTWRITEBYTECODE=1, damit veralteter Bytecode keine Ueberlebenden vortaeuscht; Quelltexte
als LF (Windows-Python schreibt sonst CRLF und die Zeichenketten unten finden nichts). Ein Mutant
kann in eine Endlosschleife laufen; nach TIMEOUT Sekunden gilt er als gefunden. Mutanten laufen
parallel (--jobs, Standard 6); `--with-app` nimmt die AppTests hinzu. `--dry-run` prueft nur, ob
jede Zeichenkette genau einmal vorkommt."""
import concurrent.futures
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PY = sys.executable
WITH_APP = "--with-app" in sys.argv
TIMEOUT = 240
TEST_ORDER = ["test_scenario.py", "test_rules.py", "test_simulation.py", "test_evaluation.py", "test_presets.py", "test_stories.py", "test_visualization.py", "test_pdf_export.py"]

MUTANTS = [
    # hst_constants.py
    ("hst_constants.py", "ROW_SPACING_M = 15.0", "ROW_SPACING_M = 12.0"),
    ("hst_constants.py", "BASE_DIST_M = 20.0", "BASE_DIST_M = 15.0"),
    ("hst_constants.py", "return BASE_DIST_M + row_index * ROW_SPACING_M", "return BASE_DIST_M + (row_index + 1) * ROW_SPACING_M"),
    ("hst_constants.py", "return abs(row_distance(row_a) - row_distance(row_b))", "return row_distance(row_a) + row_distance(row_b)"),
    ("hst_constants.py", "MIN_DWELL_MIN = 5.0", "MIN_DWELL_MIN = 1.0"),
    ("hst_constants.py", "VERDICT_Z = 2.0", "VERDICT_Z = 1.0"),
    # hst_scenario.py
    ("hst_scenario.py", "return random.Random(seed * 1_000_003 + 7)", "return random.Random(seed * 1_000_003)"),
    ("hst_scenario.py", "arrival = rng.uniform(0.0, window_min)", "arrival = rng.uniform(0.0, window_min * 0.9)"),
    ("hst_scenario.py", "dwell = max(C.MIN_DWELL_MIN, rng.expovariate(1.0 / mean_dwell_min))", "dwell = max(C.MIN_DWELL_MIN, rng.expovariate(1.0 / mean_dwell_min)) * 1.1"),
    ("hst_scenario.py", "pickup_est = max(arrival + 1.0, pickup + err)", "pickup_est = max(arrival, pickup + err)"),
    ("hst_scenario.py", "err = noise.gauss(0.0, sigma_pct / 100.0 * mean_dwell_min)", "err = noise.gauss(0.0, sigma_pct / 200.0 * mean_dwell_min)"),
    # hst_rules.py
    ("hst_rules.py", "cand.sort(key=lambda r: (C.row_distance(r), r))", "cand.sort(key=lambda r: (C.row_distance(r), -r))"),
    ("hst_rules.py", "non_blocking = [r for r in cand if not rows[r] or item.pickup_est <= min(o.pickup_est for o in rows[r])]", "non_blocking = [r for r in cand if not rows[r] or item.pickup_est < min(o.pickup_est for o in rows[r])]"),
    ("hst_rules.py", "return (-top, C.row_distance(r), r)", "return (top, C.row_distance(r), r)"),
    ("hst_rules.py", "blockers_deep_to_front = stack[pos + 1:]", "blockers_deep_to_front = stack[pos:]"),
    ("hst_rules.py", "return list(reversed(blockers_deep_to_front))", "return list(blockers_deep_to_front)"),
    ("hst_rules.py", "extra_dist += 2.0 * C.leg_distance(r, new_r)", "extra_dist += C.leg_distance(r, new_r)"),
    ("hst_rules.py", "return [r for r in range(len(rows)) if len(rows[r]) < depth]", "return [r for r in range(len(rows)) if len(rows[r]) <= depth]"),
    # hst_simulation.py
    ("hst_simulation.py", "ev.sort(key=lambda e: (e[0], e[1], e[3].idx))", "ev.sort(key=lambda e: (e[0], e[3].idx))"),
    ("hst_simulation.py", "res.retrieval_dist_sum += C.row_distance(r)", "res.retrieval_dist_sum += C.row_distance(r) * 1.0 + 0.01"),
    ("hst_simulation.py", "res.relocations += sum(1 for _, new_r in moves if new_r is not None)", "res.relocations += len(moves)"),
    ("hst_simulation.py", "res.overflow += sum(1 for _, new_r in moves if new_r is None)", "res.overflow += 0"),
    ("hst_simulation.py", "return self.retrieval_dist_sum / self.n_pickups if self.n_pickups else 0.0", "return self.retrieval_dist_sum / self.n_pickups if self.n_pickups else 1.0"),
    ("hst_simulation.py", "return self.relocations / self.n_items if self.n_items else 0.0", "return self.relocations / self.n_items if self.n_items else 1.0"),
    ("hst_simulation.py", "return self.overflow / self.n_items if self.n_items else 0.0", "return self.overflow / self.n_items if self.n_items else 1.0"),
    ("hst_simulation.py", "self.mean_retrieval_dist * (self.n_pickups / self.n_items if self.n_items else 0.0) + self.reloc_extra_dist_per_item",
     "self.mean_retrieval_dist + self.reloc_extra_dist_per_item"),
    # hst_evaluation.py
    ("hst_evaluation.py", "return -d / nt * 100 if nt else 0.0", "return d / nt * 100 if nt else 0.0"),
    ("hst_evaluation.py", "if se == 0.0 or abs(m) <= C.VERDICT_Z * se:", "if se == 0.0 or abs(m) < C.VERDICT_Z * se:"),
    ("hst_evaluation.py", "return (\"besser\" if m < 0 else \"schlechter\"), m, se", "return (\"besser\" if m <= 0 else \"schlechter\"), m, se"),
    ("hst_evaluation.py", "r = max(1, round(cap / h))", "r = max(1, cap // h)"),
    ("hst_evaluation.py", "if overflow_share >= 0.08:", "if overflow_share > 0.08:"),
    ("hst_evaluation.py", "if diff_pct <= -3.0:", "if diff_pct < -3.0:"),
    ("hst_evaluation.py", "if diff_pct >= 3.0:", "if diff_pct > 3.0:"),
    ("hst_evaluation.py", "var = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)", "var = sum((x - m) ** 2 for x in xs) / len(xs)"),
    # hst_presets.py
    ("hst_presets.py", "value = spec.lo + round((value - spec.lo) / spec.step) * spec.step", "value = spec.lo + int((value - spec.lo) / spec.step) * spec.step"),
    ("hst_presets.py", "if spec.step and spec.step > 1 and spec.lo is not None:", "if spec.step and spec.step > 2 and spec.lo is not None:"),
    ("hst_presets.py", "if value not in C.DEPTH_LEVELS:", "if value not in C.DEPTH_LEVELS[:3]:"),
    ("hst_presets.py", "value = int(round(float(raw)))", "value = int(float(raw))"),
    ("hst_presets.py", "if isinstance(value, float) and not math.isfinite(value):\n        return None", "if isinstance(value, float) and math.isfinite(value):\n        return None"),
    # hst_visualization.py
    ("hst_visualization.py", "def _lock_axes(fig):\n    fig.update_xaxes(fixedrange=True)", "def _lock_axes(fig):\n    fig.update_xaxes(fixedrange=False)"),
    ("hst_visualization.py", "    fig.update_yaxes(fixedrange=True)\n    return fig", "    fig.update_yaxes(fixedrange=False)\n    return fig"),
    # hst_pdf_export.py
    ("hst_pdf_export.py", "\"–\": \"-\", \"—\": \"-\", \"€\": \"EUR\"", "\"—\": \"-\", \"€\": \"EUR\""),
    ("hst_pdf_export.py", "\"€\": \"EUR\", ", ""),
]


def check_unique():
    bad = []
    for n, (name, old, new) in enumerate(MUTANTS, 1):
        text = (ROOT / name).read_bytes().decode("utf-8").replace("\r\n", "\n")
        if text.count(old) != 1:
            bad.append((n, name, old[:70], text.count(old)))
        if old == new:
            bad.append((n, name, "alt == neu", 0))
    return bad


def run_one(args):
    n, name, old, new, base = args
    tmp = pathlib.Path(tempfile.mkdtemp(prefix=f"hst_mut{n}_"))
    try:
        shutil.copytree(base, tmp, dirs_exist_ok=True)
        path = tmp / name
        original = path.read_bytes().decode("utf-8")
        path.write_bytes(original.replace(old, new).encode("utf-8"))
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        files = [f"tests/{f}" for f in TEST_ORDER + (["test_app.py"] if WITH_APP else [])]
        try:
            r = subprocess.run([PY, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider", *files], cwd=tmp, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT)
            return n, name, old, new, r.returncode == 0, False
        except subprocess.TimeoutExpired:
            return n, name, old, new, False, True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    only = args[0] if args else ""
    jobs = 6
    if "--jobs" in sys.argv:
        jobs = int(sys.argv[sys.argv.index("--jobs") + 1])
        only = "" if only == str(jobs) else only
    wanted = None
    if "--indices" in sys.argv:
        spec = sys.argv[sys.argv.index("--indices") + 1]
        only = "" if only == spec else only
        wanted = set()
        for part in spec.split(","):
            lo, _, hi = part.partition("-")
            wanted.update(range(int(lo), int(hi or lo) + 1))
    bad = check_unique()
    for b in bad:
        print("FEHLER (Stelle nicht eindeutig gefunden):", b)
    if "--dry-run" in sys.argv:
        print(f"{len(MUTANTS)} Mutanten, {len(bad)} Fehler in der Mutantenliste")
        return
    base = pathlib.Path(tempfile.mkdtemp(prefix="hst_mut_base_"))
    for f in ROOT.glob("*.py"):
        (base / f.name).write_bytes(f.read_bytes().replace(b"\r\n", b"\n"))
    shutil.copytree(ROOT / "tests", base / "tests", ignore=shutil.ignore_patterns("__pycache__"))
    for f in (base / "tests").glob("*.py"):
        f.write_bytes(f.read_bytes().replace(b"\r\n", b"\n"))
    bad_ids = {b[0] for b in bad}
    work = [(n, name, old, new, base) for n, (name, old, new) in enumerate(MUTANTS, 1) if n not in bad_ids and (not only or only in name) and (wanted is None or n in wanted)]
    survivors, killed = [], 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        for n, name, old, new, survived, timeout in pool.map(run_one, work):
            if timeout:
                print(f"[{n:3d}] Zeitueberschreitung (als gefunden gezaehlt)  {name}", flush=True)
            if survived:
                survivors.append((n, name, old[:70], new[:70]))
                print(f"[{n:3d}] UEBERLEBT  {name}: {old[:70]!r} -> {new[:70]!r}", flush=True)
            else:
                killed += 1
                print(f"[{n:3d}] gefunden  {name}", flush=True)
    print(f"\n{killed} gefunden, {len(survivors)} ueberlebt, {len(bad)} Fehler in der Mutantenliste")
    shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    main()
