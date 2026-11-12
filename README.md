# 나만의 용돈 기입장

Python 콘솔에서 거래, 카테고리, 월 예산을 관리합니다. 미션 B2-1의 필수 기능을 구현하며
외부 패키지나 설치 과정 없이 **Python 3.10 이상 표준 라이브러리**만 사용합니다.

## 시작하기

프로젝트 루트에서 실행합니다. 환경에 따라 `python` 대신 `python3`를 사용하세요.

```bash
python3 -m budget_app --help
python3 -m budget_app category list
python3 -m budget_app add
python3 -m budget_app list --limit 10
```

`add`는 날짜, 타입, 카테고리, 양수 정수 금액, 메모, 태그를 차례대로 묻습니다.
잘못된 필드는 다시 입력할 수 있고, 마지막 입력까지 정상적으로 끝나면 생성된 거래 ID를 출력합니다.
입력 도중 Ctrl+C 또는 EOF로 종료하면 거래는 저장되지 않습니다.

```text
날짜(YYYY-MM-DD): 2024-01-15
타입(income/expense): expense
카테고리: food
금액(양수 정수): 15000
메모(선택): 점심
태그(쉼표로 구분, 없으면 엔터): meal,친구
[저장 완료] id=TX-...
```

모든 명령과 하위 명령에서 `--help`를 사용할 수 있습니다. 옵션은 `--` 표기로 통일합니다.
`--data-dir`와 `--verbose`는 명령 앞이나 뒤에 지정할 수 있습니다.

```bash
python3 -m budget_app --data-dir ./my-data list
python3 -m budget_app budget set --month 2024-01 --amount 500000 --data-dir ./my-data
python3 -m budget_app summary --month 2024-01 --verbose
```

## 주요 명령

| 명령 | 기능 |
| --- | --- |
| `add` | 대화형 거래 추가, 생성 ID 출력 |
| `list --limit 20` | 최신순 거래 조회, 기본 20건 |
| `search` | 조건을 AND로 결합한 최신순 검색 |
| `update --id ID [수정 옵션]` | 지정한 필드만 수정 |
| `delete --id ID` | 거래 삭제 |
| `summary --month YYYY-MM --top 5` | 수입/지출/잔액, 지출 순위, 예산 사용률·초과 경고 |
| `budget set --month YYYY-MM --amount 금액` | 월 예산 설정 또는 갱신 |
| `budget show --month YYYY-MM` | 월 예산 조회 |
| `category add/list/remove` | 카테고리 등록·조회·삭제 |
| `import --from 파일.csv` | CSV 전체 검증 후 일괄 추가 |
| `export --out 파일.csv --month YYYY-MM` | 월별 CSV 내보내기 |

검색 기간은 양끝 날짜를 포함합니다. 메모 검색은 대소문자를 구분하지 않고, 태그는 정확히 일치해야 합니다.

```bash
python3 -m budget_app search --from 2024-01-01 --to 2024-01-31 --category food --type expense --q 점심 --tag meal
python3 -m budget_app summary --month 2024-01 --top 3
```

**update는 옵션 방식으로 고정**했습니다. `TX-...`는 `add` 또는 `list`에서 확인한 실제 ID로 바꾸세요.
`--memo ""`, `--tags ""`로 값을 지울 수 있으며 생략한 필드는 유지됩니다. ID 자체는 변경할 수 없습니다.

```bash
python3 -m budget_app update --id TX-... --amount 20000 --date 2024-01-16 --memo "저녁" --tags "meal,친구"
python3 -m budget_app update --id TX-... --memo "" --tags ""
python3 -m budget_app delete --id TX-...
```

카테고리 추가·삭제는 기본적으로 이름을 묻습니다. `--name`으로도 지정할 수 있습니다.
카테고리 이름은 대소문자를 구분합니다. 거래에서 사용 중인 카테고리는 삭제할 수 없습니다.

```bash
python3 -m budget_app category add
python3 -m budget_app category add --name 취미
python3 -m budget_app category list
python3 -m budget_app category remove --name 취미
```

## 저장 위치와 형식

기본 저장 위치는 **명령을 실행한 디렉터리 기준 `./data`**입니다.
`--data-dir`로 바꿀 수 있으며 폴더와 없는 저장 파일은 자동 생성됩니다.
`--help`만 실행할 때는 저장 파일을 생성하지 않습니다.

| 파일 | JSONL 한 행의 예 |
| --- | --- |
| `transactions.jsonl` | `{"id":"TX-...","type":"expense","date":"2024-01-15","amount":15000,"category":"food","memo":"점심","tags":["meal"]}` |
| `categories.jsonl` | `{"name":"food"}` |
| `budgets.jsonl` | `{"month":"2024-01","amount":500000}` |

- 파일은 UTF-8 JSONL로 저장하며 한 줄이 하나의 레코드입니다. 저장 중에는 `.write.lock`과 임시 파일도 생깁니다.
- 최초 카테고리 파일 생성 시 `food`, `transport`, `rent`, `salary`, `etc`를 등록합니다.
  기존 카테고리 파일이 비어 있으면 기본값을 되살리지 않습니다. `category add`로 먼저 등록하세요.
- 거래는 `(날짜, ID)` 내림차순으로 저장합니다. 같은 날짜에서는 ID 내림차순이며 입력 시각 순서는 아닙니다.
- 목록·검색은 제너레이터로 한 줄씩 읽습니다. 월별 요약은 거래 전체 대신 카테고리 합계만 보관합니다.
- 변경은 같은 폴더의 임시 파일에 쓴 후 flush/fsync와 원자적 교체를 수행합니다.
  쓰기·검증 실패 시 교체되지 않은 원본이 보존됩니다. 저장 파일을 직접 수정하지 마세요.
- 앱의 쓰기 잠금은 카테고리 검증과 저장 사이의 동시 변경을 막습니다. 다른 쓰기가 진행 중이면 재시도 안내를 출력합니다.
  비정상 강제 종료로 잠금이 남았다면 **실행 중인 앱이 없는지 확인한 뒤** `.write.lock`을 제거하세요.
- `data/`는 Git 추적에서 제외합니다. 파일 시스템 장애까지 대비하려면 데이터 폴더를 별도로 보관하세요.

## CSV 가져오기·내보내기

UTF-8, 헤더 포함 CSV를 사용합니다. UTF-8 BOM 입력도 허용합니다.
필수 열은 네 개이며 선택 열은 생략할 수 있습니다. 중복 헤더와 정의되지 않은 열은 오류입니다.

| 열 | 필수 | 값 |
| --- | --- | --- |
| `date` | 예 | 실제 날짜, `YYYY-MM-DD` |
| `type` | 예 | `income` 또는 `expense` |
| `category` | 예 | 등록된 카테고리 |
| `amount` | 예 | 0보다 큰 정수 |
| `memo` | 아니요 | 문자열, 기본 빈 문자열 |
| `tags` | 아니요 | 쉼표로 구분한 태그, 기본 없음 |

```csv
date,type,category,amount,memo,tags
2024-01-15,expense,food,15000,"점심, 친구와 함께","meal,친구"
2024-01-14,income,salary,3000000,월급,
```

```bash
python3 -m budget_app import --from import.csv
python3 -m budget_app export --out january.csv --month 2024-01
python3 -m budget_app export --out period.csv --from 2024-01-01 --to 2024-02-15
python3 -m budget_app export --out intersection.csv --month 2024-01 --from 2024-01-10 --to 2024-02-15
```

- 내보내기는 **월 또는 시작일·종료일 쌍 중 하나 이상**을 받습니다. 둘 다 지정하면 **교집합**을 내보냅니다.
  위 intersection.csv 예시는 2024-01-10부터 2024-01-31까지를 포함합니다.
  두 조건이 겹치지 않으면 정상 종료하며 헤더만 있는 CSV를 만듭니다.
  조건 전체 생략, 시작일/종료일 중 하나만 지정, 잘못된 날짜나 역전된 기간은 오류입니다.
- 내보내는 열 순서는 `date,type,category,amount,memo,tags`입니다. 대상 거래가 없어도 헤더 파일을 만듭니다.
- 기존 출력 CSV는 정상 완료 시 교체합니다. 내부 저장 파일과 그 심볼릭 링크 대상은 출력 경로로 사용할 수 없습니다.
- CSV 인용 규칙은 `csv` 모듈이 처리합니다. 쉼표·큰따옴표·줄바꿈이 들어간 메모도 보존합니다.
- 가져오기는 잘못된 행이 하나라도 있으면 **전체 반영을 취소**하고 원인과 힌트를 출력합니다.
  검증 오류는 행 번호를 포함합니다. 문법/인코딩 오류는 파일과 원인을 안내합니다.
- 가져올 때 ID를 새로 부여합니다. 같은 CSV를 다시 가져오면 별도 거래로 추가되며 기존 ID를 복원하는 백업 기능은 아닙니다.
- 날짜가 뒤섞인 입력은 최대 1,024건씩 디스크 청크로 정렬하고, 한 번에 최대 32개 청크를 병합합니다.
  임시 디스크 공간은 필요하지만 거래 전체를 메모리에 적재하지 않습니다.
- 성공 출력 예: `imported=5, skipped=0`, `january.csv (5 records)`.

## 구조와 공통 관심사

```text
budget_app/
  __main__.py                실행 진입점·객체 조립
  cli/commands/              거래·카테고리·예산·요약·CSV별 명령
  cli/prompts.py             대화형 입력·재입력
  cli/presenters.py          결과 표시
  cli/error_handler.py       오류 안내·종료 코드 데코레이터
  services/                  기능별 업무 규칙과 절차
  infrastructure/repositories/  거래·카테고리·예산 저장소
  infrastructure/            JSONL·CSV·병합 정렬·파일 교체·잠금
  domain/                    불변 모델·검색 조건·순수 검증
  common/                    공통 오류 타입·시간 측정 데코레이터
```

의존성은 `CLI → 서비스 → 입출력 → 모델·검증 → 공통 기반` 방향입니다. 필요한 더 아래 계층은 직접 참조할 수 있습니다.
기능 서비스끼리는 참조하지 않고 각 서비스가 필요한 저장소를 조합합니다.
CLI 명령은 서비스만 호출하며, `__main__`이 저장소와 서비스를 생성·연결합니다.
하위 계층에는 `input()`·`print()`가 없고 파일 읽기·쓰기는 infrastructure에 모았습니다.
예산 계산과 CSV 검증은 서비스에, 파일 포맷 처리는 하위 계층에 두었습니다.

실행 시간 측정은 `@timed`, 화면 오류 처리는 `@handle_errors`로 분리해 실제 적용했습니다.
`--verbose`는 실행 시간을 stderr에 표시하며 거래 메모는 로그에 포함하지 않습니다.
자세한 정책은 [구조 문서](docs/architecture.md)를 참고하세요.

## 오류와 검증

정상 종료는 `0`, 입력/업무/저장소 오류는 `2`, 일반 입출력/예기치 않은 오류는 `1`, 입력 취소는 `130`입니다.
오류 메시지는 stderr에 원인과 해결 힌트를 출력하며 앱 실행 시 스택트레이스를 출력하지 않습니다.
거래가 없는 조회나 미설정 예산 조회는 정상 종료합니다.

```bash
python3 -m unittest discover -v
python3 -m unittest tests.test_architecture -v
```

테스트는 임시 폴더를 사용합니다. CRUD·검색·집계·예산 경계·CSV 왕복·쓰기 실패 보존·실제 CLI·동시 쓰기 방지와
하향 의존성·순환 참조·표준 라이브러리만 사용 여부를 확인합니다.
백업 명령, 반복 거래, 가변 폭 표 정렬은 선택 과제로 구현하지 않았습니다.

Python 3.11과 3.14에서 전체 70개 테스트를 통과했습니다. [검증 기록](docs/validation.md)에 시나리오와 검증 범위를 정리했습니다.
평가 질문에 대한 발표용 답변, 코드 근거와 시연 절차는 [평가 항목별 구현 설명](docs/evaluation-answers.md)을 참고하세요.
