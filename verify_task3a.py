#!/usr/bin/env python3
"""Exact-arithmetic audit of the four requested Task 3A checks.

[author confirmation needed] All computations are NEW research-audit material,
not manuscript text and not a verification of the complete NP-completeness proof.

Source: Main_Manuscript_Econometrica(2).pdf, 12 September 2026.
Primitives: equation (1), Section 4.2, equation (17), Section 5.2.
Python standard library only. No randomness or floating-point arithmetic.

Usage:
    python verify_task3a.py --output task3a_audit.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction as F
from itertools import combinations, product
from pathlib import Path

STATUS = "[author confirmation needed]"
SUPPORT = ("100", "110", "010", "011", "001", "101")
EXPECTED_CORE = {
    "100": (3, 2, 1), "110": (3, 2, 1),
    "010": (2, 1, 3), "011": (2, 1, 3),
    "001": (1, 3, 2), "101": (1, 3, 2),
}
CORE_R = {1: F(-1), 2: F(0), 3: F(1)}
CORE_KAPPA = {1: F(4), 2: F(1, 2), 3: F(4)}
CORE_TYPES = {
    1: (F(1, 10), F(2, 5)),
    2: (F(1, 10), F(-1, 10)),
    3: (F(-2, 5), F(-1, 10)),
}
EXPECTED_RANKINGS = {
    1: ((2, 3, 1), (3, 2, 1)),
    2: ((3, 1, 2), (1, 3, 2)),
    3: ((1, 2, 3), (2, 1, 3)),
}


def require(condition: bool, message: str) -> None:
    """Keep checks active even when Python runs with -O."""
    if not condition:
        raise AssertionError(message)


def pair(a: int) -> tuple[int, int]:
    return 2 * a + 2, 2 * a + 3


def primitive_data(k: int):
    """[author confirmation needed] Transcribe Section 5 for k source sets.

    k=0 is used only for computing the three-worker core by itself.
    """
    require(k >= 0, "k must be nonnegative")
    r, curvature, types = dict(CORE_R), dict(CORE_KAPPA), dict(CORE_TYPES)
    for a in range(1, 2 * k + 1):
        u, v = pair(a)
        r[u], r[v] = F(10 + 4 * a), F(11 + 4 * a)
        curvature[u] = curvature[v] = F(1)
        types[u], types[v] = (r[v] + F(1, 8),), (r[u] + F(1, 8),)
    return r, curvature, types


def utility_table(k: int, bits: str) -> dict[int, dict[int, F]]:
    require(len(bits) == 3 and set(bits) <= {"0", "1"}, "Invalid core profile")
    r, curvature, types = primitive_data(k)
    table = {}
    for i in r:
        t = types[i][int(bits[i - 1])] if i <= 3 else types[i][0]
        table[i] = {
            j: F(-1 if j == 2 else 0) - curvature[i] * (r[j] - t) ** 2 / 2
            for j in r
        }
        require(len(set(table[i].values())) == len(r), f"Utility tie: k={k}, i={i}")
    return table


def ttc(table: dict[int, dict[int, F]]):
    """[author confirmation needed] Run TTC directly from rational utilities.

    Workers initially own equally numbered contracts. Execute all directed cycles
    in each round; remove their workers and endowed contracts simultaneously.
    """
    remaining = set(table)
    allocation: dict[int, int] = {}
    rounds = []
    while remaining:
        pointers = {i: max(remaining, key=lambda j: table[i][j]) for i in sorted(remaining)}
        found = {}
        for start in sorted(remaining):
            path, position = [], {}
            vertex = start
            while vertex not in position:
                position[vertex] = len(path)
                path.append(vertex)
                vertex = pointers[vertex]
            cycle = path[position[vertex]:]
            pivot = cycle.index(min(cycle))
            cycle = tuple(cycle[pivot:] + cycle[:pivot])
            found[frozenset(cycle)] = cycle
        cycles = sorted(found.values())
        removed = {i for cycle in cycles for i in cycle}
        require(bool(removed), "No TTC cycle")
        rounds.append({"pointers": pointers, "cycles": cycles})
        allocation.update({i: pointers[i] for i in removed})
        remaining -= removed
    require(set(allocation.values()) == set(table), "Output is not a permutation")
    return allocation, rounds


def block(i: int) -> int:
    return 0 if i <= 3 else (i - 4) // 2 + 1


def fiscal_matrices(L: int, sets: tuple[frozenset[int], ...]):
    """[author confirmation needed] Build the full original cost matrices.

    Zero-based Python arrays; worker and contract IDs elsewhere remain one-based.
    """
    k, n = len(sets), 3 + 4 * len(sets)
    matrices = [("block", [[int(block(i) != block(j)) for j in range(1, n + 1)]
                           for i in range(1, n + 1)])]
    for j in range(2, k + 1):
        d = [[1] * n for _ in range(n)]
        u, v = pair(k + j)
        d[u - 1][v - 1] += 1
        u, v = pair(k + 1)
        d[u - 1][v - 1] -= 1
        matrices.append((f"sync_{j}", d))
    for ell in range(1, L + 1):
        d = [[1] * n for _ in range(n)]
        d[0][1] += 1
        d[1][0] -= 1
        for j, S in enumerate(sets, 1):
            entry = int(ell in S)
            u, v = pair(j)
            d[u - 1][v - 1] -= entry
            u, v = pair(k + j)
            d[u - 1][v - 1] += entry
        matrices.append((f"element_{ell}", d))
    require(len(matrices) == L + k, "Wrong number of fiscal coordinates")
    require(all(0 <= z <= 2 for _, d in matrices for row in d for z in row),
            "Fiscal entry outside {0,1,2}")
    return matrices


def direct_residual(d: list[list[int]], allocation: dict[int, int]) -> int:
    return sum(d[i - 1][allocation[i] - 1] - d[i - 1][i - 1] for i in allocation)


def has_exact_cover(L: int, sets: tuple[frozenset[int], ...]) -> bool:
    return any(all(sum(int(ell in S) * bit for S, bit in zip(sets, bits)) == 1
                   for ell in range(1, L + 1))
               for bits in product((0, 1), repeat=len(sets)))


def run_audit(max_k_ttc: int = 12) -> dict:
    # The fiscal checks below reuse TTC outcomes for k=1,2,3.
    require(max_k_ttc >= 3, "max_k_ttc must be at least 3")

    # [author confirmation needed] Check rankings and TTC without using Table II.
    outcomes, traces = {}, {}
    for bits in SUPPORT:
        table = utility_table(0, bits)
        allocation, rounds = ttc(table)
        for i in range(1, 4):
            ranking = tuple(sorted(table[i], key=table[i].get, reverse=True))
            require(ranking == EXPECTED_RANKINGS[i][int(bits[i-1])], "Ranking mismatch")
        require(tuple(allocation[i] for i in range(1, 4)) == EXPECTED_CORE[bits],
                f"Unexpected actual TTC outcome at {bits}")
        outcomes[bits], traces[bits] = allocation, rounds

    # [author confirmation needed] Enumerate all supported unilateral edges.
    edges, strict, equality = [], 0, 0
    adjacency = {m: set() for m in SUPPORT}
    for m, other in combinations(SUPPORT, 2):
        different = [i for i in range(3) if m[i] != other[i]]
        if len(different) != 1:
            continue
        i = different[0] + 1
        m0, m1 = (m, other) if m[i-1] == "0" else (other, m)
        j0, j1 = outcomes[m0][i], outcomes[m1][i]
        u0, u1 = utility_table(0, m0)[i], utility_table(0, m1)[i]
        delta0, delta1 = u0[j0] - u0[j1], u1[j1] - u1[j0]
        require(delta0 >= 0 and delta1 >= 0, f"Supported IC violation: {m0}, {m1}")
        if j0 != j1:
            require(delta0 > 0 and delta1 > 0, "Nonconstant edge not strict both ways")
        strict += int(delta0 > 0) + int(delta1 > 0)
        equality += int(delta0 == 0) + int(delta1 == 0)
        edges.append({
            "worker": i, "bit0_profile": m0, "bit1_profile": m1,
            "own_contract_bit0": j0, "own_contract_bit1": j1,
            "bit0_truthful_utility": str(u0[j0]), "bit0_deviation_utility": str(u0[j1]),
            "bit1_truthful_utility": str(u1[j1]), "bit1_deviation_utility": str(u1[j0]),
            "bit0_surplus": str(delta0), "bit1_surplus": str(delta1),
        })
        adjacency[m].add(other)
        adjacency[other].add(m)
    reached, stack = set(), [SUPPORT[0]]
    while stack:
        m = stack.pop()
        if m not in reached:
            reached.add(m)
            stack.extend(adjacency[m] - reached)
    require(len(reached) == 6 and len(edges) == 6, "Support graph is not the intended cycle")
    require({e['worker'] for e in edges if e['own_contract_bit0'] != e['own_contract_bit1']}
            == {1, 2, 3}, "A strategically active worker lacks a nonconstant supported edge")
    require((strict, equality) == (6, 6), "Unexpected strict/equality comparison count")

    # [author confirmation needed] Include ALL auxiliary workers in TTC for k=1,...,12.
    full_outcomes = {}
    full_runs = 0
    for k in range(1, max_k_ttc + 1):
        for bits in SUPPORT:
            table = utility_table(k, bits)
            allocation, _ = ttc(table)
            require(tuple(allocation[i] for i in range(1, 4)) == EXPECTED_CORE[bits],
                    "Auxiliaries altered a core TTC outcome")
            for a in range(1, 2 * k + 1):
                u, v = pair(a)
                require(allocation[u] == v and allocation[v] == u, "Auxiliary pair did not swap")
                require(table[u][v] - table[u][u] == F(5, 8), "Wrong first-partner IR gain")
                require(table[v][u] - table[v][v] == F(3, 8), "Wrong second-partner IR gain")
            full_outcomes[k, bits] = allocation
            full_runs += 1

    # [author confirmation needed] Exhaust all small ordered set families.
    # Repeated nonempty source sets and uncovered elements are allowed.
    instances = supported_rows = matrix_checks = yes = no = uncovered = 0
    for L in range(1, 4):
        nonempty = tuple(frozenset(ell + 1 for ell in range(L) if mask & (1 << ell))
                         for mask in range(1, 1 << L))
        for k in range(1, 4):
            for sets in product(nonempty, repeat=k):
                matrices = fiscal_matrices(L, sets)
                cover = has_exact_cover(L, sets)
                yes += int(cover)
                no += int(not cover)
                uncovered += int(any(all(ell not in S for S in sets) for ell in range(1, L+1)))
                instances += 1
                for bits in SUPPORT:
                    allocation = full_outcomes[k, bits]
                    t = int(allocation[1] == 2) - int(allocation[2] == 1)
                    x = tuple(int(allocation[pair(j)[0]] == pair(j)[1]) for j in range(1, k+1))
                    y = tuple(int(allocation[pair(k+j)[0]] == pair(k+j)[1]) for j in range(1, k+1))
                    require(t == 0 and all(x) and all(y), "Wrong supported fiscal indicators")
                    residuals = {name: direct_residual(d, allocation) for name, d in matrices}
                    require(all(value == 0 for value in residuals.values()), "Nonzero fiscal residual")
                    for ell in range(1, L+1):
                        H = sum(int(ell in S) for S in sets)
                        coverage = sum(int(ell in S)*bit for S, bit in zip(sets, x))
                        require(residuals[f'element_{ell}'] == t - coverage + y[0]*H,
                                "Direct matrix calculation disagrees with equation (20)")
                    supported_rows += 1
                    matrix_checks += len(matrices)

    require(instances == 441 and supported_rows == 2646, "Unexpected exhaustive test size")
    off_support_ttc = {}
    for bits in ("000", "111"):
        allocation, _ = ttc(utility_table(0, bits))
        off_support_ttc[bits] = [allocation[i] for i in range(1, 4)]
    require(off_support_ttc["111"] == [3, 1, 2], "Diagnostic TTC(111) must be C-minus")

    return {
        "status": STATUS,
        "scope": "Four requested checks only; no manuscript changes; not a complete hardness proof audit.",
        "arithmetic": "Exact fractions and integers; no random sampling.",
        "support": list(SUPPORT),
        "actual_core_ttc": {m: [outcomes[m][i] for i in range(1, 4)] for m in SUPPORT},
        "core_ttc_rounds": traces,
        "supported_edges": sorted(edges, key=lambda e: (e['worker'], e['bit0_profile'])),
        "connected": True,
        "directed_supported_comparisons": {"strict": strict, "equality": equality, "negative": 0},
        "full_ttc_checks": {"k_min": 1, "k_max": max_k_ttc, "supported_profile_runs": full_runs,
                            "all_auxiliary_pairs_swap": True},
        "fiscal_checks": {"L_range": [1, 3], "k_range": [1, 3], "ordered_set_families": instances,
                          "YES_families": yes, "NO_families": no,
                          "families_with_uncovered_elements": uncovered,
                          "supported_assignment_checks": supported_rows,
                          "full_cost_matrix_residual_checks": matrix_checks,
                          "all_residuals_exactly_zero": True},
        "off_support_diagnostic_only": {"actual_core_ttc": off_support_ttc,
              "note": "Table II is an extension, not TTC on all eight profiles. At 111 TTC is C-minus; Table II uses C-plus."},
        "all_four_requested_checks": "PASS, subject to author confirmation",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("task3a_audit.json"))
    parser.add_argument("--source-pdf", type=Path, help="Optional provenance hash; no PDF parsing or alteration")
    args = parser.parse_args()
    if args.source_pdf is not None:
        if not args.source_pdf.is_file():
            raise FileNotFoundError(args.source_pdf)
        output_is_source = args.output.resolve() == args.source_pdf.resolve()
        if args.output.exists():
            output_is_source = output_is_source or args.output.samefile(args.source_pdf)
        if output_is_source:
            parser.error("--output must not refer to the --source-pdf file")

    report = run_audit()
    if args.source_pdf is not None:
        report["source"] = {"filename": args.source_pdf.name,
                            "sha256": hashlib.sha256(args.source_pdf.read_bytes()).hexdigest()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "status", "actual_core_ttc", "directed_supported_comparisons", "full_ttc_checks",
        "fiscal_checks", "all_four_requested_checks")}, indent=2))
    print(f"Audit written to {args.output}")


if __name__ == "__main__":
    main()
