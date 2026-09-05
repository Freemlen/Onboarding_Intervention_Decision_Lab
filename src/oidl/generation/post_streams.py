"""Isolated post-assignment draw registry, DGP §§6 and 17.1–17.1.3."""
from hashlib import sha256
import re

import numpy as np

from oidl.domain.contracts import ContractError
from oidl.generation.streams import NUMPY_VERSION

POST_DRAWS = {}
for namespace, names in {
    "delivery_u": ("control_contamination_u", "package_attempt_u", "package_reach_u",
                   "package_accept_u", "followup_seen_u", "callback_request_u",
                   "callback_completion_u", "bau_assistance_u"),
    "verification_u": ("resolution_u",),
    "funding_u": ("initiation_u", "qualifying_settlement_u", "main_nonsuccess_status_u",
                  "repeated_failure_u", "optional_extra_event_u"),
    "event_times": ("initial_attempt_time_u", "callback_request_time_u",
                    "callback_completion_time_u", "main_nonsuccess_status_time_u"),
    "guardrails": ("unwanted_u", "complaint_u", "product_protection_u",
                   "unwanted_time_u", "complaint_time_u", "product_protection_time_u"),
}.items():
    for variable in names:
        POST_DRAWS[namespace, variable] = ("uniform", (), (55000,))
POST_DRAWS.update({
    ("latent_vector", "base_standard_normals"): ("normal", (), (55000, 5)),
    ("funding_u", "extra_event_status_u"): ("uniform", (), (55000, 3)),
    ("event_times", "nonsuccess_time_u"): ("uniform", (), (55000, 3)),
    ("event_times", "bau_time_beta_2_3"): ("beta", (2, 3), (55000,)),
    ("event_times", "downstream_dirichlet_friction"): ("dirichlet", (2, 2, 1, 3), (55000, 4)),
    ("event_times", "downstream_dirichlet_no_friction"): ("dirichlet", (2, 1, 3), (55000, 3)),
    ("fidelity_duration", "initial_help_beta_2_3"): ("beta", (2, 3), (55000,)),
    ("fidelity_duration", "callback_help_beta_2_3"): ("beta", (2, 3), (55000,)),
    ("fidelity_duration", "declined_beta_2_5"): ("beta", (2, 5), (55000,)),
})
CORRELATION = np.array([
    [1, .25, .15, .20, -.10],
    [.25, 1, .20, .15, -.10],
    [.15, .20, 1, .10, -.15],
    [.20, .15, .10, 1, -.05],
    [-.10, -.10, -.15, -.05, 1],
])
CORRELATION.flags.writeable = False


def post_assignment_draws(seed_hex):
    """Explicit injection only; no discovery, file reads, seed persistence or logging."""
    if type(seed_hex) is not str or re.fullmatch(r"[0-9a-f]{64}", seed_hex) is None:
        raise ContractError("POST_ASSIGNMENT_INPUT", "INVALID_SEED_ENCODING")
    if np.__version__ != NUMPY_VERSION:
        raise ContractError("POST_ASSIGNMENT_INPUT", "NUMPY_VERSION_MISMATCH")
    draws = {}
    for (namespace, variable), (kind, params, shape) in POST_DRAWS.items():
        parent = sha256(seed_hex.encode("ascii") + b"|" + namespace.encode("ascii")).digest()
        child = sha256(parent + b"|" + variable.encode("ascii")).digest()
        rng = np.random.Generator(np.random.PCG64(int.from_bytes(child[:16], "big")))
        if kind == "uniform":
            array = rng.random(shape)
        elif kind == "normal":
            array = rng.standard_normal(shape)
        elif kind == "beta":
            array = rng.beta(*params, size=shape)
        else:
            array = rng.dirichlet(params, size=shape[0])
        array.flags.writeable = False
        draws[variable] = array
    return draws


def latent_rows(draws):
    return draws["base_standard_normals"] @ np.linalg.cholesky(CORRELATION).T
