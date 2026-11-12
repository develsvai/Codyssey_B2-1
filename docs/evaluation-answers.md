# 평가 항목별 구현 설명과 답변

작성·확인일: 2026-11-12. 현재 `budget_app` 구현을 기준으로 정리했다.
각 질문의 **답변 예시**는 발표할 때 사용할 수 있는 짧은 설명이고, 이어지는 내용은 코드 근거와 확인 방법이다.
아래 개선안은 별도로 표시했으며 현재 구현된 기능으로 설명하지 않는다.

## 항목 1. 기능 동작과 데이터 보존

### 1-1. add/list/search/summary/export/import/update/delete가 요구사항대로 동작하는가?

**답변 예시:** “8개 명령을 구현했고, 실제 Python 프로세스를 실행하는 테스트로 연결 동작까지 확인했습니다. 입력은 CLI, 업무 규칙은 기능별 서비스, 파일 처리는 저장소가 담당합니다.”

| 명령 | 실제 동작과 주의할 규칙 | 코드 근거 |
| --- | --- | --- |
| `add` | 날짜·타입·카테고리·금액·메모·태그를 대화형 입력한다. 잘못된 필드는 재입력하고, 정상 완료 시 새 ID와 함께 저장한다. 입력 취소 시 거래를 저장하지 않는다. | `cli/commands/transactions.py::add`, `TransactionService.add` |
| `list` | 기본 20건, `--limit`으로 변경한다. 날짜 내림차순이며 같은 날짜는 ID 내림차순이다. 같은 날짜의 입력 시각 순서는 보장하지 않는다. | `TransactionService.list_recent` |
| `search` | 날짜·카테고리·타입·메모 키워드·태그를 AND로 결합한다. 날짜 양끝 포함, 메모는 대소문자 무시, 태그는 정확히 일치한다. | `TransactionService.search`, `TransactionFilter.matches` |
| `summary` | 지정 월의 총수입·총지출·잔액, 카테고리별 지출 TOP N과 설정된 예산의 사용률·초과 경고를 출력한다. | `ReportService.monthly`, `MonthlySummary` |
| `export` | 월 또는 완전한 시작일·종료일 쌍이 필요하다. 둘 다 주면 교집합을 내보내며, 결과가 없으면 헤더만 있는 CSV를 만든다. | `TransferService.export_csv` |
| `import` | CSV 전체가 유효해야 반영한다. 새 ID를 부여하고 기존 거래와 정렬 병합한다. 같은 CSV를 다시 가져오면 거래가 추가된다. | `TransferService.import_csv` |
| `update` | `--id`와 수정 옵션을 받아 지정한 필드만 바꾼다. ID는 유지하고, 날짜가 바뀌면 정렬 위치도 바꾼다. `--memo ""`, `--tags ""`는 값 지우기다. | `TransactionService.update` |
| `delete` | 지정 ID의 거래를 제외한 새 파일을 만든다. 없는 ID는 오류이며 원본을 유지한다. | `TransactionService.delete`, `TransactionRepository.delete` |

코드 경로는 `budget_app/` 기준이다. 상세 구현은 [거래 서비스](../budget_app/services/transactions.py),
[요약 서비스](../budget_app/services/reports.py), [CSV 서비스](../budget_app/services/transfer.py)에 있다.
확인 근거는 [CLI 테스트](../tests/test_cli.py)의 `test_add_list_search_update_delete`, `test_csv_commands`,
`test_export_combined_conditions`와 [통합 테스트](../tests/test_acceptance.py)의 `test_mission_scenario_across_processes_and_new_data_directory`다.

### 1-2. 재실행 후에도 거래·카테고리·예산이 유지되는가? 저장 파일은 3개 이상인가?

**답변 예시:** “세 종류의 데이터를 각각 UTF-8 JSONL 파일에 저장합니다. 새 프로세스에서도 같은 저장 폴더를 읽기 때문에 데이터가 유지됩니다. 시작할 때는 없는 파일만 만들고 기존 파일은 초기화하지 않습니다.”

| 파일 | 저장 내용 | 한 행의 예 |
| --- | --- | --- |
| `transactions.jsonl` | 거래 | `{"id":"TX-1","type":"expense","date":"2024-01-15","amount":15000,"category":"food","memo":"점심","tags":["meal"]}` |
| `categories.jsonl` | 등록 카테고리 | `{"name":"food"}` |
| `budgets.jsonl` | 월별 예산 | `{"month":"2024-01","amount":500000}` |

기본 위치는 **실행 디렉터리 기준 `./data`**다. 다른 위치에서 실행하면 다른 `./data`를 볼 수 있으므로,
시연에서는 항상 같은 `--data-dir` 절대 경로를 사용한다.
[DataDirectory.initialize](../budget_app/infrastructure/data_directory.py)는 없는 파일만 생성한다.
기존 카테고리 파일이 비어 있어도 기본 카테고리를 다시 넣지 않는다.

확인: [저장소 테스트](../tests/test_repositories.py)의 `test_initialization_and_empty_categories_are_preserved`,
`test_sorted_insert_update_delete_and_persistence`, `test_category_and_budget_persistence`와 실제 프로세스 통합 테스트.
부록의 각 명령도 매번 별도 프로세스로 실행되므로 저장과 재실행을 함께 확인할 수 있다.

### 1-3. category add/list/remove와 사용 중인 카테고리 삭제는 어떻게 처리하는가?

**답변 예시:** “등록·조회·삭제를 지원하며, 거래에서 사용하는 카테고리의 삭제는 막습니다. 거래가 존재하지 않는 카테고리를 참조하게 되는 것을 방지하기 위한 정책입니다.”

[CategoryService](../budget_app/services/categories.py)는 이름을 검증하고, 중복 등록·없는 이름 삭제를 오류로 처리한다.
`remove()`는 쓰기 잠금을 잡고 거래를 한 건씩 확인한다. 사용 중이면 `ConflictError`와 함께
‘해당 거래의 카테고리를 수정하거나 거래를 삭제한 뒤 재시도’하라는 힌트를 준다.
검사와 저장을 같은 잠금 안에서 수행해 그 사이 다른 쓰기가 끼어드는 것을 막는다.
사용하지 않는 카테고리는 목록에서 제외한 후 저장한다. 이름은 대소문자를 구분한다.

확인: [카테고리 테스트](../tests/test_categories.py)의 `test_add_list_remove`, `test_used_category_cannot_be_removed`와
[CLI 테스트](../tests/test_cli.py)의 `test_category_interactive_and_used_removal`.

### 1-4. budget set이 저장되고 summary에 사용률·초과 여부가 출력되는가?

**답변 예시:** “월별 예산을 저장하며, 같은 월을 다시 설정하면 금액을 갱신합니다. 사용률은 월 지출을 예산으로 나눈 백분율이고, 지출이 예산보다 클 때만 초과 경고를 출력합니다.”

[BudgetService.set](../budget_app/services/budgets.py)이 월 형식과 양수 정수 금액을 검증하고
[BudgetRepository.set](../budget_app/infrastructure/repositories/budgets.py)이 월을 키로 저장한다.
[ReportService.monthly](../budget_app/services/reports.py)는 해당 월 거래를 집계하고 예산을 읽어 결과를 반환한다.
[MonthlySummary](../budget_app/domain/reports.py)가 `Decimal`로 사용률을 계산하며,
[show_summary](../budget_app/cli/presenters.py)가 소수 첫째 자리까지 표시한다.

- 예산 500,000원, 지출 215,000원: `사용률 43.0%`, 초과 경고 없음.
- 예산 500,000원, 지출 500,000원: `100.0%`, 초과 경고 없음.
- 예산 500,000원, 지출 500,001원: 초과 경고 있음. 판정은 반올림한 표시값이 아니라 실제 금액 비교다.
- 예산 미설정: 사용률은 `None`이고 summary의 예산 줄을 생략한다. `budget show`는 미설정을 안내한다.

확인: [예산 테스트](../tests/test_budgets.py), [요약 테스트](../tests/test_reports.py)의 `test_exact_budget_and_excess`,
[CLI 테스트](../tests/test_cli.py)의 `test_budget_summary_warning_and_empty_month`.

### 1-5. import/export가 UTF-8·헤더·컬럼을 포함한 CSV 스키마를 따르는가?

**답변 예시:** “CSV는 외부 교환용입니다. 내보내기는 UTF-8과 고정된 6개 헤더를 사용하고, 가져오기는 필수 4개 열과 선택 2개 열을 검증합니다. 쉼표와 줄바꿈이 포함된 값은 표준 `csv` 모듈로 처리합니다.”

```csv
date,type,category,amount,memo,tags
2024-01-15,expense,food,15000,"점심, 친구와 함께","meal,친구"
```

| 열 | 입력 규칙 |
| --- | --- |
| `date` | 필수. 실제 존재하는 `YYYY-MM-DD` 날짜 |
| `type` | 필수. `income` 또는 `expense` |
| `category` | 필수. 이미 등록된 카테고리 |
| `amount` | 필수. 양수 정수 |
| `memo` | 선택. 생략하면 빈 문자열 |
| `tags` | 선택. 쉼표로 구분한 태그. 생략하면 태그 없음 |

[csv_io.py](../budget_app/infrastructure/csv_io.py)의 `CSV_FIELDS`가 출력 순서를 정한다.
입력은 열 순서를 바꿀 수 있지만 필수 열 누락·중복 헤더·알 수 없는 열·열 수 불일치는 오류다.
읽기는 `utf-8-sig`로 UTF-8 BOM도 허용하고, 쓰기는 `utf-8`을 사용한다.
ID는 CSV에 포함하지 않으므로 가져올 때 새로 생성한다. 내부 저장 파일을 CSV로 덮어쓰는 경로도 차단한다.

확인: [CSV 테스트](../tests/test_transfer.py)의 `test_roundtrip_quotes_newlines_unicode_and_tags`,
`test_invalid_headers_columns_and_csv_syntax`, `test_bom_and_header_only`, `test_missing_or_non_utf8_input`.

### 1-6. 잘못된 입력·파일 오류에서 스택트레이스 없이 오류와 해결 힌트를 출력하는가?

**답변 예시:** “업무·입력·저장 오류에는 메시지와 힌트를 담고, 최상위 CLI의 오류 처리 데코레이터가 이를 사용자 안내로 바꿉니다. 하위 계층에서는 직접 출력하지 않습니다.”

[common/errors.py](../budget_app/common/errors.py)의 `AppError` 계열이 오류 정보를 전달한다.
[CommandParser.error](../budget_app/cli/parser.py)도 인수 오류를 `ValidationError`로 바꾸며,
진입점 `main()`의 [@handle_errors](../budget_app/cli/error_handler.py)가 이를 잡아 stderr에 출력한다.
일반 입출력 오류와 예기치 않은 예외에도 안내를 출력하고 비정상 종료한다.

```text
[오류] 없는 거래 ID: missing
[힌트] list 또는 search로 거래 ID를 확인하세요.
```

`add`의 대화형 입력은 [prompts.py](../budget_app/cli/prompts.py)에서 잘못된 필드를 다시 묻는다.
사용자가 수정해 완료한 경우에는 정상 종료한다. 즉, 오류 안내를 한 번 출력했다고 최종 종료가 반드시 실패인 것은 아니다.
파일 오류의 경우 경로·권한·인코딩 또는 손상된 행을 확인하도록 안내한다.

확인: [CLI 테스트](../tests/test_cli.py)의 `test_invalid_arguments_errors_and_no_traceback`,
`test_corrupt_file_and_bad_directory`, `test_interactive_reprompt`.

### 1-7. 오류 시 종료 코드가 0이 아닌지 어떻게 확인하는가?

**답변 예시:** “오류 처리 함수가 정수 종료 코드를 반환하고, 진입점에서 `SystemExit(main())`으로 프로세스에 전달합니다. 터미널에서는 명령 직후 `$?`, 테스트에서는 `CompletedProcess.returncode`로 확인합니다.”

| 코드 | 의미 |
| --- | --- |
| `0` | 정상 처리, help, 빈 조회 결과 |
| `2` | `AppError` 계열: 입력·업무 오류와 `StorageError`로 변환된 파일 오류 |
| `1` | 변환되지 않은 일반 입출력 오류 또는 예기치 않은 예외 |
| `130` | EOF 또는 Ctrl+C로 입력 취소 |

프로젝트 루트에서 실행한다. 이 예시는 인수 검증에서 끝나므로 저장 파일을 만들지 않는다.

```bash
python3 -m budget_app list --limit 0
echo $?
```

예상 종료 코드는 `2`다. `$?`는 직전 명령의 결과이므로 다른 명령을 실행하기 전에 확인해야 한다.
[CLI 테스트](../tests/test_cli.py)는 오류 종료 코드, `[오류]`, `[힌트]`, `Traceback` 미출력을 함께 검사한다.
빈 검색 결과와 예산 초과 경고는 명령 실패가 아니므로 정상 종료한다.

## 항목 2. 모듈·클래스 책임과 안전한 변경

### 2-1. 모듈의 책임을 어떻게 나눴는가?

**답변 예시:** “먼저 거래·카테고리·예산·요약·CSV라는 기능으로 나누고, 각 기능에서 사용자 입출력·업무 규칙·파일 처리를 분리했습니다. 변경 이유가 다른 코드를 분리하고, 반복되는 입출력 처리는 공통 계층에 모았습니다.”

```text
__main__ : 저장소·서비스 객체 생성과 연결
    ↓
cli : 인수 해석·대화형 입력·결과 표시·종료 코드
    ↓
services : transactions / categories / budgets / reports / transfer
    ↓
infrastructure : 저장소 + JSONL·CSV·원자적 교체·잠금·외부 정렬
    ↓
domain : Transaction·Budget·검색 조건·순수 검증·요약 결과
    ↓
common : 공통 오류 타입·시간 측정
```

상위가 필요한 더 아래 계층을 직접 참조하는 것은 허용한다. 예를 들어 서비스는 모델과 검증도 사용한다.
다만 CLI 명령이 저장소를 직접 호출하지 않으며, 기능 서비스끼리도 서로 호출하지 않는다.
요약처럼 여러 데이터가 필요한 기능은 자기 서비스에서 거래·예산 저장소를 조합한다.

공통 관심사도 책임에 맞는 계층에 둔다. 화면 오류 안내는 CLI 공통 모듈, JSONL/CSV 파일 처리는 infrastructure,
화면과 무관한 오류 타입·시간 측정은 common이다. 예산 계산이나 ‘사용 중 카테고리 삭제 금지’ 같은 업무 규칙은 서비스·도메인에 둔다.
따라서 출력 문구 변경은 CLI, 저장 포맷 변경은 infrastructure를 중심으로 수정할 수 있다.

근거: [구조 문서](architecture.md), [객체 조립 진입점](../budget_app/__main__.py).
검증: [test_architecture.py](../tests/test_architecture.py)가 import를 AST로 분석해 상향 의존·순환·서비스 간 참조,
CLI의 저장소 직접 참조 및 하위 계층의 콘솔 입출력을 검사한다.

### 2-2. 최소 2개 이상의 클래스에 부여한 책임 경계를 어떻게 정했는가?

**답변 예시:** “데이터 자체가 항상 지켜야 하는 조건, 작업 순서와 업무 규칙, 실제 저장 방법을 서로 다른 책임으로 봤습니다. 예를 들어 Transaction은 유효한 거래 한 건, TransactionService는 거래 변경 절차, TransactionRepository는 파일 저장을 책임집니다.”

| 클래스 | 책임 | 다른 클래스에 맡긴 일 |
| --- | --- | --- |
| `Transaction` | 거래 필드와 날짜·타입·금액 등의 불변식. `frozen=True`로 생성 후 임의 변경 방지 | 카테고리 등록 여부 조회, 저장, 화면 표시 |
| `Budget` | 월과 양수 정수 예산의 유효성 | 월별 저장·갱신, 실제 지출 집계 |
| `TransactionService` | 입력 정규화, 등록 카테고리 확인, 쓰기 잠금 안에서 수정 절차 조정 | JSONL 직렬화, 화면 출력 |
| `TransactionRepository` | 거래 읽기, 정렬 유지, ID 조회, 삽입·교체·삭제 결과 생성 | 사용자에게 질문하기, 카테고리 사용 정책 결정 |
| `DataDirectory` | 저장 경로, 최초 파일 생성, 여러 저장소가 공유하는 쓰기 잠금 | 거래 금액·예산 사용률 계산 |

핵심 경계는 `Transaction`이 카테고리 **이름 형식**만 검증하고, `TransactionService`가 저장소를 통해
그 이름이 **실제로 등록되어 있는지** 확인한다는 점이다. 모델이 파일 저장 방식에 의존하지 않도록 나눴다.
수정에는 `dataclasses.replace()`로 검증된 새 객체를 만들고 ID는 유지한다.

근거: [모델](../budget_app/domain/models.py), [거래 서비스](../budget_app/services/transactions.py),
[거래 저장소](../budget_app/infrastructure/repositories/transactions.py).
확인: [모델 테스트](../tests/test_domain.py)의 불변성과 잘못된 필드 테스트, [거래 테스트](../tests/test_transactions.py)의 수정·검증 테스트.

### 2-3. 파일 기반 update/delete를 어떻게 안전하게 처리했는가?

**답변 예시:** “원본을 바로 고치지 않고 변경 결과 전체를 같은 폴더의 임시 파일에 씁니다. 모든 읽기·검증·쓰기가 끝난 뒤 flush와 fsync를 수행하고 os.replace로 교체합니다. 중간에 실패하면 교체 전 원본을 유지합니다.”

1. 서비스가 데이터 폴더의 `.write.lock`을 독점 생성해 다른 쓰기를 막는다.
2. update는 기존 ID를 찾고 변경 값을 검증한다. 저장소는 기존 거래를 읽으며 해당 ID를 빼고 새 거래를 정렬 위치에 넣는다.
3. delete는 해당 ID만 제외하고 나머지를 내보낸다. 끝까지 ID를 못 찾으면 오류를 발생시킨다.
4. `write_jsonl()`이 이 결과를 원본과 같은 폴더의 임시 파일에 기록한다.
5. 모두 성공하면 `flush()` → `os.fsync()` → 파일 닫기 → `os.replace()` 순으로 반영한다.
6. 일반적인 예외 발생 시 `finally`에서 임시 파일과 잠금을 정리한다. 검증 실패나 교체 실패 시 원본은 유지된다.

같은 폴더를 쓰는 이유는 같은 파일 시스템 안에서 교체하도록 하기 위해서다.
원자적 교체는 독자가 **덜 써진 중간 파일**을 보지 않게 하는 장치이며, 잠금은 **동시 쓰기의 덮어쓰기 손실**을 막는 장치다.
두 장치의 역할은 다르다.

근거: [TransactionRepository](../budget_app/infrastructure/repositories/transactions.py),
[atomic_text_writer](../budget_app/infrastructure/atomic_file.py), [write_lock](../budget_app/infrastructure/data_directory.py).
확인: [저장소 테스트](../tests/test_repositories.py)의 `test_failed_replace_preserves_original_and_cleans_temp`,
`test_generator_error_rolls_back`, `test_missing_ids_and_duplicate_leave_original`와 별도 프로세스의 잠금 충돌 테스트.

**보장 범위:** 파일 하나의 교체 단위다. 세 파일 전체를 묶는 DB 트랜잭션이나 읽기 시점의 일관된 스냅샷은 아니다.
강제 종료 시 잠금·임시 파일이 남을 수 있고, 디렉터리 자체의 fsync는 구현하지 않아 정전까지 포함한 내구성을 보장한다고 설명하지 않는다.

## 항목 3. 제너레이터·데코레이터·타입 힌트

### 3-1. list/search를 제너레이터로 어떻게 구현했고 왜 유리한가?

**답변 예시:** “JSONL을 한 줄씩 읽어 거래 객체로 만들고, 검색 조건에 맞는 객체만 yield합니다. CLI도 받은 객체를 바로 출력하므로 전체 거래나 결과 목록을 메모리에 모으지 않습니다. list는 필요한 개수만 읽고 멈춥니다.”

처리 흐름은 `read_jsonl()` → `TransactionRepository.iter_all()` → `list_recent()/search()` → `show_transactions()`다.
각 단계가 다음 한 건을 요청할 때만 읽는 지연 실행 구조다. 실제 검색 구현의 핵심은 다음과 같다.

```python
def records() -> Iterator[Transaction]:
    with closing(self.transactions.iter_all()) as transactions:
        for transaction in transactions:
            if query.matches(transaction):
                yield transaction
```

출처: [TransactionService.search](../budget_app/services/transactions.py)의 내부 함수 발췌.
`list_recent()`는 `yield from islice(transactions, limit)`을 사용한다.
저장 파일을 날짜·ID 내림차순으로 유지하므로 조회할 때 전체를 다시 정렬하지 않는다.
`closing()`은 중간에 소비를 끝내거나 오류가 나도 제너레이터와 그 안의 파일을 닫도록 한다.

장점은 거래 수만큼 객체를 쌓지 않아 메모리 사용을 줄이고, 첫 결과부터 출력할 수 있다는 것이다.
한 건의 크기가 일정하다고 보면 거래 스트림 자체의 추가 메모리는 거의 일정하다. 단, 카테고리 조회에는 카테고리 수만큼 메모리가 들고 큰 메모 한 건도 메모리를 차지한다.
검색은 여전히 최악에 전체 N건을 읽는 O(N)이다. 제너레이터가 검색 인덱스를 만들어 주는 것은 아니다.
조회 도중 뒤쪽 파일 손상이 발견되면 앞선 출력이 이미 나왔을 수 있지만, 최종 명령은 오류로 끝난다.

확인: [거래 테스트](../tests/test_transactions.py)의 `test_lazy_limit_does_not_read_remainder`는 limit 1일 때 다음 거래를 읽지 않는지 검사한다.
[통합 테스트](../tests/test_acceptance.py)의 `test_large_search_streams_without_materializing_transactions`는 12,000건을 소비하며
`tracemalloc`으로 추적한 검색 중 최대 Python 메모리가 1,000,000 bytes 미만인지 확인한다.
이는 해당 테스트의 측정값이며 프로세스 전체 메모리나 10만 건 성능 보장은 아니다.

### 3-2. 데코레이터로 분리한 공통 기능은 무엇이며 왜 분리했는가?

**답변 예시:** “여러 기능에 반복되는 실행 시간 측정은 @timed로, 최상위 오류 안내와 종료 코드 변환은 @handle_errors로 분리했습니다. 각 기능이 자기 업무 로직에 집중하면서 같은 로그·오류 정책을 적용하도록 하기 위해서입니다.”

| 데코레이터 | 적용 위치와 동작 | 분리 이유 |
| --- | --- | --- |
| `@timed` | 거래 변경·카테고리 변경·예산 설정·요약·CSV 서비스 메서드. `perf_counter()`로 측정하고 `finally`에서 DEBUG 로그 기록 | 성공·실패 모두 같은 방식으로 측정하고 측정 코드 중복 제거 |
| `@handle_errors` | `__main__.main`. 예외를 메시지·힌트·종료 코드로 변환 | 사용자 안내를 CLI 한 곳에서 일관되게 처리하고 하위 계층을 화면에 의존시키지 않음 |

[timed](../budget_app/common/decorators.py)는 `functools.wraps`로 원래 함수 이름·문서 등 메타데이터를 유지한다.
로그 설정은 CLI 진입점에서 하므로 `--verbose`일 때 함수명과 시간 로그를 볼 수 있다. 인수나 거래 메모를 기록하지 않는다.
`list_recent/search`에는 `@timed`를 붙이지 않았다. 제너레이터를 반환하는 시간만 재면 실제 소비·검색 시간을 측정했다고 볼 수 없기 때문이다.

확인: [모델·공통 기능 테스트](../tests/test_domain.py)의 `test_timed_preserves_result_metadata_and_errors`가 반환값·이름·예외 전달과
성공/실패 로그를 검사한다. [CLI 테스트](../tests/test_cli.py)는 verbose 로그와 오류 안내를 별도로 확인한다.

### 3-3. 타입 힌트의 이점을 실제 코드 예로 어떻게 확인했고 왜 도움이 되는가?

**답변 예시:** “함수의 입력과 결과, 값이 없을 수 있는 경우를 코드에 명시했습니다. 덕분에 호출자가 반환값을 리스트로 생각하거나 None 검사를 빠뜨리는 실수를 줄일 수 있습니다. 실제 값 검증은 타입 힌트와 별도로 수행합니다.”

| 실제 선언 | 읽어낼 수 있는 계약과 이점 |
| --- | --- |
| `list_recent(self, limit: int = 20) -> Iterator[Transaction]` | 거래를 순차 소비한다. `len(result)`나 `result[0]`을 지원하는 리스트라고 가정하지 않는다. |
| `BudgetService.get(self, month: str) -> Budget | None` | 예산 미설정 가능성이 있다. `.amount` 접근 전에 None 처리가 필요함을 드러낸다. |
| `Transaction.amount: int`, `tags: tuple[str, ...]` | 금액의 단위가 정수이고 태그는 문자열 튜플임을 알 수 있다. dict 키 추측보다 모델 필드 확인이 쉽다. |
| `timed(function: Callable[P, R]) -> Callable[P, R]` | `ParamSpec`과 `TypeVar`로 감싼 함수의 인수·반환 타입 관계를 유지한다. |

예를 들어 [show_budget](../budget_app/cli/presenters.py)는 `Budget | None`에 맞춰 None을 먼저 처리한 뒤 금액을 출력한다.
[모델](../budget_app/domain/models.py)은 `amount: int`라는 선언에 더해 `__post_init__()`에서 실제 정수인지 검사하고,
[서비스](../budget_app/services/budgets.py)는 CLI에서 받은 문자열 금액을 `positive_int()`로 변환한다.
이렇게 입력 경계의 `int | str`과 검증 완료된 모델의 `int`를 구분했다.

확인: [test_domain.py](../tests/test_domain.py)는 문자열·bool 금액 등을 넣었을 때 런타임 검증이 거부하는지 확인한다.
타입 힌트 자체는 Python 실행 중 타입을 강제하지 않는다. IDE나 별도 정적 검사기를 연결하면 호출 실수를 일찍 찾는 데 도움이 되지만,
현재 저장소에서 mypy/pyright 전체 검사를 통과했다고 주장하지 않는다. 기존 AST 구조 검사도 정적 타입 검사와는 다르다.

## 항목 4. 저장 포맷과 확장·실패 정책

### 4-1. JSONL과 CSV의 장단점은 무엇이고 왜 JSONL을 저장 포맷으로 택했는가?

**답변 예시:** “내부 저장에는 JSONL, 외부 교환에는 CSV를 사용했습니다. JSONL은 한 줄씩 읽으면서 정수와 태그 배열을 자연스럽게 표현할 수 있고, CSV는 스프레드시트 등 다른 도구와 교환하기 편하기 때문입니다.”

| 비교 | JSONL | CSV |
| --- | --- | --- |
| 구조 | 행마다 필드 이름이 있는 JSON 객체 | 헤더와 열 위치를 공유하는 표 |
| 타입·태그 | 숫자와 배열 표현 가능. `tags`를 배열로 저장 | 읽은 값은 문자열이며 숫자 변환 필요. 태그의 별도 표현 규칙 필요 |
| 순차 처리 | 한 물리적 줄을 한 레코드로 파싱 | `csv` 파서로 순차 처리 가능. 인용된 줄바꿈 때문에 단순 줄 분할은 부적절 |
| 크기 | 매 행 키를 반복해 용량이 커질 수 있음 | 반복 키가 없어 같은 표 데이터는 더 간결할 수 있음 |
| 사람·외부 도구 | 객체 구조를 확인하기 좋음 | 스프레드시트와 표 형태 교환에 편리 |
| 수정·검색 | 인덱스가 없으면 순차 검색, 현재 구조는 변경 시 재작성 | 파일만으로 쓰면 수정·검색 문제는 비슷함 |

이 프로젝트에서는 태그가 여러 개이고 금액을 정수로 다루므로 내부 표현에 JSONL이 잘 맞는다.
`json.dumps(..., ensure_ascii=False)`로 한글을 보존하며 메모 안 줄바꿈은 이스케이프되어 레코드 경계가 유지된다.
CSV에도 스트리밍은 가능하므로 “스트리밍하려면 JSONL만 가능하다”는 설명은 하지 않는다.
JSONL도 스키마를 자동 보장하지 않기 때문에 읽을 때 모델로 복원해 다시 검증한다.

근거: [jsonl_io.py](../budget_app/infrastructure/jsonl_io.py), [csv_io.py](../budget_app/infrastructure/csv_io.py),
[decode_transaction](../budget_app/infrastructure/repositories/transactions.py).
확인: 손상 JSONL 보존 테스트와 한글·태그·쉼표·줄바꿈의 CSV 왕복 테스트.

### 4-2. 거래가 10만 건이면 병목은 어디이며 어떻게 개선할 것인가?

**답변 예시:** “제너레이터 덕분에 전체 거래를 메모리에 쌓지는 않지만, 검색·요약은 전체 파일을 읽고 수정·삭제는 전체 파일을 다시 씁니다. 따라서 먼저 처리 시간과 읽기·쓰기 양을 측정한 뒤, 파일을 유지한다면 월별 분할과 배치 쓰기를, 제약이 완화되면 인덱스가 있는 저장소로의 교체를 검토하겠습니다.”

N은 전체 거래 수, K는 요청 건수, C는 집계 대상 카테고리 수다. 아래는 코드 구조에 따른 분석이며 10만 건 실측 결과가 아니다.

| 현재 기능 | 예상 비용과 병목 | 향후 개선안 — 현재 미구현 |
| --- | --- | --- |
| `list --limit K` | 정렬된 앞부분만 읽어 O(min(N, K)). 많은 결과는 터미널 출력도 비용 | 페이지 단위 조회·출력 제한 |
| `search`, `export` | 현재 날짜 조건이 있어도 전체 순회 O(N), JSON 파싱·모델 검증·출력 비용 | 날짜 정렬을 활용한 범위 밖 건너뛰기/조기 종료, 월별 파일 분할, 조건 인덱스 |
| `summary` | O(N) 읽기 + O(C log C) 순위 정렬, 합계 보관 O(C) | 월별 파일만 조회, 수정·삭제까지 일관되게 갱신하는 집계 캐시 |
| `add/update/delete` | 정렬 유지와 원자적 교체 때문에 O(N) 재작성. update는 ID 조회도 반복 | 단건 반복 쓰기 대신 배치 반영, 월별 분할, ID 인덱스가 있는 저장소 |
| 카테고리 삭제 | 참조 거래 탐색 최악 O(N) | 참조 수 또는 카테고리 인덱스. 거래 변경과 함께 갱신 필요 |
| `import` | 기존 ID 배치 충돌 확인 + 외부 정렬 + 전체 병합·쓰기, 임시 디스크 공간·잠금 시간 | 측정에 맞춘 청크 크기 조정, 검증 단계와 잠금 범위 검토, 저장소 변경 |

현재 import는 이미 1,024건 단위로 정렬하고 한 번에 최대 32개 청크를 병합한다.
전체 거래 객체를 모으지는 않지만, 청크 경로 목록과 임시 디스크 공간은 입력 크기에 따라 늘어난다.
또한 쓰기 잠금은 입력 검증·정렬을 포함한 전체 import 동안 유지된다.

개선은 다음 순서로 검토한다.

1. 별도 임시 데이터로 10만 건을 만들고 조회·검색·요약·수정·import의 시간, 메모리, 파일 크기, 잠금 유지 시간을 측정한다. 긴 메모와 검색 결과가 많은 경우도 포함한다.
2. JSONL 과제 조건을 유지하면 날짜 범위 활용, 월별 분할, 여러 변경을 한 번에 반영하는 배치를 우선 검토한다. 여러 파일을 바꾸는 작업에는 새로운 일관성 설계가 필요하다.
3. 파일 3개·포맷 제약을 변경할 수 있다면 표준 라이브러리 `sqlite3`와 날짜/ID/카테고리 인덱스, 트랜잭션을 검토한다. 변경 전 데이터 이관과 조회 결과 동등성을 검증한다.

하위 저장소를 분리했으므로 CLI 동작과 업무 규칙을 유지하면서 저장 구현 교체 범위를 줄일 수 있다.
다만 현재 서비스는 구체 저장소 타입과 `DataDirectory.write_lock()`을 사용하므로 완전한 무수정 교체는 아니다.
교체 시 저장소 인터페이스와 트랜잭션 경계를 먼저 정의해야 한다.
현재 성능 근거는 12,000건 검색 메모리 검사와 2,300건 다단계 외부 병합 검사이며, 10만 건 벤치마크는 미실시다.

### 4-3. import CSV에 깨진 행이 섞이면 어떻게 사용자 신뢰를 지키는가?

**답변 예시:** “현재는 부분 성공 없이 전체 성공 또는 전체 취소 정책입니다. 잘못된 행 하나라도 발견하면 기존 거래 파일을 교체하지 않습니다. 오류 위치와 해결 힌트를 보고 입력을 수정한 뒤 다시 시도할 수 있어 반영 범위가 분명합니다.”

[TransferService.import_csv](../budget_app/services/transfer.py)는 CSV 형식과 업무 값을 순서대로 검증한다.
[insert_many](../budget_app/infrastructure/repositories/transactions.py)는 유효한 입력을 디스크에서 정렬한 뒤 기존 거래와 병합하고,
완성된 결과에만 원자적 파일 교체를 적용한다. 앞선 정상 행을 원본에 먼저 저장하는 방식이 아니다.
따라서 뒤쪽 행에서 오류가 나도 앞선 행을 별도로 지우는 보상 작업 없이 전체 반영을 취소할 수 있다.

- 날짜·금액·카테고리 등 값 오류와 열 수 오류: CSV 행 번호와 원인·힌트를 안내한다. 여러 줄 필드가 있으면 파서가 보고한 물리적 끝 행 번호다.
- 헤더 오류: 필요한 헤더 구성을 안내한다. CSV 문법·인코딩·파일 오류는 파일과 원인을 안내하며 모든 종류의 오류가 행 번호를 포함하는 것은 아니다.
- 실패: 첫 오류에서 중단한다. 전체 오류 목록 파일이나 부분 성공 리포트는 현재 구현하지 않았다.
- 성공: `imported=N, skipped=0`을 출력한다. 새 거래 ID가 부여되며 카테고리는 자동 생성하지 않는다.
- 성공했던 같은 CSV를 다시 실행하면 중복 내용이 새 거래로 추가된다. 실패 후 재시도와 성공 후 재실행을 구분해야 한다.

확인: [CSV 테스트](../tests/test_transfer.py)의 `test_bad_late_row_rolls_back_all_imported_rows`는
앞 행은 정상이고 뒤 행은 잘못된 CSV에서 원본 바이트가 그대로인지, 정렬 임시 폴더가 정리되는지 검사한다.
`test_unknown_category_is_not_automatically_added`와 잘못된 헤더·문법·인코딩 테스트도 포함한다.

향후 개선안은 `--dry-run`과 행별 검증 리포트다. 부분 성공 모드를 추가한다면 성공/실패 건수뿐 아니라
반영된 행과 실패 행을 구분하고, 재시도 시 중복 반영을 막는 정책을 먼저 정해야 한다. 현재 기본 정책은 전체 취소다.

## 부록 A. 검증 상태와 답변 범위

2026-11-12에 다음 명령을 실행해 전체 **70개 테스트 통과**를 확인했다.

```bash
python3 -W error::ResourceWarning -m unittest discover -q
```

2026-11-10의 Python 3.11·3.14 교차 검증과 추가 시나리오는 [검증 기록](validation.md),
미션 원문 대조는 [요구사항 점검표](mission-checklist.md)를 참고한다.
이번 문서는 애플리케이션 동작을 변경하지 않았다. Python 3.10 런타임, 정적 타입 검사기, 10만 건 성능 시험을 수행한 것으로 설명하지 않는다.

## 부록 B. 실제 명령으로 시연하기

프로젝트 루트의 bash/zsh에서 아래 순서로 실행한다. `mktemp`로 별도 폴더를 만들어 기존 사용자 데이터를 건드리지 않는다.
각 `budget_demo` 호출은 새 Python 프로세스를 실행한다. 일부 명령은 의도적으로 실패하므로 `set -e` 없이 실행한다.

```bash
DEMO_ROOT=$(mktemp -d)
budget_demo() { python3 -m budget_app --data-dir "$DEMO_ROOT/data" "$@"; }

# 카테고리 등록·재조회와 예산 저장
budget_demo category add --name 취미
budget_demo category list
budget_demo budget set --month 2024-01 --amount 50000
budget_demo budget show --month 2024-01

# add의 6개 질문에 순서대로 답한다.
budget_demo add <<'INPUT'
2024-01-15
expense
취미
60000
책 구매
book,study
INPUT
budget_demo list --limit 1
budget_demo search --from 2024-01-01 --to 2024-01-31 --category 취미 --q 책 --tag book
budget_demo summary --month 2024-01

# 사용률 120.0%, 초과 경고. 사용 중인 카테고리 삭제는 실패한다.
budget_demo category remove --name 취미
echo "사용 중 카테고리 삭제 종료 코드: $?"

# UTF-8 CSV 헤더·행 확인, 새 데이터 폴더로 가져오기
budget_demo export --out "$DEMO_ROOT/out.csv" --month 2024-01
cat "$DEMO_ROOT/out.csv"
python3 -m budget_app --data-dir "$DEMO_ROOT/copied" category add --name 취미
python3 -m budget_app --data-dir "$DEMO_ROOT/copied" import --from "$DEMO_ROOT/out.csv"
python3 -m budget_app --data-dir "$DEMO_ROOT/copied" list

# 시연 데이터 한 건의 ID를 읽어 수정한다.
TX_ID=$(python3 -c 'import json,sys; print(json.loads(open(sys.argv[1], encoding="utf-8").readline())["id"])' "$DEMO_ROOT/data/transactions.jsonl")
budget_demo update --id "$TX_ID" --amount 40000
budget_demo summary --month 2024-01

# 뒤쪽 행이 잘못된 CSV: 먼저 정상인 행도 반영되지 않아야 한다.
cat > "$DEMO_ROOT/bad.csv" <<'CSV'
date,type,category,amount,memo,tags
2024-01-16,expense,취미,1000,정상 행,
2024-01-17,expense,취미,-1,잘못된 금액,
CSV
cp "$DEMO_ROOT/data/transactions.jsonl" "$DEMO_ROOT/before.jsonl"
budget_demo import --from "$DEMO_ROOT/bad.csv"
echo "잘못된 CSV 종료 코드: $?"
cmp "$DEMO_ROOT/before.jsonl" "$DEMO_ROOT/data/transactions.jsonl"
echo "원본 비교 결과(0이면 동일): $?"

# 없는 입력 파일도 안내와 비0 종료 코드로 처리한다.
budget_demo import --from "$DEMO_ROOT/missing.csv"
echo "없는 파일 종료 코드: $?"

# 거래 삭제 후 카테고리 삭제는 성공한다. 예산은 그대로 남는다.
budget_demo delete --id "$TX_ID"
budget_demo category remove --name 취미
budget_demo category list
budget_demo list
budget_demo budget show --month 2024-01
ls "$DEMO_ROOT/data"
echo "시연 파일 위치: $DEMO_ROOT"
```

기대 결과: 최초 summary는 지출 60,000원·사용률 120.0%·경고, 수정 후는 40,000원·80.0%·경고 없음이다.
사용 중 카테고리 삭제·잘못된 CSV·없는 파일은 종료 코드 2, 실패 전후 원본 비교는 0이다.
거래 삭제 후 `list`는 `데이터 없음`이고 예산 50,000원과 JSONL 파일 3개는 유지된다.
작성 시 이 절의 CLI 호출 22회를 실제 실행해 예상 오류 3건, 출력값, 파일 보존과 최종 저장 상태를 확인했다.
