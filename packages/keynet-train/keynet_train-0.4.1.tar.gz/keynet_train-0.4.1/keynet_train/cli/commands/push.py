"""
Push command implementation.

This module implements the 'push' command that builds and pushes
container images for training templates.

ARCHITECTURE (Backend API + podman):
1. Extract hyperparameters from training script
2. Request uploadKey from Backend API (with hyperparameters)
3. Build container image with podman
4. Tag and push image to Harbor Registry
"""

import argparse
import sys
from pathlib import Path

from ..config.manager import ConfigManager
from ..parser.extractor import ArgumentParserExtractor
from ..validator import PythonSyntaxValidator


def setup_push_parser(subparsers: argparse._SubParsersAction) -> None:
    """
    Set up the push command parser.

    Args:
        subparsers: Subparsers action from parent parser

    """
    parser = subparsers.add_parser(
        "push",
        help="Build and push training container image",
        description="Build container image with podman and send metadata to Backend API",
        epilog="""
Examples:
    # Build and push training image (after login)
    keynet-train push train.py

    # Specify Dockerfile location
    keynet-train push train.py --dockerfile ./Dockerfile

    # Add custom tags
    keynet-train push train.py --tag latest --tag v1.0.0

Notes:
    - Requires 'keynet-train login' first
    - Uses Harbor credentials and API token from config
    - Requires podman installed and configured
    - Hyperparameters extracted automatically from argparse/click/typer
    - Hyperparameters sent to Backend API during uploadKey request
        """,
    )

    parser.add_argument(
        "entrypoint",
        type=str,
        help="Path to training script entrypoint (e.g., train.py)",
    )

    parser.add_argument(
        "--dockerfile",
        type=str,
        default="./Dockerfile",
        help="Path to Dockerfile (default: ./Dockerfile)",
    )

    parser.add_argument(
        "--tag",
        type=str,
        action="append",
        default=None,
        help="Image tags (can specify multiple times, default: latest)",
    )

    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Build without using cache",
    )

    parser.set_defaults(func=handle_push)


def handle_push(args: argparse.Namespace) -> int:
    """
    Handle push command execution.

    WORKFLOW:
    1. Validate entrypoint file exists and has valid Python syntax
    2. Extract argument metadata (argparse/click/typer)
    3. Select project from Backend API
    4. Request uploadKey from Backend API (with hyperparameters)
    5. Build container image with podman
    6. Tag image with uploadKey
    7. Push image to Harbor Registry

    Args:
        args: Parsed command-line arguments containing:
            - entrypoint: Path to training script
            - dockerfile: Path to Dockerfile
            - tag: Image tags (list)
            - no_cache: Build without cache

    Returns:
        Exit code:
            - 0: Success
            - 1: Error

    """
    try:
        # Step 0: Load configuration and get credentials
        config_manager = ConfigManager()

        # Check for Harbor credentials
        harbor_creds = config_manager.get_harbor_credentials()
        if not harbor_creds:
            print("오류: Harbor 자격증명이 설정되지 않음", file=sys.stderr)
            print(
                "먼저 로그인하세요: keynet-train login <server-url>",
                file=sys.stderr,
            )
            return 1

        # Check for API key
        api_key = config_manager.get_api_key()
        if not api_key:
            print("경고: API 키를 찾을 수 없음", file=sys.stderr)
            print("인증 없이는 일부 기능이 작동하지 않을 수 있음", file=sys.stderr)

        # Step 1: Validate entrypoint
        print("🔍 엔트리포인트 검증 중...")
        entrypoint = Path(args.entrypoint)

        if not entrypoint.exists():
            print(
                f"오류: 엔트리포인트 파일을 찾을 수 없음: {args.entrypoint}",
                file=sys.stderr,
            )
            return 1

        if not entrypoint.is_file():
            print(
                f"오류: 엔트리포인트가 파일이 아님: {args.entrypoint}", file=sys.stderr
            )
            return 1

        # Validate Python syntax
        validator = PythonSyntaxValidator()
        success, error = validator.validate_file(entrypoint)

        if not success:
            print("오류: Python 문법 검증 실패:", file=sys.stderr)
            print(error, file=sys.stderr)
            return 1

        print(f"✓ 엔트리포인트 검증 완료: {entrypoint.name}")
        print()

        # Step 2: Extract argument metadata
        print("📝 인자 메타데이터 추출 중...")
        extractor = ArgumentParserExtractor()
        args_metadata = extractor.extract_metadata(str(entrypoint))

        if args_metadata.get("parser_type"):
            arg_count = len(args_metadata.get("arguments", []))
            print(f"✓ {args_metadata['parser_type']} 파서 감지됨 (인자 {arg_count}개)")
            print()
        else:
            print("⚠ 인자 파서 감지 안 됨")
            print()

        # Step 3: Build container image
        print("🐳 컨테이너 이미지 빌드 중...")
        print(f"   Harbor 레지스트리: {harbor_creds['url']}")
        print(f"   Harbor 사용자명: {harbor_creds['username']}")
        print(f"   Dockerfile: {args.dockerfile}")
        tags = args.tag if args.tag else ["latest"]
        print(f"   태그: {', '.join(tags)}")
        print()

        if api_key:
            print("✓ API 키 확인됨")
        print("✓ Harbor 자격증명 확인됨")
        print()

        # TODO: Implement Backend API client and podman integration
        print("⚠️  미구현: Backend API 및 podman 통합")
        print("    다음 단계:")
        print("    1. Backend API에서 프로젝트 선택")
        print("    2. uploadKey 요청 (하이퍼파라미터 포함)")
        print("    3. podman으로 Dockerfile에서 이미지 빌드")
        print("    4. uploadKey로 이미지 태그")
        print("    5. Harbor Registry에 이미지 푸시")
        print()

        # Placeholder for new implementation
        print("📦 Backend에 전송될 하이퍼파라미터 메타데이터:")
        import json

        print(json.dumps(args_metadata, indent=2, ensure_ascii=False))
        print()

        print("✓ Push 워크플로우 검증 완료 (구현 대기 중)")
        return 0

    except Exception as e:
        print(f"오류: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1
