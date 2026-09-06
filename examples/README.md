# NON_CANONICAL_DEMO — accepted Slice 1 demonstration

This is one fabricated synthetic realization using a fixed public non-secret
input. It is **not hidden-seed acceptance, empirical brokerage evidence, a real
human approval, or evidence about bias, coverage, power or method superiority**.

The runner composes the accepted production capabilities at
`db507f05928d07f39044a64171cfbe6af1769502`. It verifies their source bytes and the
frozen v0.2.7 contracts before running. No core code or contract bytes change.

## Reproduce

From the WSL repository root, under the existing pinned environment:

```sh
PYTHONPATH=src .venv/bin/python -u examples/run_slice1_demo.py
```

The default output is
`outputs/demo_slice1/NON_CANONICAL_DEMO/`. Existing outputs are refused. To
reproduce into a fresh location:

```sh
PYTHONPATH=src .venv/bin/python -u examples/run_slice1_demo.py \
  --output-dir outputs/demo_slice1_replay
```

The complete run performs substantial full-cohort generation and repeated
authentication; allow several minutes. Progress messages identify each stage.
The runner accepts only an output-directory option, with no seed discovery,
seed override, configuration selection or fallback behavior.

The public fixture is the SHA-256 hexadecimal encoding of the ASCII phrase
`NON_CANONICAL_DEMO_PUBLIC_FABRICATED_SEED_2026_09_06_V1`. This provides the exact
64-lowercase-hex input required by the accepted custody interface. Production
then commits/verifies the SHA-256 of that input's exact ASCII bytes. The phrase,
public input and commitment are recorded in `demo_inputs.json`, outside all
authoritative packages. These values have no connection to the canonical seed.

The configuration ID remains the frozen
`CANONICAL_TARGETED_STRESS_TEST_V0.3` target card; that existing name does not
make this public-input run canonical. Run IDs, fabricated approver IDs, reasons,
archive/commitment labels, directory ancestry and all demo presentation files
carry `NON_CANONICAL_DEMO`. Schema-fixed payloads and sidecars inherit the
directory label: the runner never inserts extra fields or changes frozen bytes.

## Production flow and files

- Checkpoint4Run: validates contracts and commits the pre-outcome assignment
  sequence, calls generate_packages for both packages from one realization,
  freezes the LOCAL_BYTES_VERIFIED scan, authenticates the signed dataset release,
  then emits randomization_audit.json and baseline_balance.json.
- Checkpoint5Analysis: receives only public analyst inputs, validates descriptive
  diagnostics, accepts a fabricated Gate D and emits primary_itt_result.json/.md.
- Checkpoint6Run: freezes the analysis, records the existing Slice 1 Gate F/G
  dispositions, closes the archive, verifies the explicit public seed receipt,
  accepts fabricated Gate H before unblinding, compares and closes the benchmark.

All approval inputs are explicitly fabricated demonstrations passed through
unchanged validators, not real human authorization. The runner calls the existing
predecessor-binding helpers; it does not invent gates, signatures, hash domains,
governance states, exposure classes or package exceptions.

Output layout:

```text
NON_CANONICAL_DEMO/
  README.md
  demo_inputs.json
  summary.json
  summary.md
  demo_file_inventory.json
  public/               # authoritative analyst/release/audit/analysis/freeze/close files
    analyst/            # exactly four analyst tables with accepted manifest/sidecar
    ...                 # accepted records and closed archive
  custody/oracle/       # isolated complete oracle package from the same realization
  exposure_registry/    # original genesis and authorized-unblind records
```

The demo summary copies the production primary and authorized comparison values;
multiplication by 100 is only presentation in percentage points. It neither
recalculates the estimator nor reads oracle payloads to construct another truth.
Freeze-before-comparison evidence uses the accepted lifecycle history and the
hash of the unchanged primary result. The inventory is a demo presentation aid,
not a new normative run artifact, and lists exact bytes/hashes of all other
output files.

The accepted core commit is the runtime code binding. A separate runner digest
in demo_inputs.json identifies the demonstration wrapper. Fixed inputs and
fabricated timestamps make the authoritative bytes reproducible independently
of the chosen output location. Replays use separate explicitly fabricated
directories; they do not reset any real or canonical exposure history.

## Verification

```sh
.venv/bin/python -m pytest -q tests/test_slice1_demo.py \
  tests/test_contracts.py tests/test_execution_environment.py
```

The five lightweight demo tests check production capability bindings, absence
of duplicated DGP/estimator dependencies, fixed accepted-format public inputs,
direct result projection and output isolation/overwrite refusal. The selected
suite passes **170 tests** under unchanged CPython 3.12.3 and requirements-dev.lock,
with no version overrides. The full accepted core regression suite is not rerun
for this wrapper-only change; the full demo exercises the production lifecycle.

One complete end-to-end run finished at BENCHMARK_CLOSED. The initial descriptive
seed-format preflight was rejected before output creation or cohort generation;
the fixed public phrase was then encoded to the accepted format. No generated
realization was discarded, reseeded or rerolled.

The final selected test run passed 170 tests in 16.45 seconds. The offline wheel
build passed with --no-index --no-deps --no-build-isolation --no-cache-dir; all
51 packaged Python modules match accepted source bytes. All 16 release checksums
pass, all 17 contract files and all 51 source modules remain byte-identical to
the accepted commit, and Git whitespace checks pass.

The output contains 87 files (883,416,394 bytes). The demo inventory verifies
the exact membership, sizes and SHA-256 of the other 86 files. All 25 public JSON
records use accepted schemas; run-enveloped records carry the demo run ID, and
the assignment commitment retains its frozen schema. Analyst payload membership
is exactly four tables; the two balance artifacts contain identical 45-row
diagnostics across OVERALL, KYC_FRICTION_0 and KYC_FRICTION_1.

## Completed NON_CANONICAL_DEMO results

Values below are copied from summary.json and authoritative production results.
Effects, standard error, and confidence limits are in probability units unless
percentage points are stated explicitly.

| Quantity | Value |
| --- | --- |
| screened_n | 55000 |
| randomized_n | 50000 |
| excluded_n | 5000 |
| treatment_n | 25000 |
| control_n | 25000 |
| treatment_primary_outcome_rate | 0.21224 |
| control_primary_outcome_rate | 0.20064 |
| itt_probability_units | 0.0116 |
| itt_percentage_points | 1.16 |
| standard_error | 0.0035804721705631026 |
| ci_95 | [0.004582403498048364, 0.018617596501951633] |
| p_value | 0.0011961517507138417 |
| probability_scale_truth | 0.013299999988454499 |
| finite_schedule_truth | 0.01318 |
| estimate_minus_finite_truth | -0.0015800000000000015 |
| estimate_minus_probability_truth | -0.0016999999884544995 |
| ci_contains_finite_truth | true |
| ci_contains_probability_truth | true |
| analysis_frozen_before_oracle_comparison | true |
| lifecycle | "BENCHMARK_CLOSED" |

The run-level summary and exact output inventory are available at
[summary.md](../outputs/demo_slice1/NON_CANONICAL_DEMO/summary.md) and
[demo_file_inventory.json](../outputs/demo_slice1/NON_CANONICAL_DEMO/demo_file_inventory.json).
Generated outputs are retained locally and ignored by Git. No canonical seed
was accessed or used; no HTE, economics, policy, ML/AI/agents or UI was added.
