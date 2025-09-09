import subprocess
import sys
import os


def run_tests(schema_path: str, api_url: str, hooks_module: str) -> int:
    env = os.environ.copy()
    env["SCHEMATHESIS_HOOKS"] = hooks_module
    cmd = [
        sys.executable,
        "-m", "schemathesis.cli", "run",
        schema_path,
        "--url", api_url,
        "--checks", "all",
        # Исключаем все DELETE-запросы
        "--exclude-method", "DELETE",
        # Исключаем опасные эндпоинты по их путям
        "--exclude-path", ".*delete.*",
        "--exclude-path", ".*remove.*",
        "--exclude-path", ".*drop.*",
        "--exclude-path", ".*unlink.*"
    ]
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env)
    return result.returncode


if __name__ == "__main__":
    schema_file = r"G:/Project/!!!!!!!!!tool_helper/src/WEB/openapi.json"
    api_url = "http://192.168.0.10/backend/"
    hooks_module = "schemathesis_hooks"

    exit_code = run_tests(schema_file, api_url, hooks_module)
    sys.exit(exit_code)