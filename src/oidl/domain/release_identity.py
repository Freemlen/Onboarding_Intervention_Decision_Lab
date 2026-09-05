"""Pinned identities transcribed from the verified frozen v0.2.6 release.

Source: Contract Bundle sections 2/4, ResearchSpec specification, SHA256SUMS.txt.
These are release constants, never refreshed from input at runtime.
"""

RELEASE = "0.2.6"

NORMATIVE_PATHS = ('Architecture_v0.2.6.md',
 'Contract_Bundle_v0.2.6.md',
 'DGP_Parameter_Sheet_v0.3.0.md',
 'Decision_Rule_Spec_v0.3.0.md',
 'Golden_Fixtures_v0.2.6.yaml',
 'Guardrail_Spec_v0.3.0.md',
 'Oracle_Benchmark_Spec_v0.4.0.md',
 'ResearchSpec_v0.2.6.md',
 'ResearchSpec_v0.2.6.yaml',
 'Slice_1_Definition_of_Done_v0.2.6.md',
 'Statistical_Analysis_Plan_v0.4.0.md')

RELEASE_HASHES = {'Architecture_v0.2.6.md': 'b7917b7d2b098d3a9e4c192d07b831b926b74473e93c33e212b32e472ea8b27a',
 'CHANGELOG_v0.2.6.md': '329589893e3575f9ec963b83e51b8b0bc497956d737b5968fae5700f114c4c72',
 'Contract_Bundle_v0.2.6.md': 'f7710fc07a98f3f0703f4d3bf2286fd87e9d1ada86fd398fa23646a4f8a66327',
 'DGP_Parameter_Sheet_v0.3.0.md': '4370f133ab9ac526c6b2aacdefd0aae6adfb1289ceed17e2ecbfe81ff8bbf1e3',
 'Decision_Rule_Spec_v0.3.0.md': 'f748f87c3192732908ea0114f3139ccac9a443fd1e16916983fe5b71f520e23a',
 'Final_Consistency_and_Regression_Audit_v0.2.6.md': '009d7269e295f4116117a32dbbd4fb902d1f57c6b2670361d2d80058bf41f43a',
 'Finding_Resolution_Matrix_v0.2.6.md': '7f4588698544c178798cda7bae5384b1b85934863fb441ef21003f112643f1dc',
 'Golden_Fixtures_v0.2.6.yaml': 'a4a7fe0da0b3b16e7fbaff96e216577b4ffb6bfd4460defbb060661ee59e42f7',
 'Guardrail_Spec_v0.3.0.md': '0fffe186508ab7d7e7f93509d96d43291195f4a29711478a5037ea61cf7c1b9a',
 'Oracle_Benchmark_Spec_v0.4.0.md': 'f238b8e549514c9496c71bcbc1659d62c3f5c544632865780e66ca287cc632b2',
 'README.md': 'd8d63bc0786510998d38cabb8ab77a55ba51b7ed0fe4a61b3a608e41ba1b955d',
 'ResearchSpec_v0.2.6.md': '00176398e772721dc2c8eac3322531f117408fdfd6cfcaea3f94a923962ce5b8',
 'ResearchSpec_v0.2.6.yaml': 'a8f60d8eb2ea93bef1f5e782b95a2e648d2fab063bcd02820439fb10e3fb5e2d',
 'Slice_1_Definition_of_Done_v0.2.6.md': 'f10844ad53c93ece2bc0524186344649116aece9c0b1d7a85f085acb6ec7003b',
 'Statistical_Analysis_Plan_v0.4.0.md': '9c9622aa91de236031c664dec76a41ca5706f50fffd61a874b32b8d8694b8b1d',
 'validation_results.json': '045c19e0050117b13a221a3cfec926351f23978f81f23d17d720695d1d8de081'}

LINKED_CONTRACTS = {'architecture': 'Architecture_v0.2.6',
 'contract_bundle': 'Contract_Bundle_v0.2.6',
 'decision_rule': 'Decision_Rule_Spec_v0.3.0',
 'dgp_parameter_card': 'DGP_Parameter_Sheet_v0.3.0',
 'golden_fixtures': 'Golden_Fixtures_v0.2.6',
 'guardrails': 'Guardrail_Spec_v0.3.0',
 'oracle_protocol': 'Oracle_Benchmark_Spec_v0.4.0',
 'slice_1': 'Slice_1_Definition_of_Done_v0.2.6',
 'statistical_analysis_plan': 'Statistical_Analysis_Plan_v0.4.0'}

SEMANTIC_VERSIONS = {'architecture': '0.2.6',
 'decision_rule': '0.3.0',
 'dgp': '0.3.0',
 'golden_fixtures': '0.2.6',
 'guardrails': '0.3.0',
 'oracle_protocol': '0.4.0',
 'research_spec': '0.2.6',
 'sap': '0.4.0',
 'slice_1': '0.2.6'}

# SAP v0.4.0 §4.3; independent of the primary estimator and SAP versions.
BALANCE_METHOD_ID = "OIDL-PRE-T0-BALANCE-SMD"
BALANCE_METHOD_VERSION = "1.0.0"
