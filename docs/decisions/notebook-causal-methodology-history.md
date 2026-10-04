# Notebook and causal-methodology history — non-normative

This record preserves historical ChatGPT methodological rationale supplied by
project owner in the final preservation request received on **2026-10-04**.
It is informative historical material, outside the frozen contract bundle.
It adds no product requirement, repair, approval, execution, or causal claim.

The original critique and analysis dates, earlier notebook identity, original
message identifiers, and complete source transcript are **unavailable**. The
recovered summary below is the evidence retained; those missing details are
not reconstructed. No attribution of the earlier defects to the accepted
portfolio notebook is inferred.

## Recorded portfolio demonstration

The historical portfolio design describes a read-only notebook demonstration
over an already recorded synthetic run. The notebook does not generate a new
sample. Its status is `NON_CANONICAL_DEMO`; its claim status is
`CALCULATION_ONLY_NO_CAUSAL_CLAIM`.

| Historical design item | Preserved conclusion |
|---|---|
| Cohort flow | 55,000 screened → 50,000 randomized. |
| Assignment counts | 25,000 treatment / 25,000 control. |
| Assignment design | Strict 1:1 assignment across 16 blocks. |
| Estimand | Assignment-level intention-to-treat (ITT). |
| Receipt status | Reached, accepted, refused, and not-reached are post-randomization variables; they must not replace treatment assignment in the ITT contrast. |
| Customer journeys | Views describe chronology and mechanism, without identifying individual causal effects. |
| Funding outcome | Funding initiation is not equivalent to qualifying settlement. |

The existing [notebook documentation](../../notebooks/README.md) describes the
saved readout and its recorded artifacts. The [demo documentation](../../examples/README.md)
records the synthetic run, public fabricated input, fabricated demonstration
approvals, cohort counts, and accepted production calculation. These links
preserve the distinction between a completed portfolio calculation and real
human approvals, empirical evidence, or canonical/hidden-seed acceptance.

## Recovered critique of an earlier notebook/analysis route

The owner supplied the following historical methodological conclusions about
an earlier route whose exact artifact identity is unavailable:

- Significance-based filtering of format×region strata biased the reported effect.
- PRE p > .05 was incorrectly treated as proof of balance.
- 1:1 matched observations were analyzed as independent samples instead of paired differences.
- Post-hoc power was circular.
- 32 tests lacked multiplicity discipline.
- Bootstrap procedures broke matched pairs.
- One two-sided bootstrap p-value calculation omitted the factor of two.
- The claimed normality check did not actually test normality.

These are retained as the recovered critique. They are not a newly performed
audit, a finding that the accepted Slice 1 implementation or portfolio notebook
contains these defects, or a reconstruction of unavailable R1–R4 findings.

## Recovered recommended analysis order

The historical recommendation for the earlier matched-analysis route was:

```text
overlap / balance / standardized mean differences (SMD)
    → all design-eligible strata
    → paired differences
    → ATT, standard error (SE), 95% confidence interval (CI), raw p-value
```

Do not use significance gates to select strata. Power should be defined ex ante
from a minimum detectable effect (MDE), rather than inferred post hoc.

This recommendation concerns the recovered matched-analysis route and its
average treatment effect on the treated (ATT). It does not replace the frozen
randomized Slice 1 assignment-level ITT estimator or its Neyman variance
calculation. The authoritative specifications remain the
[Contract Bundle v0.2.7](../../contracts/Contract_Bundle_v0.2.7.md) and its normative
members, including the
[Statistical Analysis Plan v0.4.0](../../contracts/Statistical_Analysis_Plan_v0.4.0.md).

## Preservation boundary and remaining provenance

This final historical-preservation delta captures the supplied conclusions;
no further archaeology, original wording reconstruction, review loop, or
methodology change is authorized by it. Unavailable original dates, notebook
identity, full transcript, message IDs, and attribution remain **forensic /
historical only (category B)**. They are not required to understand, reproduce,
review, or continue the accepted Slice 1 artifact under its existing frozen
specifications and repository evidence.
