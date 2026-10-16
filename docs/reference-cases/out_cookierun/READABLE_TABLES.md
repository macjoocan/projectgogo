# 쿠키런 크럼블 테이블 변환 결과

원본 버전: com.devsisters.cc 1.0.002 / 작업일: 2026-09-15

## 결과

- 복호화된 patch_binary_set의 185개 항목은 `.bytes` 183개와 기존 CSV 2개입니다. 이전 보고에서 185개 전부를 `.bytes` 테이블로 설명한 부분을 정정합니다.
- `.bytes` 183개를 필드 이름이 있는 JSON으로 변환했습니다. 총 Data 행 수는 67,940행입니다.
- 변환 실패 0개, 미확인 필드 0개입니다.
- 원본 필드 번호, C# 속성명, 자료형, 반복 필드의 원소 자료형은 APK의 Unity 39 메타데이터와 네이티브 타입 등록 정보에서 복원했습니다.
- nullable/oneof는 getter 반환형으로 확인했습니다. NoInt 등 명시적인 빈 값 메시지도 그대로 보존했습니다.

## 파일

- `readable_tables/*.json`: 변환된 테이블. `Data` 배열 안에 행이 들어 있습니다.
- `table_field_dictionary.json`: 필드 번호와 이름, 자료형 사전입니다.
- `table_enum_dictionary.json`: Patchdata.Protobuf 열거형의 이름과 숫자 대응표입니다.
- `table_decode_validation.json`: 테이블별 행 수, 실패 및 미확인 필드 목록, 검증 횟수입니다.
- `PatchDataIdMap.csv`, `deleted_accepted_string_ids.csv`: 원래 묶음에 들어 있던 CSV입니다.

## 검증 및 해석 범위

- 모든 입력을 끝까지 읽었으며, protobuf 필드 태그·길이·값을 다시 인코딩해 원본 바이트와 일치하는지 검사했습니다.
- 문자열 UTF-8, 부호 있는 정수, 고정 길이 수치도 왕복 변환을 검사했습니다. 출력 JSON을 다시 읽어 메모리의 변환 결과와 동일한지 확인했습니다.
- 원본에 생략된 protobuf 기본값은 JSON에서도 생략합니다. 필드가 없다는 사실만으로 null 또는 미정 값으로 해석하지 마세요.
- 열거형 값은 원본 숫자를 유지합니다. 이름은 별도 사전을 참고하세요. 시간·비율·게임 내 단위는 별도 해석이 필요합니다.
- 이 결과는 원본 protobuf descriptor 전체를 복원한 것이 아니라 생성된 C# 메타데이터에 근거한 변환입니다. CLR 정수형만으로는 protobuf int와 sint를 구분할 수 없어 일반 int 해석을 적용했습니다. 바이트 보존 검증은 통과했으나, 이 검증만으로 게임 내 모든 수치 의미를 보증하지는 않습니다.
- 게임 실행이나 게임사 서버/CDN 접속 없이 로컬 파일만 처리했습니다.

## 재현

`metadata_schema.py` → `native_types.py` → `decode_tables.py` 순서입니다. Python 표준 라이브러리만 사용합니다. 입력은 이 작업 폴더의 복호화 파일과 원본에서 추출한 libil2cpp.so, packages/cookierun_1.0.002의 APK입니다.
