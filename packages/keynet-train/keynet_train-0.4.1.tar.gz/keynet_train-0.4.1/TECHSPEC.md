# TECHSPEC: Training Image Upload Client (keynet-train)

## 문서 정보

- **버전**: 3.1 (Specification-Oriented)
- **작성일**: 2025-11-04
- **대상 모듈**: `keynet-train` (packages/train/)

## ⚠️ 버전 3.0 주요 변경사항

v2.0에서 작성된 TECHSPEC이 실제 코드베이스와 달라 전면 재작성:

- **CLI 프레임워크**: Typer → **argparse** (이미 구현됨)
- **명령어 이름**: `push` → **`push`** (이미 구현됨)
- **설정 관리**: PushSettings + keyring → **ConfigManager + JSON** (이미 구현됨)
- **워크플로우**: Backend API 직접 호출 → **`login` 후 `push`** (이미 구현됨)
- **하이퍼파라미터**: 수동 JSON 파일 → **자동 추출** + **Backend API 전송** (이미 구현됨)

---

## 1. 개요

### 1.1 목적

keynet-train 패키지의 **`push` 명령어**를 완성하여 사용자가 학습 스크립트를 Harbor Registry에 컨테이너 이미지로 배포할 수 있도록 합니다.

**전체 워크플로우**:

1. **`login`**: 플랫폼 서버 인증 → API token + Harbor Robot 계정 자격증명 저장 → 자동 podman login 실행
2. **`push train.py`**: 학습 이미지 push
   - Python 문법 검증 ✅ (구현 완료)
   - 하이퍼파라미터 자동 추출 (argparse/click/typer 지원) ✅ (구현 완료)
   - Backend API에서 uploadKey 발급 (하이퍼파라미터 함께 전송) 🚧 (TODO)
   - podman-py로 컨테이너 이미지 빌드 🚧 (TODO)
   - Harbor Registry에 이미지 푸시 🚧 (TODO)

**Harbor Robot 계정**: 플랫폼 서버 로그인 시 Backend가 자동으로 생성/관리하여 응답에 포함됩니다. CLI는 자동으로 `podman login`을 실행하므로 사용자는 Harbor 인증을 전혀 의식할 필요가 없습니다. (상세: @packages/train/AUTH.md 참조)

### 1.2 범위

**포함**:

- ✅ **이미 구현됨**:

  - CLI 프레임워크 (argparse 기반)
  - ConfigManager (설정 파일 관리)
  - `login/show/clear` 명령어
  - `push` 명령어 스케폴드
  - ArgumentParserExtractor (하이퍼파라미터 자동 추출)
  - PythonSyntaxValidator

- 🚧 **TODO (이번 구현 범위)**:
  - Backend API 클라이언트 (uploadKey + 하이퍼파라미터 전송)
  - podman-py 통합 (이미지 빌드 및 푸시)
  - 에러 처리
  - 프로그레스 표시

**제외**:

- Backend API 구현 (별도 Kotlin 프로젝트)
- Harbor Webhook 처리 (Backend 책임)
- Dockerfile 생성 (사용자가 제공)

### 1.3 성공 기준

- **AC-1**: `login`으로 서버 인증 및 Harbor 자격증명 저장 성공 ✅
- **AC-2**: `push`으로 하이퍼파라미터 자동 추출 성공 ✅
- **AC-3**: Backend API에 uploadKey + 하이퍼파라미터 전송 성공 🚧
- **AC-4**: podman-py로 Harbor Registry에 이미지 푸시 성공 🚧

---

## 2. 아키텍처 설계

### 2.1 현재 모듈 구조

```
packages/train/keynet_train/
├── cli/
│   ├── commands/
│   │   ├── config.py           ✅ 구현 완료
│   │   └── push.py           🚧 일부 구현
│   ├── config/
│   │   └── manager.py          ✅ 구현 완료
│   ├── parser/
│   │   ├── argparse_parser.py  ✅ 구현 완료
│   │   ├── click_parser.py     ✅ 구현 완료
│   │   ├── typer_parser.py     ✅ 구현 완료
│   │   └── extractor.py        ✅ 구현 완료
│   ├── validator.py            ✅ 구현 완료
│   └── main.py                 ✅ 구현 완료
├── clients/                    🚧 신규 생성 필요
│   ├── backend.py              🚧 TODO
│   └── podman.py            🚧 TODO
└── config/
    └── settings.py             ✅ 기존 (MLflow용, 별도 용도)
```

### 2.2 의존성 추가 필요

**pyproject.toml**:

```toml
dependencies = [
    # ... 기존 의존성 ...
    "httpx>=0.27.0",           # Backend API 호출 (신규)
    "podman>=5.0.0",           # Container 관리 (신규)
]
```

⚠️ **keyring 제거**: 실제로는 JSON 파일에 저장하므로 불필요

### 2.3 데이터 흐름

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: 초기 설정 (한 번만)                                   │
└─────────────────────────────────────────────────────────────┘

User: keynet-train login https://api.example.com
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  config.py                                                   │
│  - Username/Password 입력 받기                                │
│  - POST {server_url}/v1/auth/sign-in/one-time               │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼ Response (AUTH.md 참조):
       {
         "accessToken": "eyJhbGciOiJIUzI1NiIsInR...",
         "accessTokenExpiresAt": "2025-11-04T12:00:00Z",
         "user": {
           "id": "550e8400-e29b-41d4-a716-446655440000",
           "email": "user@example.com",
           "displayName": "User Name",
           "role": "GENERAL"
         },
         "harbor": {
           "url": "https://kitech-harbor.wimcorp.dev",
           "username": "robot$550e8400e29b41d4a716446655440000",  <- Robot 계정
           "password": "eyJhbGciOiJSUzI1NiIs..."      <- Robot 계정 password (JWT)
         }
       }
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  ConfigManager                                               │
│  - ~/.config/keynet/config.json에 저장 (권한 600)            │
└─────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────┐
│  STEP 2: 학습 이미지 제출                                      │
└─────────────────────────────────────────────────────────────┘

User: keynet-train push train.py --dockerfile ./Dockerfile
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  1. push.py - 검증 단계 ✅                                  │
│     - PythonSyntaxValidator: train.py 문법 검증              │
│     - ArgumentParserExtractor: 하이퍼파라미터 자동 추출      │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼ {"parser_type": "argparse", "arguments": [...]}
       │
┌─────────────────────────────────────────────────────────────┐
│  2. Backend API Client 🚧                                    │
│     - ConfigManager에서 API token 로드                        │
│     - POST /v1/projects/{projectId}/trains/images            │
│       Request: {modelName, hyperParameters}                  │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼ Response: {id, uploadKey, command}
       │
┌─────────────────────────────────────────────────────────────┐
│  3. Podman Client (podman-py) 🚧                          │
│     - ConfigManager에서 Harbor 자격증명 로드                  │
│     - podman.build(Dockerfile) → 이미지 빌드                 │
│     - image.tag(harbor/{project}/{uploadKey})                │
│     - podman.login(harbor) → Robot 계정으로 인증             │
│     - podman.push(tagged_image) → Harbor에 푸시              │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Harbor Registry                                             │
│  - 이미지: harbor/{project}/{uploadKey}                       │
│  - 하이퍼파라미터는 이미 Backend에 전송됨 (Step 2)            │
│  - PUSH_ARTIFACT 이벤트 → Webhook → Backend                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 상세 설계

### 3.1 ConfigManager ✅ (이미 구현됨)

**파일**: `cli/config/manager.py`

**책임**:

- 설정 파일 관리 (`~/.config/keynet/config.json`, 권한 600)
- 서버 로그인 응답 저장 (API token + Harbor Robot 계정 자격증명)
- 민감 정보 마스킹 (show 명령어)

**인터페이스** (AUTH.md 준수):

```python
class ConfigManager:
    """
    ~/.config/keynet/config.json 관리

    중요:
    - Harbor Robot 계정은 서버 로그인 시 자동 발급되어 포함됨
    - 파일 권한은 자동으로 600 설정 (보안)
    - show 시 password/token은 마스킹 처리
    """

    def save_credentials(
        self,
        server_url: str,
        username: str,
        api_token: str,
        api_token_expires_at: str,  # JWT 만료 시간 (ISO 8601)
        harbor: dict,  # {"url": str, "username": str, "password": str}
    ) -> None:
        """로그인 응답에서 받은 자격증명 저장"""

    def load_config(self) -> dict | None:
        """저장된 설정 반환 (없으면 None)"""

    def show_config(self) -> dict[str, Any]:
        """설정 표시 (password/token 마스킹)"""
```

**설정 파일 구조**:

```json
{
  "server_url": "https://api.example.com",
  "username": "myuser",
  "api_token": "eyJhbGciOiJIUzI1NiIsInR...",
  "api_token_expires_at": "2025-11-04T12:00:00Z",
  "harbor": {
    "url": "https://kitech-harbor.wimcorp.dev",
    "username": "robot$550e8400e29b41d4a716446655440000",
    "password": "eyJhbGciOiJSUzI1NiIs..."
  },
  "last_login": "2025-11-04T08:30:00"
}
```

**참조**: 인증 아키텍처 @packages/train/AUTH.md, Backend 사양 @packages/train/BACKEND_AUTH_SPEC.md

### 3.2 Backend API Client 🚧 (TODO)

**파일**: `clients/backend.py`

**책임**:

- Backend API 호출 (uploadKey + 하이퍼파라미터 전송)
- 인증 헤더 관리 (Bearer token)
- 요청/응답 데이터 변환 (snake_case ↔ camelCase)
- 에러 처리 (401/403/400/5xx)

**Backend API 계약**:

- `POST /v1/auth/sign-in/one-time`: 플랫폼 인증 및 Harbor credentials 발급 (@packages/train/AUTH.md, @packages/train/BACKEND_AUTH_SPEC.md)
- `GET /v1/projects/trainable`: 학습 가능한 프로젝트 목록 조회 (페이지네이션 지원)
- `POST /v1/projects/{projectId}/trains/images`: uploadKey 발급

**projectId 결정 방식**:
- `GET /v1/projects/trainable`로 프로젝트 목록 조회
- 사용자가 목록에서 선택
- 선택한 `TrainingProjectBrief.id`를 `projectId`로 사용

**Backend Request Schemas** (Kotlin):

```kotlin
// 프로젝트 조회 응답
data class FetchTrainableProjectsResponse(
    val content: List<TrainingProjectBrief>,
    val meta: OffSetPageMeta
)

data class TrainingProjectBrief(
    val id: Long,                    // projectId로 사용
    val title: String,
    val summary: String,
    val taskType: TrainingTaskType,  // OBJECT_DETECTION, SEGMENTATION, OBJECT_CLASSIFICATION
    val author: Author
)

// uploadKey 발급 요청
data class CreateTrainingImageRequest(
    val modelName: String,              // 모델 명 (예: "object_detection")
    val hyperParameters: List<ArgumentDefinition> = emptyList()  // 선택사항
)
```

**데이터 모델** (Backend ArgumentDefinition VO 호환):

```python
class ArgumentType(str, Enum):
    """Backend ArgumentType enum 미러링"""
    STRING = "str"
    INTEGER = "int"
    FLOAT = "float"
    BOOLEAN = "bool"

class ArgumentDefinition(BaseModel):
    """
    Backend ArgumentDefinition VO와 호환

    중요: ArgumentParserExtractor 출력을 이 형식으로 변환 필요
    """
    name: str
    type: ArgumentType
    default: Optional[Any] = None
    required: bool = False
    help: Optional[str] = None
    choices: Optional[List[str]] = None

class UploadKeyRequest(BaseModel):
    """snake_case → camelCase 변환"""
    model_name: str  # modelName으로 직렬화
    hyper_parameters: Optional[List[ArgumentDefinition]]  # hyperParameters로 직렬화

class UploadKeyResponse(BaseModel):
    """camelCase → snake_case 변환"""
    id: int
    upload_key: str  # uploadKey에서 역직렬화
    command: str

class TrainingProjectBrief(BaseModel):
    """프로젝트 목록 조회 응답의 개별 항목"""
    id: int                     # projectId로 사용
    title: str
    summary: str
    task_type: str              # taskType에서 역직렬화: "OBJECT_DETECTION" | "SEGMENTATION" | "OBJECT_CLASSIFICATION"
    author: dict                # {"id": UUID, "displayName": str}

class FetchTrainableProjectsResponse(BaseModel):
    """프로젝트 목록 조회 응답"""
    content: List[TrainingProjectBrief]
    meta: dict                  # {"total": int, "page": int, "limit": int, "maxPage": int}
```

**인터페이스**:

```python
class BackendAPIError(Exception):
    """Backend API 호출 실패"""

class AuthenticationError(BackendAPIError):
    """인증 실패 (401/403)"""

class ValidationError(BackendAPIError):
    """요청 검증 실패 (400)"""

class BackendClient:
    """
    Backend API 클라이언트

    중요:
    - Bearer token 인증 헤더 자동 추가
    - 하이퍼파라미터는 uploadKey 요청 시 함께 전송
    - ArgumentParserExtractor 출력을 ArgumentDefinition으로 변환 필요
    """

    def __init__(self, base_url: str, api_token: str) -> None:
        """ConfigManager에서 로드한 자격증명으로 초기화"""

    def fetch_trainable_projects(
        self,
        page: int = 0,
        limit: int = 20
    ) -> FetchTrainableProjectsResponse:
        """
        GET /v1/projects/trainable

        학습 가능한 프로젝트 목록 조회 (페이지네이션 지원)

        Raises:
            AuthenticationError: 인증 실패 (401/403)
            BackendAPIError: API 호출 실패 (5xx)
        """

    def request_upload_key(
        self,
        project_id: int,
        request: UploadKeyRequest
    ) -> UploadKeyResponse:
        """
        POST /v1/projects/{projectId}/trains/images

        하이퍼파라미터를 포함하여 uploadKey 발급 요청

        Raises:
            AuthenticationError: 인증 실패 (401/403)
            ValidationError: 요청 검증 실패 (400)
            BackendAPIError: API 호출 실패 (5xx)
        """
```

**ArgumentParserExtractor 출력 변환**:

ArgumentParserExtractor 출력을 Backend 호환 형식으로 변환 필요:

```python
# Input: ArgumentParserExtractor.extract_metadata()
{
    "parser_type": "argparse",
    "arguments": [{"name": "lr", "type": "float", "default": 0.001, ...}]
}

# Output: List[ArgumentDefinition]
def convert_to_argument_definitions(extractor_output: dict) -> List[ArgumentDefinition]:
    """
    ArgumentParserExtractor 출력을 ArgumentDefinition 리스트로 변환

    중요: type 문자열을 ArgumentType enum으로 변환 필요
    """
```

### 3.3 Podman Client (podman-py) 🚧 (TODO)

**파일**: `clients/podman.py`

**책임**:

- Dockerfile로 컨테이너 이미지 빌드
- uploadKey를 이미지 태그로 사용
- Harbor Registry 인증 (Robot 계정)
- 이미지 푸시

**주요 클래스**:

```python
from podman import PodmanClient
from typing import Optional

class ImageNotFoundError(Exception):
    """소스 이미지를 찾을 수 없음"""
    pass

class BuildError(Exception):
    """이미지 빌드 실패"""
    pass

class PushError(Exception):
    """이미지 푸시 실패"""
    pass

class PodmanClient:
    """
    Podman을 통한 컨테이너 이미지 빌드 및 푸시

    중요:
    - Robot 계정은 서버 로그인 시 자동 발급되어 ConfigManager에 저장됨
    - uploadKey는 repository 경로로 사용 (예: kitech-model/abc123xyz)
    - 빌드, 태그, 푸시 순서로 진행
    """

    def __init__(self, harbor_config: dict) -> None:
        """
        ConfigManager에서 로드한 Harbor Robot 계정으로 초기화

        Args:
            harbor_config: {"url": str, "username": str, "password": str}
        """

    def build_image(
        self,
        dockerfile_path: str,
        context_path: str = ".",
        no_cache: bool = False
    ) -> str:
        """
        Dockerfile로 컨테이너 이미지 빌드

        Returns:
            빌드된 이미지 ID

        Raises:
            BuildError: 빌드 실패
        """

    def tag_image(
        self,
        image_id: str,
        upload_key: str,
        project: str
    ) -> str:
        """
        이미지에 uploadKey 태그 추가

        Returns:
            태그된 이미지 전체 경로 ({harbor_registry}/{project}/{upload_key})

        Raises:
            ImageNotFoundError: 소스 이미지를 찾을 수 없음
        """

    def push_image(self, tagged_image: str) -> None:
        """
        Harbor Registry에 이미지 푸시

        Raises:
            PushError: 푸시 실패
        """
```

### 3.5 Push 명령어 상세 흐름 🚧 (TODO)

**파일**: `cli/commands/push.py`

**함수 시그니처**:

```python
def handle_push(args: argparse.Namespace) -> int:
    """
    Push 명령어 처리

    Args:
        args.entrypoint: 훈련 스크립트 경로 (필수)
        args.dockerfile: Dockerfile 경로 (선택, 기본: ./Dockerfile)
        args.no_cache: 빌드 캐시 비활성화 (선택, 기본: False)

    Returns:
        Exit code: 0 (성공) / 1 (실패)
    """
```

**처리 흐름**:

#### Step 1: 인증 확인

**담당 클래스**: `ConfigManager`

**입력**: 없음 (파일 시스템에서 로드)

**처리**:
- `~/.config/keynet/config.json` 존재 여부 확인
- 파일이 없으면 "Not logged in" 에러 메시지 출력 후 종료

**출력**:
```python
config = {
    "server_url": str,
    "api_token": str,
    "api_token_expires_at": str,  # ISO 8601
    "harbor": {
        "url": str,
        "username": str,  # Robot 계정
        "password": str   # Robot 계정
    }
}
```

**실패 처리**: Exit code 1, "❌ Not logged in. Run: keynet-train login"

---

#### Step 2: Entrypoint 검증

**담당 클래스**: `PythonSyntaxValidator`

**입력**: `args.entrypoint` (Path)

**검증**:
- 파일 존재 여부
- Python 문법 오류 검사 (ast.parse 사용)
- ArgumentParser 사용 여부 검증 (선택)

**출력**: 검증 통과 (예외 발생 시 실패)

**실패 처리**: `ValidationError` 발생 → Exit code 1

---

#### Step 3: 하이퍼파라미터 추출

**담당 클래스**: `ArgumentParserExtractor`

**입력**: `args.entrypoint` (str)

**처리**:
- 스크립트에서 argparse/click/typer 사용 여부 탐지
- 각 argument의 메타데이터 추출 (name, type, default, required, help, choices)

**출력**:
```python
{
    "parser_type": "argparse" | "click" | "typer",
    "arguments": [
        {
            "name": str,
            "type": str,  # "str" | "int" | "float" | "bool"
            "default": Any,
            "required": bool,
            "help": str,
            "choices": List[str] | None
        }
    ]
}
```

**변환**: `convert_to_argument_definitions()` 함수로 Backend 호환 형식으로 변환
- ArgumentParserExtractor 출력 → `List[ArgumentDefinition]`

---

#### Step 4: 프로젝트 선택

**담당 클래스**: `BackendClient`

**입력**:
- `config["server_url"]`, `config["api_token"]` (인증)

**처리**:
1. `GET /v1/projects/trainable?page=0&limit=20` 호출
2. 프로젝트 목록을 사용자에게 표시:
   ```
   학습 가능한 프로젝트 목록:
   [1] 객체 탐지 모델 (OBJECT_DETECTION) - 홍길동
   [2] 세그멘테이션 모델 (SEGMENTATION) - 김철수
   ...
   선택하세요 (1-20): _
   ```
3. 사용자 입력 받기
4. 선택한 프로젝트의 `id`를 `project_id`로 사용

**출력**: `project_id` (int)

**실패 처리**:
- `AuthenticationError` (401/403): 재로그인 요청
- `BackendAPIError` (5xx): 서버 오류
- 잘못된 선택: 재입력 요청

**중요 결정 필요**:
> **TODO**: 선택한 `project_id`를 어떻게 관리할지 결정 필요
>
> **옵션 A**: config.json에 저장하여 재사용
> ```json
> {
>   "project_id": 123,
>   "project_title": "객체 탐지 모델"
> }
> ```
> - 장점: 매번 선택 불필요
> - 단점: 프로젝트 변경 시 재설정 필요
>
> **옵션 B**: 매번 선택
> - 장점: 유연성
> - 단점: 매번 입력 필요
>
> **옵션 C**: `keynet-train project select` 명령 추가
> - 장점: 명시적 관리
> - 단점: 추가 명령어 구현 필요

---

#### Step 5: UploadKey 발급

**담당 클래스**: `BackendClient`

**입력**:
- `config["server_url"]`, `config["api_token"]` (인증)
- `project_id` (Step 4 출력)
- `UploadKeyRequest`:
  - `model_name`: entrypoint 파일명 또는 사용자 지정
  - `hyper_parameters`: Step 3에서 변환된 `List[ArgumentDefinition]`

**API 호출**:
```http
POST /v1/projects/{projectId}/trains/images
Authorization: Bearer {accessToken}
Content-Type: application/json

{
  "modelName": "object_detection",
  "hyperParameters": [
    {
      "name": "learning_rate",
      "type": "float",
      "default": "0.001",
      "required": false,
      "help": "Learning rate for training"
    },
    {
      "name": "batch_size",
      "type": "int",
      "default": "32",
      "required": true,
      "help": "Batch size for training"
    }
  ]
}
```

**출력**: `UploadKeyResponse`
```python
{
    "id": 123,
    "upload_key": "abc123xyz456789012345",  # NanoId 21자
    "command": "python train.py --learning_rate 0.001 --batch_size 32"
}
```

**실패 처리**:
- `AuthenticationError` (401/403): 재로그인 요청
- `ValidationError` (400): 요청 데이터 검증 실패
- `BackendAPIError` (5xx): 서버 오류

---

#### Step 6: 컨테이너 이미지 빌드

**담당 클래스**: `PodmanClient`

**입력**:
- `config["harbor"]`: Harbor 설정 dict (url, username, password)
- `dockerfile_path`: Dockerfile 경로
- `context_path`: 빌드 컨텍스트 (기본: 현재 디렉토리)
- `no_cache`: 캐시 사용 여부

**처리**: `podman.build_image()`
- Dockerfile 기반 컨테이너 이미지 빌드
- 빌드 로그를 사용자에게 실시간 표시

**출력**: `image_id` (str, 예: "a1b2c3d4e5f6...")

**실패 처리**: `BuildError` → Exit code 1

---

#### Step 7: 이미지 태깅

**담당 클래스**: `PodmanClient`

**입력**:
- `image_id` (Step 6 출력)
- `upload_key` (Step 5 출력)
- `project`: Harbor 프로젝트명 (예: "kitech-model")

**처리**: `podman.tag_image()`
- 이미지에 태그 추가
- 태그 형식: `{harbor_registry}/{project}/{upload_key}` (스킴 제외)
- 예: `kitech-harbor.wimcorp.dev/kitech-model/abc123xyz456789012345`

**출력**: `tagged_image` (str, 전체 이미지 경로)

**실패 처리**: `ImageNotFoundError` → Exit code 1

---

#### Step 8: 이미지 푸시

**담당 클래스**: `PodmanClient`

**입력**: `tagged_image` (Step 7 출력)

**처리**: `podman.push_image()`
- Harbor Registry에 이미지 푸시
- 푸시 진행 상황을 사용자에게 표시

**출력**: 없음 (성공 시)

**실패 처리**: `PushError` → Exit code 1

**중요**: Harbor 인증은 `keynet-train login` 명령 실행 시 이미 완료되었음 (podman credential helper에 저장됨)

---

#### Step 9: 결과 출력

**출력 정보**:
```
✨ Push completed successfully!
   Upload Key: {upload_key}
   Image: {tagged_image}
   Hyperparameters: {count} arguments sent to Backend

Note: Hyperparameters were sent to Backend API during uploadKey request.
```

**Exit code**: 0 (성공)

---

**클래스 의존성 흐름**:

```
handle_push()
  ├─> ConfigManager.load_config()                                 # Step 1
  │     └─> config: Dict
  │
  ├─> PythonSyntaxValidator.validate_file()                       # Step 2
  │     └─> 검증 통과
  │
  ├─> ArgumentParserExtractor.extract_metadata()                  # Step 3
  │     └─> metadata: Dict
  │
  ├─> convert_to_argument_definitions(metadata)                   # Step 3
  │     └─> hyper_params: List[ArgumentDefinition]
  │
  ├─> BackendClient(config["server_url"], config["api_token"])
  │   ├─> fetch_trainable_projects()                             # Step 4
  │   │     └─> projects: List[TrainingProjectBrief]
  │   │     └─> 사용자 선택 → project_id
  │   │
  │   └─> request_upload_key(project_id, UploadKeyRequest)       # Step 5
  │         └─> response: UploadKeyResponse
  │
  └─> PodmanClient(config["harbor"])
      ├─> build_image() → image_id                                # Step 6
      ├─> tag_image(image_id, upload_key, project) → tagged_image # Step 7
      └─> push_image(tagged_image)                                # Step 8
          # Harbor 인증은 login 명령에서 이미 완료됨
```

**중요 원칙**:

1. **순차 실행**: 각 단계는 이전 단계의 성공을 전제로 함
2. **조기 종료**: 어느 단계에서든 실패 시 즉시 종료 (exit code 1)
3. **에러 메시지**: 각 단계 실패 시 사용자에게 명확한 에러 메시지 제공
4. **진행 상황 표시**: 각 주요 단계 시작/완료 시 사용자에게 알림

---

## 4. CLI 사용법

### 4.1 초기 설정 (한 번만)

```bash
# 플랫폼 서버 로그인
keynet-train login https://api.example.com

# 프롬프트:
# Username: myuser
# Password: ********

# 응답: API token + Harbor Robot 계정 자격증명 저장됨 + 자동 podman login
# ✓ Credentials stored at: ~/.config/keynet/config.json
```

**설정 확인**:

```bash
keynet-train config show
```

출력 (AUTH.md 구조):

```json
{
  "server_url": "https://api.example.com",
  "username": "myuser",
  "api_token": "eyJhbG...abc",
  "api_token_expires_at": "2025-11-04T12:00:00Z",
  "harbor": {
    "url": "https://kitech-harbor.wimcorp.dev",
    "username": "robot$550e8400e29b41d4a716446655440000",
    "password": "ABCD...xyz"
  },
  "last_login": "2025-11-04T08:30:00"
}
```

### 4.2 학습 이미지 제출

```bash
# 기본 사용
keynet-train push train.py

# Dockerfile 위치 지정
keynet-train push train.py --dockerfile ./custom/Dockerfile

# 커스텀 태그 추가
keynet-train push train.py --tag latest --tag v1.0.0

# 캐시 사용 안 함
keynet-train push train.py --no-cache
```

**출력 예시**:

```
🔍 Validating entrypoint...
✓ Entrypoint validated: train.py

📝 Extracting argument metadata...
✓ Detected argparse parser with 5 arguments

📡 Requesting uploadKey from Backend...
✅ UploadKey received: abc123xyz456789012345

🐳 Building container image...
Step 1/8 : FROM python:3.10-slim
 ---> ...
✅ Image built: a1b2c3d4e5f6

🏷️  Tagging image...
🔐 Logging in to Harbor...
🚀 Pushing image to Harbor: kitech-harbor.wimcorp.dev/kitech-model/abc123xyz456789012345
✅ Image pushed successfully

📦 Attaching hyperparameter metadata...
✅ Metadata attached successfully

✨ Push completed successfully!
   Upload Key: abc123xyz456789012345
   Image: kitech-harbor.wimcorp.dev/kitech-model/abc123xyz456789012345
   Hyperparameters: 5 arguments
```

---

## 5. 에러 처리

### 5.1 에러 시나리오 및 복구 전략

| 에러 시나리오               | 에러 타입           | 복구 전략                                |
| --------------------------- | ------------------- | ---------------------------------------- |
| 설정 파일 없음              | ConfigError         | `login` 실행 안내                        |
| 인증 실패 (401/403)         | AuthenticationError | 즉시 중단, `login` 재실행 안내           |
| 요청 데이터 검증 실패 (400) | ValidationError     | 즉시 중단, 하이퍼파라미터 형식 확인 안내 |
| Dockerfile 없음             | BuildError          | 즉시 중단, Dockerfile 경로 확인 안내     |
| 이미지 빌드 실패            | BuildError          | 즉시 중단, 빌드 로그 출력                |
| Harbor 인증 실패            | AuthenticationError | 즉시 중단, `login` 재실행 안내           |

### 5.2 에러 메시지 예시

**설정 파일 없음**:

```
❌ Error: No Harbor credentials configured

Please login first:
    keynet-train login https://api.example.com

After login, your API token and Harbor credentials will be stored at:
    ~/.config/keynet/config.json
```

**Backend API 인증 실패**:

```
❌ Error: Backend API authentication failed

API returned 401 Unauthorized.

Possible causes:
- API token has expired
- Token has been revoked
- Server configuration changed

Please login again:
    keynet-train login https://api.example.com
```

**Harbor Robot 계정 인증 실패**:

```
❌ Error: Harbor Registry authentication failed

Failed to login to harbor.example.com

Possible causes:
- Harbor Robot account has been revoked or expired
- Harbor credentials in config are invalid

Please re-login to refresh credentials:
    keynet-train login https://api.example.com

The server will issue a new Robot account automatically.
```

**이미지 빌드 실패**:

```
❌ Error: Container image build failed

Build failed at step 3:
    RUN pip install -r requirements.txt

Error: Could not find package 'nonexistent-package'

Please check:
1. Dockerfile syntax is correct
2. All dependencies are available
3. Base image is accessible

Dockerfile: ./Dockerfile
```

---

## 6. 테스트 전략

### 6.1 Unit Tests

**파일**: `tests/clients/test_backend.py`

```python
def test_request_upload_key_success(httpx_mock):
    """uploadKey 발급 성공"""
    httpx_mock.add_response(
        json={"id": 1, "uploadKey": "abc123", "command": "..."}
    )
    ...

def test_request_upload_key_authentication_error(httpx_mock):
    """인증 실패 시 AuthenticationError 발생"""
    httpx_mock.add_response(status_code=401)
    ...

def test_convert_to_argument_definitions():
    """ArgumentParserExtractor 출력을 ArgumentDefinition으로 변환"""
    extractor_output = {
        "parser_type": "argparse",
        "arguments": [
            {"name": "lr", "type": "float", "default": 0.001}
        ]
    }
    definitions = convert_to_argument_definitions(extractor_output)
    assert len(definitions) == 1
    assert definitions[0].name == "lr"
    assert definitions[0].type == ArgumentType.FLOAT
```

**파일**: `tests/clients/test_podman.py`

```python
def test_build_image(mock_podman):
    """이미지 빌드 성공"""
    mock_podman.images.build.return_value = (Mock(id="abc123"), [])
    ...

def test_tag_image(mock_podman):
    """이미지 태그 성공"""
    ...

def test_push_image(mock_podman):
    """이미지 푸시 성공"""
    ...
```

### 6.2 Integration Tests

**파일**: `tests/integration/test_push_flow.py`

```python
@pytest.mark.integration
def test_full_push_flow(tmp_path):
    """
    전체 push 플로우 통합 테스트

    1. Mock Backend API 서버
    2. Mock podman 이미지 빌드
    3. Mock Harbor Registry
    4. push 명령어 실행
    5. 결과 검증
    """
    # ConfigManager에 테스트 자격증명 설정
    config_manager = ConfigManager(str(tmp_path / "config.json"))
    config_manager.set_credentials(...)

    # push 실행
    result = handle_push(args)

    # 검증
    assert result == 0
    ...
```

### 6.3 E2E Tests (Manual)

**시나리오**:

1. 실제 Backend API에 로그인
2. 실제 학습 스크립트로 push 실행
3. Harbor Registry에 이미지 푸시 확인
4. Backend에서 uploadKey 요청 시 하이퍼파라미터 수신 확인
5. Backend에서 Webhook 수신 확인

---

## 7. 구현 체크리스트

### 7.1 TODO

- [ ] `clients/backend.py` 구현

  - [ ] `BackendClient` 클래스
  - [ ] `convert_to_argument_definitions()` 함수
  - [ ] 에러 타입 정의

- [ ] `clients/podman.py` 구현

  - [ ] `PodmanClient` 클래스
  - [ ] `build_image()` 메서드
  - [ ] `tag_image()` 메서드
  - [x] ~~`login_registry()` 메서드~~ (제거됨: Harbor 인증은 login 시 완료)
  - [ ] `push_image()` 메서드

- [ ] `cli/commands/push.py` 업데이트

  - [ ] Backend API 호출 통합
  - [ ] Podman Client 통합
  - [ ] 프로그레스 표시 개선

- [ ] `cli/commands/config.py` 업데이트

  - [ ] `handle_login()` 실제 API 호출 구현 (현재 TODO)

- [ ] 의존성 추가 (`pyproject.toml`)

  - [ ] httpx
  - [ ] podman (podman-py)

- [ ] 테스트 작성

  - [ ] Unit tests (backend, podman)
  - [ ] Integration tests (push flow)

- [ ] 문서화
  - [ ] README 업데이트
  - [ ] 예시 Dockerfile 제공

---

## 8. 다음 단계

**TECHSPEC v3.0 승인 후**:

1. `PLAN.md` 작성 (TDD 방식 상세 구현 계획)
2. 환경 검증:
   - podman 설치 확인
   - Backend API 접근 확인
   - Harbor Registry 접근 확인
3. TDD 방식으로 구현:
   - RED: 테스트 작성
   - GREEN: 최소 구현
   - REFACTOR: 리팩토링

---

## 9. 참고 문서

- **CLAUDE.md**: 프로젝트 개발 가이드 (TDD, 코드 스타일)
- **VERSIONING.md**: 버전 관리 전략
- **RUFF_TECHSPEC.md**: Backend API 사양서 (ArgumentDefinition 참조)
- [podman-py Documentation](https://podman-py.readthedocs.io/)
- [httpx Documentation](https://www.python-httpx.org/)

---

## 10. 변경 이력

### v3.1 (2025-11-04) - Specification-Oriented Refactoring

**이유**: 기술 사양서로서 적절성 개선 - 구현 세부사항 제거, 인터페이스/계약 중심으로 재구성

**주요 변경사항**:

1. **구현 제거 → 인터페이스 유지**:
   - ConfigManager: 메서드 시그니처만 유지, 구현 제거
   - BackendClient: 메서드 시그니처만 유지, 재시도 로직 제거
   - PodmanClient: 메서드 시그니처만 유지, podman-py API 호출 제거 (~120줄)
   - handle_push(): 워크플로우 개요만 유지, 110줄 구현 제거

2. **재시도 관련 내용 완전 제거**:
   - tenacity 의존성 제거
   - @retry 데코레이터 구현 제거
   - TODO 체크리스트에서 "재시도 로직" 제거
   - 참고 문서에서 tenacity 링크 제거

3. **핵심 가치 보존**:
   - API 계약 명시 (Request/Response 형식)
   - 데이터 모델 구조 (Pydantic BaseModel)
   - 중요 노트 및 주의사항
   - 예외 타입 정의

**삭제된 내용**:

- 구체적인 구현 코드 (~300줄)
- try-catch 블록, for 루프, 상세 로직
- tenacity 재시도 구현 및 의존성

**결과**:

- 사양서로서 명확한 역할: WHAT과 WHY 중심
- 구현팀의 자율성 보장: HOW는 구현자 결정
- 유지보수성 향상: 구현 변경 시 사양서 수정 불필요

---

### v3.0 (2025-11-04) - Major Rewrite

**이유**: v2.0 사양서가 실제 코드베이스와 완전히 달라 전면 재작성

**주요 변경사항**:

1. **CLI 프레임워크**: Typer → **argparse** (실제 구현 반영)
2. **명령어**: `push` → **`push`** (실제 구현 반영)
3. **설정 관리**:
   - PushSettings + keyring → **ConfigManager + JSON** (실제 구현 반영)
   - ⚠️ **keyring 의존성 제거** (실제로 JSON 파일 사용)
4. **워크플로우**: Backend API 직접 호출 → **`login` → `push`** (실제 구현 반영)
5. **하이퍼파라미터**: 수동 JSON 파일 → **ArgumentParserExtractor 자동 추출 + Backend API 전송** (실제 구현 반영)
6. **이미 구현된 것과 TODO 명확히 구분**:
   - ✅ CLI 프레임워크, ConfigManager, ArgumentParserExtractor
   - 🚧 Backend API Client, Podman Client

**삭제된 내용**:

- PushSettings 클래스 (실제로는 ConfigManager 사용)
- keyring 의존성 (실제로는 JSON 파일 사용)
- `push` 명령어 사양 (실제로는 `push` 사용)
- Typer 기반 CLI 사양 (실제로는 argparse 사용)

**추가된 내용**:

- ConfigManager 상세 설명 (이미 구현된 것)
- ArgumentParserExtractor 활용 방법
- `convert_to_argument_definitions()` 변환 함수
- Backend API와 ArgumentParserExtractor 출력 통합
- uploadKey 요청 시 하이퍼파라미터 함께 전송하는 방식

---

## 부록: ArgumentDefinition 예시

**ArgumentParserExtractor 출력**:

```json
{
  "parser_type": "argparse",
  "arguments": [
    {
      "name": "learning_rate",
      "type": "float",
      "default": 0.001,
      "required": false,
      "help": "Learning rate for training"
    },
    {
      "name": "batch_size",
      "type": "int",
      "default": 32,
      "required": true,
      "help": "Batch size"
    },
    {
      "name": "optimizer",
      "type": "str",
      "default": "adam",
      "choices": ["adam", "sgd", "rmsprop"],
      "help": "Optimizer algorithm"
    }
  ]
}
```

**Backend API Request (camelCase)**:

```json
{
  "modelName": "train.py",
  "hyperParameters": [
    {
      "name": "learning_rate",
      "type": "float",
      "default": 0.001,
      "required": false,
      "help": "Learning rate for training"
    },
    {
      "name": "batch_size",
      "type": "int",
      "default": 32,
      "required": true,
      "help": "Batch size"
    },
    {
      "name": "optimizer",
      "type": "str",
      "default": "adam",
      "choices": ["adam", "sgd", "rmsprop"],
      "help": "Optimizer algorithm"
    }
  ]
}
```

**Note**: 하이퍼파라미터는 Backend API의 uploadKey 요청 시 함께 전송됩니다. 별도의 메타데이터 첨부 과정은 없습니다.
