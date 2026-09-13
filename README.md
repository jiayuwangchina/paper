# Task 3A: targeted four-check audit

 This is new research-audit material, not
replacement manuscript text and not a verification of the complete strengthened
NP-completeness argument. No manuscript file is changed by the script.

## Source and scope

The source is `Main_Manuscript_Econometrica(2).pdf`, dated 12 September 2026.
Inputs are transcribed from equation (1), Section 4.2, equation (17), and
Section 5.2. Tables I-IV are cross-checks, not a substitute for running TTC.
The proposed support is {100,110,010,011,001,101}.

## Run

Requires Python 3.9 or later and only the standard library:

```sh
python verify_task3a.py --output task3a_audit.json
```

To record an optional provenance hash (the PDF is read only for the hash):

```sh
python verify_task3a.py --output task3a_audit.json --source-pdf "Main_Manuscript_Econometrica(2).pdf"
```

## Findings 

1. Actual TTC gives core allocations (13) at 100/110, (12) at 010/011,
   and (23) at 001/101. Every selection and balancing pair swaps.
2. All three strategically active workers have an allocation-changing supported
   edge: worker 1 at 010--110, worker 2 at 001--011, worker 3 at 100--101.
3. Both directed truthful-report surpluses on these edges are strictly positive:
   3/5 for worker 1, 1/10 for worker 2, and 3/5 for worker 3. Across all six
   supported edges there are six strict directed comparisons, six equality
   comparisons, and no violations.
4. Supported allocations have t(g)=0 and all selection and balancing swap
   indicators equal to one. All block, synchronization, and element-coordinate
   residuals are zero. Equation (20) reduces to 0-H_ell+H_ell=0.

## Exact finite checks

- All six core TTC profiles computed from exact rational utilities.
- Full economies with k=1,...,12: 72 supported-profile TTC runs; all pairs swap.
- Every ordered family of k=1,2,3 nonempty subsets of a universe of size L=1,2,3:
  441 families, including repeated sets and uncovered elements.
- 279 of these families have an exact cover and 162 do not; 114 have an uncovered
  element. These are audit cases, not policy observations or statistical samples.
- 2,646 supported-allocation fiscal checks and 15,120 direct cost-matrix residual
  evaluations; every residual equals zero as an integer.

The finite checks are not a proof for all source-instance sizes. The accompanying
response gives the algebraic cancellation and the TTC separation reasoning.

## Important diagnostic 

At 111 actual TTC is C-minus=(132), whereas Table II selects C-plus=(123).
There is no conflict: Table II is a DSIC extension, not an assertion that it equals
TTC at all reports. They agree at all six proposed supported profiles. No table
is modified by this audit.

## Deliverables

- `verify_task3a.py`: exact-arithmetic checker; no random numbers, floating point,
  external packages, network calls, or manuscript writes.
- `task3a_audit.json`: generated results and the provenance hash of the source PDF.

Pending: original LaTeX for Sections 5 and 7, the approved patch merge and
source-level preservation comparison, and author review of any new theorem.
