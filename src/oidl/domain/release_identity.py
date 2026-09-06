"""Pinned identities from verified frozen v0.2.7 (Bundle §§2–4; Oracle §2.4.1).

These are release constants, never refreshed from inputs at runtime.
"""

RELEASE = "0.2.7"

NORMATIVE_PATHS = ('Architecture_v0.2.7.md',
 'Contract_Bundle_v0.2.7.md',
 'DGP_Parameter_Sheet_v0.3.0.md',
 'Decision_Rule_Spec_v0.3.0.md',
 'Golden_Fixtures_v0.2.7.yaml',
 'Guardrail_Spec_v0.3.0.md',
 'Oracle_Benchmark_Spec_v0.5.0.md',
 'ResearchSpec_v0.2.7.md',
 'ResearchSpec_v0.2.7.yaml',
 'Slice_1_Definition_of_Done_v0.2.7.md',
 'Statistical_Analysis_Plan_v0.4.0.md')

RELEASE_HASHES = {'Architecture_v0.2.7.md': 'bed4a1b78f99ec0eb3555a3f6a88ee58c18c3d71543642fa1ae3c3d46a342aa9',
 'CHANGELOG_v0.2.7.md': 'd26fdf7c723354b8de4eb585797079b6fc916fdf908fbb60861c6642f120dc89',
 'Contract_Bundle_v0.2.7.md': 'fb013604d824e157ecbaeb75ce670c20cadfac702dd5132601eac01e4334b67d',
 'DGP_Parameter_Sheet_v0.3.0.md': 'a5318803952a342aaaf47d016255703b286b81f08a51ff6d6dc703c729b79d65',
 'Decision_Rule_Spec_v0.3.0.md': 'cacc19e81911ddcea5b8a22796e51941a5a59fd3bbbb57df613e6696cd9a31e7',
 'Final_Consistency_and_Regression_Audit_v0.2.7.md': '18c41952285b2d65184999391d17aadf75dfc18695842ce92102ebac9fb774d7',
 'Finding_Resolution_Matrix_v0.2.7.md': '8d52c5f96013f422da6f0f546a4f5af4fb62bd2bc3ad12bc67d85f66cccfa1ea',
 'Golden_Fixtures_v0.2.7.yaml': '598377cbc942eda427191b63d7c1e15813bfd1cf3aab90a4be97131908048905',
 'Guardrail_Spec_v0.3.0.md': '0fffe186508ab7d7e7f93509d96d43291195f4a29711478a5037ea61cf7c1b9a',
 'Oracle_Benchmark_Spec_v0.5.0.md': '1a07024ee16fd6d39ab10750fa3e92fe28dafd95e3e182704b171f30fb041bbb',
 'README.md': '6433d73762701f9df19863e684ceff5a07737b6e44a7c4fea9144824efbd55b3',
 'ResearchSpec_v0.2.7.md': '0e4a6d2fd522f064f87f9e041475680fd38bfa7578f3c15d5fe87eec3665abb7',
 'ResearchSpec_v0.2.7.yaml': '6bb6d6acc8cf13fb86f229f1e71601b328b87c791ea65912444f0da98403a4fe',
 'Slice_1_Definition_of_Done_v0.2.7.md': 'd5fe0425d51b709d398b3b94eb7e954197da56cd7a16a9e793a3ff104afbd2f2',
 'Statistical_Analysis_Plan_v0.4.0.md': '8d2f917687198c4f50bc133a048319304ac5a2ef9a194e2a760e09dff09b5d61',
 'validation_results.json': '8537924e30092b019eb9acbbfa4a2cb20e843172680c77cab5809389734520d8'}

LINKED_CONTRACTS = {'architecture': 'Architecture_v0.2.7',
 'contract_bundle': 'Contract_Bundle_v0.2.7',
 'decision_rule': 'Decision_Rule_Spec_v0.3.0',
 'dgp_parameter_card': 'DGP_Parameter_Sheet_v0.3.0',
 'golden_fixtures': 'Golden_Fixtures_v0.2.7',
 'guardrails': 'Guardrail_Spec_v0.3.0',
 'oracle_protocol': 'Oracle_Benchmark_Spec_v0.5.0',
 'slice_1': 'Slice_1_Definition_of_Done_v0.2.7',
 'statistical_analysis_plan': 'Statistical_Analysis_Plan_v0.4.0'}

SEMANTIC_VERSIONS = {'architecture': '0.2.7',
 'decision_rule': '0.3.0',
 'dgp': '0.3.0',
 'golden_fixtures': '0.2.7',
 'guardrails': '0.3.0',
 'oracle_protocol': '0.5.0',
 'research_spec': '0.2.7',
 'sap': '0.4.0',
 'slice_1': '0.2.7'}

# Unchanged SAP §4.3; separate from primary and Oracle protocol versions.
BALANCE_METHOD_ID = "OIDL-PRE-T0-BALANCE-SMD"
BALANCE_METHOD_VERSION = "1.0.0"

# Oracle v0.5.0 §2.4.1. The domain ID is NOT part of the byte preimage.
RESEARCH_SPEC_SOURCE = "ResearchSpec_v0.2.7.yaml"
RESEARCH_SPEC_TWIN = "ResearchSpec_v0.2.7.md"
RESEARCH_SPEC_HASH_DOMAIN = "OIDL-RESEARCHSPEC-YAML-FILE-SHA256-v1"
