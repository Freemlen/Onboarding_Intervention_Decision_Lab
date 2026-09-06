# Portfolio demo notebook

Open Onboarding_Intervention_Decision_Lab_Demo.ipynb for the saved, executed
NON_CANONICAL_DEMO readout. It reads the already-completed demo artifacts under
outputs/demo_slice1/NON_CANONICAL_DEMO/ and does not regenerate data or inference.

Execute once, from the repository root, using the unchanged supported environment:

```sh
.venv/bin/python notebooks/execute_demo_notebook.py
```

The notebook uses ordinary Python, standard display MIME bundles and embedded
SVG/HTML. The pinned environment has no pandas, matplotlib or Jupyter packages;
the small offline executor supplies display capture and a shared cell namespace.
It is a cell execution helper, not a Jupyter kernel or security sandbox. The
notebook also uses ordinary display calls understood by a Python Jupyter kernel
when one is separately available. No additional dependency is required or installed.

Eight code cells produce six visuals: cohort flow, three observed customer
journeys, the largest absolute stored SMDs, primary rates/ITT interval, recorded
freeze order, and the authorized analyst/oracle comparison. All 45 balance
diagnostics are available in the balance_rows variable; only eight are plotted.
Short narrative cells provide the eleven-step story and a 60-second interview
explanation. Input cells carry hide-input/source_hidden metadata.

Only original public analyst artifacts are read before the oracle section. Later
cells read the existing authorized overall comparison; no custody payload, latent
variables, individual potential outcomes, generator coefficients or seed inputs
are read. All paths are repository-relative. Artifact membership/hashes and
freeze/authorization bindings are checked without estimating or generating again.

Lightweight checks:

```sh
.venv/bin/python -m pytest -q tests/test_demo_notebook.py tests/test_slice1_demo.py
```

This is a synthetic portfolio case: not Exness data or process, empirical
brokerage evidence, production security, canonical hidden-seed acceptance, or
repeated-simulation estimator validation. No HTE/economics/policy/ML is added.

Verification: all eight code cells executed top-to-bottom once under the unchanged
pinned environment. The ten notebook/demo smoke tests passed. All six saved
figures were rasterized with an existing external preview tool and visually
inspected; that tool is not a notebook dependency. The accepted source, demo
runner and all 17 contract files remain byte-identical; all 16 contract
checksums pass. All 87 existing demo files are preserved, their 86 inventoried
hashes verify, and the recorded primary/freeze/comparison/close hashes match
the completed demo. No new cohort, inference, release or oracle operation ran.
