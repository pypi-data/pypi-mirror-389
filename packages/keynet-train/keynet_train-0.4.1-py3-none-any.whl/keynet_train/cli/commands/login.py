"""
Login command implementation.

This module implements the 'login' command for server authentication.
"""

import argparse
import getpass
import sys

from ..config.manager import ConfigManager


def setup_login_parser(subparsers: argparse._SubParsersAction) -> None:
    """
    Set up the login command parser.

    Args:
        subparsers: Subparsers action from parent parser

    """
    parser = subparsers.add_parser(
        "login",
        help="Login to keynet server",
        description="Authenticate with keynet server and store credentials",
        epilog="""
Examples:
    # Login to server (prompts for username/password)
    keynet-train login https://api.example.com

    # Login with username specified
    keynet-train login https://api.example.com --username myuser

Notes:
    - Configuration is stored at ~/.config/keynet/config.json
    - File permissions are automatically set to 600 (owner only)
    - API token and Harbor credentials are stored in config file
    - After login, podman is automatically logged into Harbor
        """,
    )

    parser.add_argument(
        "server_url",
        type=str,
        help="Server URL (e.g., https://api.example.com)",
    )

    parser.add_argument(
        "--username",
        type=str,
        help="Username (will prompt if not provided)",
    )

    parser.set_defaults(func=handle_login)


def handle_login(args: argparse.Namespace) -> int:
    """
    Handle login command execution.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for error)

    """
    config_manager = ConfigManager()

    try:
        server_url = args.server_url

        # Get username
        username = args.username
        if not username:
            username = input("사용자명: ")

        # Get password (securely)
        password = getpass.getpass("비밀번호: ")

        print()
        print(f"🔐 {server_url}에 로그인 중...")

        # TODO: Implement actual server API call
        # For now, this is a placeholder
        print("⚠️  미구현: 서버 로그인 API 호출")
        print()
        print("예상 워크플로우:")
        print(f"  1. POST {server_url}/api/login")
        print(f"     Body: {{username: '{username}', password: '***'}}")
        print("  2. 응답 수신:")
        print("     {")
        print('       "apiToken": "...",')
        print('       "apiTokenExpiresAt": "...",')
        print('       "harbor": {')
        print('         "url": "harbor.example.com",')
        print('         "username": "robot$...",')
        print('         "password": "...",')
        print('         "expiresAt": "..."')
        print("       }")
        print("     }")
        print("  3. ~/.config/keynet/config.json에 자격증명 저장")
        print("  4. 'podman login' 자동 실행")
        print()

        # Placeholder: simulate successful login
        # In real implementation, use httpx to call server API
        # See AUTH.md for complete implementation details
        # Example:
        # import httpx
        # response = httpx.post(
        #     f"{server_url}/api/login",
        #     json={"username": username, "password": password},
        # )
        # if response.status_code != 200:
        #     print(f"로그인 실패: {response.status_code}", file=sys.stderr)
        #     return 1
        # data = response.json()
        # config_manager.save_credentials(
        #     server_url=server_url,
        #     username=username,
        #     api_token=data["apiToken"],
        #     harbor_url=data["harbor"]["url"],
        #     harbor_username=data["harbor"]["username"],
        #     harbor_password=data["harbor"]["password"],
        # )
        # # Auto podman login
        # import subprocess
        # subprocess.run(
        #     ["podman", "login", data["harbor"]["url"],
        #      "--username", data["harbor"]["username"],
        #      "--password-stdin"],
        #     input=data["harbor"]["password"].encode(),
        # )

        print("✓ 자격증명 저장 위치:", config_manager.config_path)
        print()
        print("구현 필요 항목:")
        print("  - httpx 의존성 추가")
        print("  - 서버 API 호출 구현 (AUTH.md 참조)")
        print("  - 인증 에러 처리")
        print("  - podman 자동 로그인")

        return 0

    except Exception as e:
        print(f"오류: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1
