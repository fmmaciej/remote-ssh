# Initial integrated result — round 0

- Basis: [baseline manifest](baseline-1/baseline.json), unchanged R5 accepted repair contract.
- Plan: [round-0 execution mapping](plan-r0.md).
- Technical owner: `/root/flyline_implementer`; coordinator executed supplied helpers across the external filesystem approval boundary without changing their design.
- Result: F1–F4 implemented and functional checks pass; startup qualification remains unmet. Full SDD task is incomplete.
- Evidence and limitations: [repair R1 record](../../../flyline-integration-repair-r1-record.md).
- Full checks: 1551 passed, 56 skipped plus Bash syntax/ShellCheck/Ruff/mypy; focused 147/26; related 108; native ownership 32/32, lifecycle 4/4, history 3/3; final diff/local links green.
- Startup: both valid 8×20 runs fail cold Atuin overhead; no waiver or sampling reinterpretation. Paired causal diagnostics do not replace acceptance.
- Next: independent audit against the same frozen basis, including performance noncompliance and any ordinary technical regressions.
