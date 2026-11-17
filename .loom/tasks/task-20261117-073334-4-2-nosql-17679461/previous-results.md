# Previous Results

10 older recorded result(s) were omitted. Promote durable context to Job Notes or explicit Context References.

## 11. CSV export 월·기간 교집합 조건 구현 및 검증

# 결과

CSV export의 월 조건과 날짜 범위를 함께 지정할 수 있도록 보완했다. 기존 월 단독·기간 단독 동작을 유지하며, 동시 지정 시 양쪽에 포함되는 거래만 스트리밍으로 내보낸다.

## 산출물

- `budget_app/services/transfer.py`: 완전한 날짜 범위 검증 후 월 필터와 날짜 필터를 AND로 적용. 유효하지만 겹치지 않는 조건은 0건 성공.
- `budget_app/cli/commands/transfer.py`: 교집합 정책을 도움말에 반영.
- `tests/test_transfer.py`, `tests/test_cli.py`: 경계·윤년·빈 교집합·잘못된 조건의 파일 보존·실제 CLI 회귀 테스트 5개 추가.
- `README.md`, `docs/architecture.md`, `docs/validation.md`, `docs/mission-checklist.md`: 예시·동작 정책·검증 결과 갱신.

## 검증

- Python 3.14.4: `python3 -W error::ResourceWarning -m unittest discover -q` — 70개 통과.
- Python 3.11.16: `python3.11 -W error::ResourceWarning -m unittest discover -q` — 70개 통과.
- 전체 테스트의 구조 검사로 하향 의존성, 순환 참조 금지, 서비스 간 참조 금지, 하위 계층의 콘솔 I/O 금지 확인.
- 앱과 테스트 50개 Python 파일의 Python 3.10 문법 파싱 통과. `git diff --check` 통과.
- `loom validate --strict` — 1 Job, 11 Task 메타데이터 정상.

## 남은 사항

이번 작업 범위의 미완료 항목이나 알려진 결함은 없다. Python 3.10 런타임 검증은 미실시이며 기존 선택 과제 제외 범위를 유지한다.

## 12. 평가 항목별 구현 설명과 발표 답변 문서 작성

# 결과

사용자가 제시한 4개 항목의 16개 질문을 `docs/evaluation-answers.md`에 정리했다. 각 질문은 발표용 답변, 실제 구현 설명, 코드 및 테스트 근거를 포함한다. README에 안내 링크를 추가했다.

## 포함 내용

- 8개 명령, JSONL 저장 파일 3개와 재실행 보존, 카테고리 참조 정책, 예산 사용률, CSV 스키마, 오류와 종료 코드.
- 기능별·계층별 모듈 책임, 모델·서비스·저장소의 클래스 경계, 임시 파일 교체 및 쓰기 잠금.
- 제너레이터의 지연 실행과 메모리 이점·시간 한계, 두 데코레이터, 실제 타입 힌트와 런타임 검증의 구분.
- JSONL/CSV 비교, 10만 건에서 예상되는 병목과 미구현 개선안, CSV 전체 반영 취소와 재시도 정책.
- 별도 임시 폴더에서 실행할 수 있는 시연 명령과 기대 결과.

## 검증

- `python3 -W error::ResourceWarning -m unittest discover -q`: 기존 전체 70개 테스트 통과.
- 질문 번호 16개 전체 대응과 문서 링크 56개의 파일 존재 확인.
- 문서 부록의 CLI 호출 22회를 새 프로세스로 실행: 정상 동작, 예상 오류 3개의 종료 코드 2, 스택트레이스 미출력, 오류 전후 원본 동일, 최종 파일 3개·예산 보존 확인.
- `git diff --check` 통과.
- `loom validate --strict`: 1 Job, 12 Task 메타데이터 정상.

## 범위와 남은 사항

애플리케이션과 기존 테스트 코드는 변경하지 않았다. 10만 건 벤치마크·정적 타입 검사·새 저장소 구현은 수행하지 않았으며 문서에서도 향후 개선 또는 미검증 범위로 명시했다. 요청 범위의 미완료 항목은 없다.
