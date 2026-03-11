from __future__ import annotations

import ast
from pathlib import Path


class _AgentModuleView:
    def __init__(self, source: str) -> None:
        self.source = source
        self.module = ast.parse(source)

    def import_names_from(self, module_name: str) -> set[str]:
        return {
            alias.name
            for node in self.module.body
            if isinstance(node, ast.ImportFrom) and node.module == module_name
            for alias in node.names
        }

    def function_def(self, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
        for node in self.module.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
                return node
        raise AssertionError(f"Expected function {name!r} in src/agent.py")


def _load_agent_module() -> _AgentModuleView:
    source = Path("src/agent.py").read_text(encoding="utf-8")
    return _AgentModuleView(source)


def test_agent_entrypoint_builds_hvac_runtime_agent_from_validated_config() -> None:
    view = _load_agent_module()

    assert "HVACConversationController" in view.import_names_from(
        "conversation.conversation_controller"
    )
    assert "load_config" in view.import_names_from("config.load_config")

    build_runtime_agent = view.function_def("build_runtime_agent")

    load_config_calls = [
        node
        for node in ast.walk(build_runtime_agent)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "load_config"
    ]
    assert load_config_calls, "Expected build_runtime_agent() to call load_config()"

    controller_calls = [
        node
        for node in ast.walk(build_runtime_agent)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "HVACConversationController"
    ]
    assert controller_calls, "Expected build_runtime_agent() to construct HVACConversationController"
    assert any(
        any(keyword.arg == "config" for keyword in call.keywords) for call in controller_calls
    ), "Expected build_runtime_agent() to pass validated config into HVACConversationController"


def test_agent_entrypoint_starts_session_with_runtime_agent_factory_not_template_assistant() -> None:
    view = _load_agent_module()

    start_calls = [
        node
        for node in ast.walk(view.module)
        if isinstance(node, ast.Await)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and node.value.func.attr == "start"
    ]
    assert start_calls, "Expected an awaited session.start(...) call in src/agent.py"

    assert any(
        any(
            keyword.arg == "agent"
            and isinstance(keyword.value, ast.Call)
            and isinstance(keyword.value.func, ast.Name)
            and keyword.value.func.id == "build_runtime_agent"
            for keyword in start_call.value.keywords
        )
        for start_call in start_calls
    ), "Expected session.start(agent=build_runtime_agent(), ...) wiring in src/agent.py"

    assert "Assistant(" not in view.source
    assert "helpful voice AI assistant" not in view.source
