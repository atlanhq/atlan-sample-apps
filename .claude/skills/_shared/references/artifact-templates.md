# Artifact Templates

Create these artifacts for major app-building loops.

## 1) verification_manifest.json
Required fields:
- `task_id`
- `timestamp_utc`
- `task_type`
- `sdk_sources`
- `docs_sources`
- `cli_sources`
- `resolved_facts`
- `unresolved_questions`
- `status`

## 2) loop_report.md
Required sections:
- Context
- Commands Executed
- Failures
- Root Cause
- Patch Plan
- Re-run Result
- Next Action

## 3) e2e_case_contract.yaml
Required sections:
- `test_workflow_args`
- `server_config`
- `expected_api_responses`
- `expected_output_paths`
- `schema_assertions`

## Validation Scripts
- `../scripts/validate_verification_manifest.py`
- `../scripts/validate_e2e_case_contract.py`
