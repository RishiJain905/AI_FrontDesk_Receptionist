from __future__ import annotations

from pathlib import Path
import re
import tomllib


REPO_ROOT = Path(__file__).resolve().parents[1]
README_PATH = REPO_ROOT / "README.md"
ENV_EXAMPLE_PATH = REPO_ROOT / ".env.example"
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"

REQUIRED_ENV_KEYS: tuple[str, ...] = (
    "LIVEKIT_URL",
    "LIVEKIT_API_KEY",
    "LIVEKIT_API_SECRET",
    "GHL_API_TOKEN",
    "GHL_LOCATION_ID",
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "TWILIO_FROM_NUMBER",
)


def _read_required_text(path: Path) -> str:
    assert path.exists(), f"Expected readiness artifact at {path.relative_to(REPO_ROOT)}"
    return path.read_text(encoding="utf-8")


def _parse_env_file(path: Path) -> dict[str, str]:
    env_map: dict[str, str] = {}
    for raw_line in _read_required_text(path).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        env_map[key.strip()] = value.strip().strip('"').strip("'")

    return env_map


def _looks_like_placeholder(value: str) -> bool:
    lowered = value.lower()
    placeholder_markers = (
        "example",
        "placeholder",
        "your_",
        "your-",
        "replace",
        "changeme",
        "sample",
        "demo",
        "<",
        ">",
        "xxxx",
        "***",
    )
    return any(marker in lowered for marker in placeholder_markers) or "555" in value


def test_readiness_artifacts_exist() -> None:
    for path in (README_PATH, ENV_EXAMPLE_PATH, PYPROJECT_PATH):
        assert path.exists(), f"Missing readiness artifact: {path.relative_to(REPO_ROOT)}"


def test_readme_has_setup_and_environment_sections() -> None:
    readme = _read_required_text(README_PATH)
    lowered = readme.lower()

    assert "setup" in lowered, "README.md must include setup instructions"
    assert "environment" in lowered, "README.md must include environment variable instructions"


def test_readme_has_console_and_dev_run_instructions() -> None:
    readme = _read_required_text(README_PATH)
    lowered = readme.lower()

    assert "src/agent.py" in readme, "README.md must reference src/agent.py run instructions"
    assert "console" in lowered, "README.md must describe console mode run steps"
    assert "dev" in lowered, "README.md must describe dev-mode run steps"


def test_readme_has_verification_commands() -> None:
    readme = _read_required_text(README_PATH)

    required_commands = (
        "uv run pytest",
        "uv run ruff check src/",
        "uv run ruff format --check src/",
    )

    for command in required_commands:
        assert command in readme, f"README.md must include verification command: {command}"


def test_readme_has_demo_script_for_normal_safety_and_partial_paths() -> None:
    readme = _read_required_text(README_PATH)
    lowered = readme.lower()

    assert "demo" in lowered, "README.md must include a demo script section"
    assert "normal" in lowered, "README demo script must include normal-call path"
    assert "safety" in lowered, "README demo script must include safety-escalation path"
    assert "partial" in lowered, "README demo script must include partial-call path"


def test_env_example_contains_required_provider_keys() -> None:
    env_map = _parse_env_file(ENV_EXAMPLE_PATH)

    missing = [key for key in REQUIRED_ENV_KEYS if key not in env_map]
    assert not missing, f".env.example missing required keys: {', '.join(missing)}"


def test_env_example_values_are_placeholders_not_live_secrets() -> None:
    env_map = _parse_env_file(ENV_EXAMPLE_PATH)

    for key in REQUIRED_ENV_KEYS:
        assert key in env_map, f"Expected key in .env.example: {key}"
        value = env_map[key]
        assert value, f".env.example value for {key} cannot be empty"
        assert value.lower() not in {"none", "null"}, (
            f".env.example value for {key} must be a placeholder, not null-like"
        )
        assert _looks_like_placeholder(value), (
            f".env.example value for {key} must look like a safe placeholder, got: {value!r}"
        )


def test_pyproject_has_core_project_metadata() -> None:
    content = _read_required_text(PYPROJECT_PATH).encode("utf-8")
    data = tomllib.loads(content.decode("utf-8"))

    project = data.get("project")
    assert isinstance(project, dict), "pyproject.toml must define [project]"

    for required_key in ("name", "version", "description", "requires-python"):
        assert project.get(required_key), f"[project] must define {required_key!r}"

    requires_python = str(project["requires-python"])
    assert re.search(r">=\s*3\.12", requires_python), (
        "[project].requires-python must support CI Python 3.12"
    )


def test_pyproject_declares_runtime_dependencies() -> None:
    data = tomllib.loads(_read_required_text(PYPROJECT_PATH))
    project = data.get("project", {})
    dependencies = project.get("dependencies", [])

    assert isinstance(dependencies, list) and dependencies, (
        "[project].dependencies must exist with runtime packages"
    )

    expected_runtime_packages = ("livekit-agents", "httpx", "python-dotenv")
    normalized = [str(dep).lower() for dep in dependencies]

    for package in expected_runtime_packages:
        assert any(dep.startswith(package) for dep in normalized), (
            f"[project].dependencies must include {package}"
        )


def test_pyproject_includes_pytest_and_ruff_configuration() -> None:
    data = tomllib.loads(_read_required_text(PYPROJECT_PATH))

    tool = data.get("tool")
    assert isinstance(tool, dict), "pyproject.toml must define [tool] configuration"

    pytest_config = tool.get("pytest", {}).get("ini_options")
    assert isinstance(pytest_config, dict), "pyproject.toml must define [tool.pytest.ini_options]"

    has_testpaths = isinstance(pytest_config.get("testpaths"), list) and bool(
        pytest_config.get("testpaths")
    )
    has_addopts = bool(pytest_config.get("addopts"))
    assert has_testpaths or has_addopts, (
        "[tool.pytest.ini_options] must define testpaths or addopts"
    )

    ruff_config = tool.get("ruff")
    assert isinstance(ruff_config, dict), "pyproject.toml must define [tool.ruff]"

    dependency_groups = data.get("dependency-groups", {})
    optional_dev = data.get("project", {}).get("optional-dependencies", {}).get("dev", [])
    dev_dependencies = [str(dep).lower() for dep in dependency_groups.get("dev", []) + optional_dev]

    assert any(dep.startswith("pytest") for dep in dev_dependencies), (
        "Dev dependencies must include pytest"
    )
    assert any(dep.startswith("ruff") for dep in dev_dependencies), (
        "Dev dependencies must include ruff"
    )
