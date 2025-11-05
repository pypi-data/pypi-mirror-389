import argparse
import json
import os
import platform
import random
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Dependencies
try:
    from ariadne import explain_routing, simulate
except Exception as e:
    print("ERROR: Could not import ariadne. Is 'ariadne-router' installed?", e)
    sys.exit(1)

try:
    from qiskit import QuantumCircuit
    from qiskit.circuit import Parameter
except Exception as e:
    print("ERROR: Could not import qiskit. Please 'pip install qiskit'.", e)
    sys.exit(1)


def get_available_backends_safe():
    try:
        from ariadne import get_available_backends

        return list(get_available_backends())
    except Exception:
        return []


def hw_info():
    info = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "os": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "available_backends": get_available_backends_safe(),
        "nvidia_smi": None,
        "jax_devices": None,
        "ariadne_version": None,
    }
    # ariadne version if available
    try:
        import ariadne as _a

        info["ariadne_version"] = getattr(_a, "__version__", None)
    except Exception:
        pass
    # nvidia-smi
    try:
        out = subprocess.check_output(["nvidia-smi", "-L"], stderr=subprocess.STDOUT, timeout=3).decode()
        info["nvidia_smi"] = out.strip()
    except Exception:
        info["nvidia_smi"] = None
    # jax devices (for Apple Metal / GPU)
    try:
        import jax

        info["jax_devices"] = [str(d) for d in jax.devices()]
    except Exception:
        info["jax_devices"] = None
    return info


# ---------- Circuit builders ----------
def ghz(n):
    qc = QuantumCircuit(n, n)
    qc.h(0)
    for i in range(n - 1):
        qc.cx(i, i + 1)
    qc.measure_all()
    return qc, {"family": "clifford_ghz", "n_qubits": n, "depth": None}


def random_clifford(n, depth=4, seed=1):
    rnd = random.Random(seed)
    qc = QuantumCircuit(n, n)
    gates = ["h", "s", "cx"]
    for _ in range(depth):
        for q in range(n):
            g = gates[rnd.randrange(0, 2)]  # pick h or s locally
            if g == "h":
                qc.h(q)
            elif g == "s":
                qc.s(q)
        # add some CXs
        for _ in range(n // 2):
            a = rnd.randrange(0, n - 1)
            b = a + 1
            qc.cx(a, b)
    qc.measure_all()
    return qc, {"family": "clifford_random", "n_qubits": n, "depth": depth}


def low_entanglement_chain(n, depth=6, seed=1):
    rnd = random.Random(seed)
    qc = QuantumCircuit(n, n)
    for _ in range(depth):
        for q in range(n):
            theta = (rnd.random() - 0.5) * 0.6  # small angles -> low entanglement
            qc.ry(theta, q)
        for i in range(n - 1):
            qc.cz(i, i + 1)
    qc.measure_all()
    return qc, {"family": "low_entanglement", "n_qubits": n, "depth": depth}


def random_universal(n, depth=8, seed=1):
    rnd = random.Random(seed)
    qc = QuantumCircuit(n, n)
    for _ in range(depth):
        for q in range(n):
            if rnd.random() < 0.5:
                qc.h(q)
            else:
                qc.t(q)  # non-Clifford
        for _ in range(n):
            a = rnd.randrange(0, n - 1)
            b = a + 1
            qc.cx(a, b)
    qc.measure_all()
    return qc, {"family": "general_random", "n_qubits": n, "depth": depth}


def parameterized_bound(n=4, theta_val=0.3):
    theta = Parameter("θ")
    qc = QuantumCircuit(n, n)
    qc.ry(theta, 0)
    for i in range(n - 1):
        qc.cx(i, i + 1)
    qc = qc.assign_parameters({theta: theta_val})
    qc.measure_all()
    return qc, {"family": "param_bound", "n_qubits": n, "depth": None}


def repetition_code(n=3):
    qc = QuantumCircuit(n, n)
    qc.cx(0, 1)
    qc.cx(0, 2)
    qc.measure_all()
    return qc, {"family": "clifford_repetition", "n_qubits": n, "depth": None}


# ---------- Utilities ----------
def tvd(counts_a, counts_b):
    # normalize and compute 0.5*L1 distance over union of keys
    total_a = sum(counts_a.values()) or 1
    total_b = sum(counts_b.values()) or 1
    keys = set(counts_a) | set(counts_b)
    return 0.5 * sum(abs(counts_a.get(k, 0) / total_a - counts_b.get(k, 0) / total_b) for k in keys)


def run_sim(qc, shots, backend=None):
    t0 = time.perf_counter()
    res = simulate(qc, shots=shots, backend=backend)
    t1 = time.perf_counter()
    elapsed = getattr(res, "execution_time", None)
    if elapsed is None:
        elapsed = t1 - t0
    used = getattr(res, "backend_used", backend or "unknown")
    counts = getattr(res, "counts", {})
    return used, elapsed, counts, res


def is_clifford(qc) -> bool:
    # heuristic: only H,S,CX and measurements
    clifford_gates = {"h", "s", "x", "y", "z", "sdg", "sx", "sxdg", "cx", "cy", "cz", "swap", "measure", "barrier"}
    for inst, _qargs, _cargs in qc.data:
        if inst.name.lower() not in clifford_gates:
            return False
    return True


def circuits_suite() -> list:
    circuits = []
    # Clifford
    for n in [8, 16, 32]:
        circuits.append(ghz(n))
    for n in [12, 24]:
        circuits.append(random_clifford(n, depth=4, seed=n))
    circuits.append(repetition_code(3))
    # Low entanglement
    for n in [12, 24]:
        circuits.append(low_entanglement_chain(n, depth=6, seed=n))
    # General
    for n in [8, 16, 24]:
        circuits.append(random_universal(n, depth=8, seed=n))
    # Param
    circuits.append(parameterized_bound(4, 0.3))
    return circuits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="results")
    ap.add_argument("--shots", type=int, default=1000)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--timeout_s", type=int, default=90)
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    hw = hw_info()
    with open(outdir / "hardware.json", "w") as f:
        json.dump(hw, f, indent=2)

    csv_path = outdir / "benchmarks.csv"
    if not csv_path.exists():
        with open(csv_path, "w") as f:
            f.write(
                "timestamp,ariadne_version,python_version,os,cpu,gpu_label,machine,"
                "circuit_id,circuit_family,n_qubits,depth,shots,"
                "backend_auto,time_auto_s,backend_baseline,time_baseline_s,tvd_vs_baseline,"
                "routing_explanation,status\n"
            )

    suite = circuits_suite()

    # Baseline availability check
    baseline_name = "qiskit"  # Ariadne's Aer alias in README examples
    have_baseline = True
    try:
        _ = simulate(QuantumCircuit(1), shots=1, backend=baseline_name)
    except Exception:
        have_baseline = False

    # Stim availability probe
    have_stim = True
    try:
        _ = simulate(QuantumCircuit(1), shots=1, backend="stim")
    except Exception:
        have_stim = False

    # Run
    for idx, (qc, meta) in enumerate(suite):
        circuit_id = f"{meta['family']}_{meta['n_qubits']}_{idx}"
        n_qubits = meta["n_qubits"]
        depth = meta.get("depth")
        # repeats
        best_auto = None
        best_auto_time = float("inf")
        last_auto_counts = None
        routing_expl = ""
        status = "ok"

        # routing explanation (non-fatal)
        try:
            routing_expl = str(explain_routing(qc))
        except Exception:
            routing_expl = ""

        # AUTO runs
        try:
            for _r in range(args.repeats):
                used, elapsed, counts, _res = run_sim(qc, args.shots, backend=None)
                if elapsed < best_auto_time:
                    best_auto_time, best_auto, last_auto_counts = elapsed, used, counts
        except Exception as e:
            status = f"auto_error:{type(e).__name__}"

        # BASELINE run (Aer)
        baseline_time = None
        tvd_val = None
        if have_baseline and status == "ok":
            try:
                b_used, baseline_time, b_counts, _ = run_sim(qc, args.shots, backend=baseline_name)
                if last_auto_counts is not None:
                    tvd_val = tvd(last_auto_counts, b_counts)
            except Exception as e:
                status = f"baseline_error:{type(e).__name__}"

        # Stim cross-check for strict Clifford
        if have_stim and status == "ok" and is_clifford(qc):
            try:
                s_used, s_time, s_counts, _ = run_sim(qc, args.shots, backend="stim")
                # if baseline missing, compare AUTO to Stim for TVD
                if tvd_val is None and last_auto_counts is not None:
                    tvd_val = tvd(last_auto_counts, s_counts)
            except Exception:
                pass

        # Write row
        gpu_label = (
            "NV:" + ("yes" if hw.get("nvidia_smi") else "no") + " JAX:" + ("yes" if hw.get("jax_devices") else "no")
        )
        row = [
            datetime.now().isoformat(),
            hw.get("ariadne_version"),
            hw.get("python"),
            hw.get("os"),
            hw.get("processor"),
            gpu_label,
            hw.get("machine"),
            circuit_id,
            meta["family"],
            n_qubits,
            depth if depth is not None else "",
            args.shots,
            best_auto or "",
            f"{best_auto_time:.6f}" if best_auto_time != float("inf") else "",
            baseline_name if have_baseline else "",
            f"{baseline_time:.6f}" if baseline_time is not None else "",
            f"{tvd_val:.6f}" if tvd_val is not None else "",
            routing_expl.replace(",", ";")[:500],
            status,
        ]
        with open(csv_path, "a") as f:
            f.write(",".join(map(str, row)) + "\n")

    # Summarize
    import csv

    rows = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r["status"] == "ok":
                rows.append(r)
    # Speedups
    speedups = []
    for r in rows:
        try:
            t_auto = float(r["time_auto_s"])
            t_base = float(r["time_baseline_s"]) if r["time_baseline_s"] else None
            if t_base and t_auto > 0:
                speedups.append((t_base / t_auto, r))
        except Exception:
            pass
    speedups.sort(reverse=True)
    top = speedups[:10]

    # Routing histogram
    from collections import Counter

    hist = Counter(r["backend_auto"] for r in rows)

    # Flags on correctness
    bad = [
        r for r in rows if r["tvd_vs_baseline"] and r["tvd_vs_baseline"] != "" and float(r["tvd_vs_baseline"]) > 0.06
    ]

    md = [
        "# Ariadne Benchmark Summary",
        "",
        f"- Total circuits run: {len(rows)}",
        "- Routing distribution: " + ", ".join(f"{k}:{v}" for k, v in hist.items()),
        "",
    ]
    if top:
        md.append("## Top Speedups (baseline/Aer vs auto)")
        for s, r in top:
            md.append(
                f"- {s:.1f}×  | {r['circuit_id']}  | auto={r['backend_auto']}  base={r['backend_baseline']}  "
                f"t_auto={float(r['time_auto_s']):.4f}s  t_base={float(r['time_baseline_s']):.4f}s"
            )
        md.append("")
    if bad:
        md.append("## Potential Correctness Flags (TVD > 0.06)")
        for r in bad:
            md.append(
                f"- {r['circuit_id']}  TVD={r['tvd_vs_baseline']}  auto={r['backend_auto']} "
                f"base={r['backend_baseline']}"
            )
        md.append("")
    md.append("## Notes")
    md.append("- TVD threshold 0.06 is a heuristic for 1k–5k shots; raise shots for tighter checks.")
    md.append(
        "- Clifford circuits should prefer 'stim' when available; low-entanglement often route to tensor networks."
    )
    md.append("- Parameterized circuits are pre-bound in this suite.")
    with open(outdir / "summary.md", "w") as f:
        f.write("\n".join(md))

    # Print TL;DR
    print("\n=== TL;DR ===")
    print(f"Circuits run: {len(rows)}")
    print("Routing:", dict(hist))
    if top:
        s, r = top[0]
        print(f"Max speedup: {s:.1f}× on {r['circuit_id']} (auto={r['backend_auto']} vs base={r['backend_baseline']})")
    if bad:
        print(f"Correctness flags (TVD>0.06): {len(bad)} -> see results/summary.md")
    print("Artifacts: results/benchmarks.csv, results/hardware.json, results/summary.md")


if __name__ == "__main__":
    main()
