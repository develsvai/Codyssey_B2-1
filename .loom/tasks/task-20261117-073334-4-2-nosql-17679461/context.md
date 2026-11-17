# Context

## Loom 코드 계약

아래 항목은 Loom 코드에 고정된 runtime 동작 계약입니다. 관련 흐름을 바꾸기 전 `loom contract show <id>`로 확인합니다.

- `task-execution`: Task 실행 전 prompt/context/previous-results에 들어가는 입력 경계입니다. 명령: `loom contract show task-execution`. Source: `loom/application/context_pack.py`, `loom/application/team_policy.py`
- `done-guardrail`: Task를 DONE으로 인정하기 전에 필요한 산출물과 상태 전이를 검증하는 계약입니다. 명령: `loom contract show done-guardrail`. Source: `loom/application/services.py`

## Project Memory

# Codyssey_B2-1

Loom 프로젝트 메모리 루트입니다.

이 파일은 `loom init`으로 생성되며 `loom analyze-repo`로 보강할 수 있습니다.

## Workspace Policy

- Output language: `ko`
- Agent provider: `claude`
- Agent model: `adapter-default`
- Reasoning effort: `high`
- Required branch: `develop`
- Dirty branch switch: `blocked`
- Commit policy: `manual`
- Include `.loom` metadata in Git: `yes`
- Read-only parallel execution: `allowed`
- Validation environment: `auto`
- Previous Task result limit: `2`
- Workspace required docs: -
- Loom fixed guardrails and verified Team required policies take precedence over this Workspace Policy.

## Job

- Title: 콘솔 용돈 기입장 구현
- Goal: 미션 B2-1의 필수 기능을 구현하고 CLI → 서비스 → 입출력 저장소의 하향 의존성, 모델·검증 및 공통 관심사 분리, 스트리밍과 안전한 영구 저장을 검증한다.
- Branch: codex/budget-app
- Task count: `13`

## Task

- Title: 평가 문서 4-2를 문서형 NoSQL 검토와 쉬운 제너레이터 설명으로 개정
- Description: 사용자 요청에 따라 4-2의 확장 방향을 문서형 NoSQL 검토로 바꾸고, 선택 이유·병목 개선·메모리에 전체 거래를 쌓지 않는 의미를 쉬운 예시로 설명한다.
- Expected output: docs/evaluation-answers.md 4-2 항목 개정 및 Loom 작업 결과
- Done condition: 제너레이터의 메모리 효과와 검색 비용을 구분하고 문서형 NoSQL 선택 근거·인덱스·개별 갱신·집계·전환 한계를 쉽게 설명하며 다른 항목과 앱 코드는 유지한다.
- In scope: 평가 문서 4-2의 답변과 설명 수정, 코드 및 기술 근거 대조, 문서 검증
- Out of scope: 실제 NoSQL 도입, 성능 최적화 구현, 다른 평가 항목 변경, 애플리케이션 및 데이터 수정
- Validation hint: 4-2 한정 변경 확인; 예제·링크·코드 근거 대조; git diff --check; loom validate --strict
- Required docs: -
- Memory refs: -
- Document outputs: `docs/evaluation-answers.md`
- Document output exceptions: -
- Source proposal: `-`
- Status: PENDING
- Assigned agent: codex

## Advisor Source Prompt

No Advisor source prompt recorded for this Task.

## Inclusion Policy

- Mandatory execution files: `prompt.md`, `context.md`, and `previous-results.md`.
- Always included: project memory, current Job/Task metadata, and Job notes.
- Previous results: up to the latest 2 recorded results from earlier Tasks in this Job.
- Job context refs: explicit Job-scoped references selected by the controlling agent or user.
- Task required docs: mandatory Task-scoped documents; missing refs block validation and execution.
- Task memory refs: mandatory Task-scoped workflow memory references; missing or non-memory refs block validation and execution.
- Repository documents, validation documents, and skill rules: included only through explicit Job context refs, Task required docs, or Task memory refs.
- Verified Team Policy Snapshot: included before Active Memory; required policy cannot be overridden by lower-priority context.
- Active workflow memory with an `always` category is included automatically while its status is `ACTIVE`.
- `task_selected` and `reference_only` memory is included only through explicit Task memory refs.
- Consumed proposals, rejected proposals, resolved memory, superseded memory, and archived memory are excluded.
- Unreferenced repository files and results from other Jobs are not included.
- `AGENTS.md` and `CLAUDE.md` remain session-level controlling-agent entrypoints and are not treated as task context artifacts by default.

## Job Notes

# Notes

## Context References

No explicit context references recorded for this job.

## Required Documents and Memory

No task-level required docs or memory refs recorded.

## Verified Team Policies

No verified Team Policy Snapshot is active.

## Active Workflow Memory

No active workflow memory recorded.
