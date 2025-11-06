import ast
import base64
import fnmatch
import importlib.metadata
import importlib.util
import io
import json
import os
import platform
import re
import sys
import tempfile
import uuid
import zipfile
from typing import Dict

import requests
import websockets
import yaml
from dotenv import dotenv_values

import qupiato.cli.config as c


async def ws_api_call(req: Dict):
    async with websockets.connect(c.DEPLOYER_WS_URL) as ws:
        await ws.send(json.dumps(req))

        while True:
            try:
                resp = await ws.recv()
                data = json.loads(resp)
                yield data
            except websockets.exceptions.ConnectionClosedOK:
                break

            except websockets.exceptions.ConnectionClosedError:
                break


def encode_secret(env_file=None):
    exclude_dirs = get_exclude_dirs()

    def load_and_encode(file_path):
        """Helper function to load and encode a .env file."""
        env_config = dotenv_values(file_path)
        env_content = "\n".join(f"{key}={value}" for key, value in env_config.items())
        return base64.b64encode(env_content.encode("utf-8")).decode("utf-8")

    if env_file:
        if os.path.isfile(env_file):
            return load_and_encode(env_file)
        else:
            return None

    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            file_path = os.path.normpath(os.path.join(root, file))
            if file_path == ".env":
                return load_and_encode(file_path)

    return None


# 현재 디렉토리와 하위 디렉토리에 있는 모든 파일 압축
def create_zip_archive(zip_filename):
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in iter_pack_candidates():
            zipf.write(file_path, os.path.relpath(file_path))


def load_qignore(file_path=".qignore"):
    if not os.path.isfile(file_path):
        return set()
    with open(file_path, "r") as f:
        ignored_patterns = set(line.strip() for line in f if line.strip() and not line.startswith("#"))
    return ignored_patterns


def is_ignored(file_path, ignored_patterns):
    for pattern in ignored_patterns:
        if pattern.endswith("/"):
            pattern = pattern + "*"

        if fnmatch.fnmatch(file_path, pattern):
            return True
    return False


def get_exclude_dirs():
    exclude_dirs = {"__pycache__", ".venv", ".git"}  # 제외할 디렉토리 목록
    return exclude_dirs


def _is_pack_included(file_path, ignored_patterns):
    norm_path = os.path.normpath(file_path)
    d_name = os.path.dirname(norm_path)
    f_name = os.path.basename(norm_path)

    if f_name.startswith(".env"):
        return False
    if f_name == "db.json":
        return False
    if f_name.startswith(".bash"):
        return False
    if f_name == ".DS_Store":
        return False
    if f_name in (".dockerignore", ".flake8", ".python-version"):
        return False
    if os.path.islink(file_path) and not os.path.exists(file_path):
        return False
    if d_name and d_name.startswith("."):
        return False
    if d_name and d_name == "__pycache__":
        return False
    if d_name and os.path.basename(d_name).startswith("."):
        return False
    if d_name and os.path.basename(d_name) == "logs":
        return False
    if f_name.endswith(".ipynb"):
        return False
    if f_name.endswith(".zip"):
        return False
    if f_name.endswith(".tar.gz"):
        return False
    if f_name.endswith(".log"):
        return False
    if f_name == "code":
        return False
    if is_ignored(norm_path, ignored_patterns):
        return False
    if is_ignored(f_name, ignored_patterns):
        return False
    if f_name == "qupiato":
        return False

    return True


def iter_pack_candidates():
    exclude_dirs = get_exclude_dirs()
    ignored_patterns = load_qignore()

    for root, dirs, files in os.walk(".", followlinks=True):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            file_path = os.path.join(root, file)
            if _is_pack_included(file_path, ignored_patterns):
                yield file_path


def calc_pack_size_bytes():
    total = 0
    for file_path in iter_pack_candidates():
        try:
            total += os.path.getsize(file_path)
        except OSError:
            pass
    return total


def human_bytes(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f}{unit}" if unit != "B" else f"{n}B"
        n /= 1024
    return f"{n:.1f}PB"


def upload_using_api(zip_filename):
    url = f"{c.API_SERVER_URL}/deployments/upload"
    headers = {"Authorization": f"Bearer {get_token()}"}
    files = {"file": (zip_filename, open(zip_filename, "rb"))}
    response = requests.post(url, headers=headers, files=files)

    if response.status_code != 200 and response.status_code != 201:
        raise Exception("Failed to upload zip file")

    return os.path.basename(zip_filename)


def create_and_upload_to_gcs_bucket():
    with tempfile.TemporaryDirectory() as temp_dir:
        zipfile_name = os.path.join(temp_dir, f'{str(uuid.uuid4()).replace("-", "")}.zip')

        # 압축 이전 디렉터리(포장 대상) 용량 계산
        size_bytes = calc_pack_size_bytes()
        if size_bytes > 30 * 1024 * 1024:  # 30MB
            raise Exception("Directory size is too large. Please reduce the size of the directory. (max 30MB)")

        create_zip_archive(zipfile_name)
        object_key = upload_using_api(zipfile_name)
        print(f"done. {object_key}")
        return object_key


def get_version():
    version = importlib.metadata.version("pyqqq-cli")
    return version


def search_strategies(params=""):
    url = f"{c.API_SERVER_URL}/strategy/publish"
    headers = {"Authorization": f"Bearer {get_token()}"}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        if response.status_code == 404:
            return None
        else:
            code, message = response.json().values()
            raise Exception(f"Failed to search strategies {message}")

    return response.json()


def pull_strategy(name, uid, strategy_name, filename):
    url = f"{c.API_SERVER_URL}/deployments/download"
    headers = {"Authorization": f"Bearer {get_token()}"}
    response = requests.get(
        url,
        headers=headers,
        params={
            "uid": uid,
            "name": strategy_name,
            "file": filename,
        },
        stream=True,
    )

    if response.status_code != 200:
        raise Exception("Failed to search strategies")

    with io.BytesIO() as buffer:
        for chunk in response.iter_content(None):
            buffer.write(chunk)

        with zipfile.ZipFile(buffer) as zipf:
            zipf.extractall(name)


def list_my_strategies(params=""):
    url = f"{c.API_SERVER_URL}/strategy/publish/mine"
    headers = {"Authorization": f"Bearer {get_token()}"}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        if response.status_code == 404:
            return None
        else:
            code, message = response.json().values()
            raise Exception(f"Failed to search strategies {message}")

    return response.json()


def delete_my_strategy(deployment_id):
    url = f"{c.API_SERVER_URL}/strategy/publish/mine/{deployment_id}"
    headers = {"Authorization": f"Bearer {get_token()}"}
    response = requests.delete(url, headers=headers)

    if response.status_code >= 400:
        msg = response.json().get("message", "Failed to delete strategy")
        raise Exception(msg)


# 전략의 공개 설정
def publish_strategy(entryfile, strategy_name, zipfile):
    # 마크다운 처리
    entry_dir = os.path.dirname(os.path.normpath(entryfile))
    markdown = None
    for root, _, files in os.walk(entry_dir or "."):
        if markdown is not None:
            break

        for file in files:
            file_path = os.path.join(root, file)
            norm_path = os.path.normpath(file_path)
            d_name = os.path.dirname(norm_path)

            if entry_dir == d_name and re.match("readme.md", os.path.basename(norm_path), re.I):
                markdown = norm_path
                break

    if markdown:
        with open(markdown, "rb") as f:
            file_content = f.read()
        files = {"file": (os.path.basename(markdown), file_content, "application/octet-stream")}
    else:
        files = None

    # 환경변수 처리
    env_classes, env_vars = export_env(entryfile)

    # executor 종류 처리 (hook, default)
    executor = export_executor(entryfile)

    # NOTE
    # variables - dict로 전달하면 서버에서 제대로 파싱되지 않아 문자열로 전달
    url = f"{c.API_SERVER_URL}/strategy/publish"
    headers = {"Authorization": f"Bearer {get_token()}"}
    payload = {
        "entryfile": entryfile,
        "strategy": strategy_name,
        "zipfile": zipfile,
        "environments": env_classes,
        "variables": json.dumps(dict(env_vars)),
        "executor": executor,
    }

    response = requests.post(url, headers=headers, data=payload, files=files)
    if response.status_code != 200 and response.status_code != 201:
        raise Exception(f"Publishing failed with status code {response.status_code}")

    return response.json()


# 사용자 정보 조회
def get_user(uid):
    url = f"{c.API_SERVER_URL}/users/{uid}"
    headers = {"Authorization": f"Bearer {get_token()}"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception("Failed to search strategies")

    return response.json()


# websocket 메시지에 추가될 agent 정보
def get_agent():
    operating_system = {
        "Linux": "linux",
        "Darwin": "mac",
        "Windows": "win",
    }
    os = operating_system.get(platform.system(), "unknown")
    version = get_version()

    return {"name": "command_line", "os": os, "version": version}


def get_token():
    if c.PYQQQ_API_KEY:
        return c.PYQQQ_API_KEY

    elif os.path.exists(c.CREDENTIAL_FILE_PATH):
        with open(c.CREDENTIAL_FILE_PATH, "r") as f:
            return f.read().strip()

    else:
        print("ERROR: Key not found.")
        print("")
        print("Please set PYQQQ_API_KEY environment variable or create a file at ~/.qred with the API key.")
        sys.exit(1)


class StrategyAnalyzer(ast.NodeVisitor):
    """전략 코드에서 환경변수와 환경 클래스 사용을 분석하는 visitor"""

    BackStrategy_Env_Classes = {"KISDomesticEnvironment", "KISOverseasEnvironment", "EBestDomesticEnvironment", "BacktestEnvironment"}

    def __init__(self):
        self.env_vars = set()
        self.used_classes = set()

    def _extract_constant(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        return None

    def _add_env_var(self, key, value):
        is_exists = next((item for item in self.env_vars if item[0] == key), None)

        if is_exists is None:
            self.env_vars.add((key, value))
        else:
            if value is not None:
                self.env_vars.remove(is_exists)
                self.env_vars.add((key, value))

    def visit_Call(self, node):
        # os.environ.get("VAR")
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Attribute) and node.func.value.attr == "environ" and isinstance(node.func.value.value, ast.Name) and node.func.value.value.id == "os":
            if node.args:
                value = self._extract_constant(node.args[0])
                if value:
                    self._add_env_var(value, None)

        # os.getenv("VAR", "DEFAULT")
        elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "os" and node.func.attr == "getenv":
            if node.args:
                is_added = False
                value = self._extract_constant(node.args[0])

                # 기본값 추출
                if len(node.args) > 1:
                    default_value = self._extract_constant(node.args[1])
                    self._add_env_var(value, default_value)
                    is_added = True

                if not is_added:
                    self._add_env_var(value, None)

        # 환경 클래스 인스턴스 생성
        elif isinstance(node.func, ast.Name) and node.func.id in self.BackStrategy_Env_Classes:
            self.used_classes.add(node.func.id)

        self.generic_visit(node)

    def visit_Subscript(self, node):
        if isinstance(node.value, ast.Attribute) and node.value.attr == "environ" and isinstance(node.value.value, ast.Name) and node.value.value.id == "os":
            value = self._extract_constant(node.slice)
            if value:
                self._add_env_var(value, None)

        self.generic_visit(node)

    def visit_Name(self, node):
        if node.id in self.BackStrategy_Env_Classes:
            self.used_classes.add(node.id)
        self.generic_visit(node)


def export_env(filepath):
    """
    전략 코드를 분석하여 사용하고 있는 환경변수와 환경 클래스를 추출

    Return:
        - 사용하고 있는 환경 클래스: ['EBestDomesticEnvironment', 'KISDomesticEnvironment']
        - 사용하고 있는 환경변수: [('BUY_AMOUNT_PER_STOCK', None), ('BUY_WEIGHT', 0.5)]
    """
    visited_files = set()
    total_env_vars = set()
    total_used_classes = set()
    base_dir = None
    original_sys_path = None

    def set_base_dir(filepath):
        """파일의 디렉터리를 base_dir로 설정하고 sys.path에 추가"""
        nonlocal base_dir, original_sys_path
        dir_path = os.path.dirname(os.path.abspath(filepath))
        if base_dir is None:
            base_dir = dir_path
            original_sys_path = sys.path.copy()
            sys.path.insert(0, base_dir)  # importlib에서 찾을 수 있도록 추가

    def restore_sys_path():
        """sys.path를 원래 상태로 복원"""
        if original_sys_path is not None:
            sys.path[:] = original_sys_path

    def _find_module_path(module_name):
        """모듈의 경로를 찾는 헬퍼 함수"""
        if not base_dir:
            return None

        try:
            spec = importlib.util.find_spec(module_name)
            if spec and spec.origin:
                return spec.origin
        except ModuleNotFoundError:
            pass

        # 1. 디렉토리 기반 모듈: common/message.py
        dir_module_path = os.path.join(base_dir, *module_name.split(".")) + ".py"
        if os.path.isfile(dir_module_path):
            return dir_module_path

        # 2. 단일 파일 모듈: common.py
        top_level_path = os.path.join(base_dir, module_name.split(".")[0] + ".py")
        if os.path.isfile(top_level_path):
            return top_level_path

        return None

    def is_local_module(module_name):
        if not base_dir:
            return False

        # 표준 라이브러리 필터링
        if module_name in sys.stdlib_module_names:
            return False

        module_path = _find_module_path(module_name)
        if module_path and "site-packages" not in module_path:
            return True

        return False

    def get_module_path(module_name):
        return _find_module_path(module_name)

    def parse(filepath):
        """파일을 분석하고 import된 로컬 모듈도 재귀 분석"""
        filepath = os.path.abspath(filepath)
        if filepath in visited_files or not os.path.exists(filepath):
            return

        set_base_dir(filepath)
        visited_files.add(filepath)

        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source, filename=filepath)
        analyzer = StrategyAnalyzer()
        analyzer.visit(tree)

        total_env_vars.update(analyzer.env_vars)
        total_used_classes.update(analyzer.used_classes)

        # import된 로컬 모듈 분석
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name.split(".")[0]
                    if is_local_module(mod):
                        path = get_module_path(mod)
                        if path:
                            parse(path)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    mod = node.module
                    if is_local_module(mod):
                        path = get_module_path(mod)
                        if path:
                            parse(path)

    try:
        parse(filepath)
        return sorted(total_used_classes), sorted(total_env_vars)
    finally:
        restore_sys_path()


def export_executor(entryfile):
    """
    entryfile의 디렉토리에서 app.yaml 파일을 찾고 executor 타입을 확인합니다.

    Args:
        entryfile (str): 분석할 파일의 경로

    Returns:
        str: "hook" 또는 "default"
    """
    # 홈 디렉토리 경로를 확장하고 절대 경로로 변환
    entryfile = os.path.expanduser(entryfile)
    entry_dir = os.path.dirname(os.path.abspath(entryfile))
    app_yaml_path = os.path.join(entry_dir, "app.yaml")

    # app.yaml 파일이 존재하는지 확인
    if not os.path.exists(app_yaml_path):
        return "default"

    # yaml 파일을 읽고 분석
    with open(app_yaml_path, "r") as f:
        try:
            config = yaml.safe_load(f)
            # executor가 "hook"인지 확인
            if config.get("executor") == "hook":
                return "hook"
        except yaml.YAMLError:
            return "default"

    return "default"
