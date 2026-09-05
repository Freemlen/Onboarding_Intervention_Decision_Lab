"""Only pre-outcome namespaces/draws from DGP §§17.1–17.1.3."""

from hashlib import sha256
import re

import numpy as np

from oidl.domain.contracts import ContractError
from oidl.domain.design import SCREENED_N

NUMPY_VERSION = "2.1.3"
PRE_OUTCOME_DRAWS = {
    ("context_categories", name): ("uniform", (SCREENED_N,))
    for name in (
        "acquisition_channel_u", "device_verification_route_u", "language_service_match_u",
        "declared_experience_u", "registration_shift_u", "local_utc_offset_u",
        "registration_time_u",
    )
}
PRE_OUTCOME_DRAWS.update({
    ("context_categories", "day_shift_load_z"): ("normal", (28, 3)),
    ("pre_t0_states", "completed_step_count_u"): ("uniform", (SCREENED_N,)),
    ("pre_t0_states", "pre_t0_deposit_time_u"): ("uniform", (SCREENED_N,)),
})


def namespace_digest(seed_hex, namespace):
    if type(seed_hex) is not str or re.fullmatch(r"[0-9a-f]{64}", seed_hex) is None:
        raise ContractError("PRE_OUTCOME_INPUT", "INVALID_SEED_ENCODING")
    if namespace not in ("population", "assignment", "context_categories", "pre_t0_states"):
        raise ContractError("PRE_OUTCOME_INPUT", "NAMESPACE_OUTSIDE_CHECKPOINT")
    return sha256(seed_hex.encode("ascii") + b"|" + namespace.encode("ascii")).digest()


def pre_outcome_draws(seed_hex):
    if np.__version__ != NUMPY_VERSION:
        raise ContractError("PRE_OUTCOME_INPUT", "NUMPY_VERSION_MISMATCH")
    draws = {}
    for (namespace, variable), (kind, shape) in PRE_OUTCOME_DRAWS.items():
        parent = namespace_digest(seed_hex, namespace)
        child = sha256(parent + b"|" + variable.encode("ascii")).digest()
        generator = np.random.Generator(np.random.PCG64(int.from_bytes(child[:16], "big")))
        array = generator.random(shape) if kind == "uniform" else generator.standard_normal(shape)
        array.flags.writeable = False
        draws[variable] = array
    return draws
