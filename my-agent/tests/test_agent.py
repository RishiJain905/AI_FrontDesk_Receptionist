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


def test_agent_entrypoint_loads_both_env_files_explicitly() -> None:
    view = _load_agent_module()

    dotenv_paths: set[str] = set()
    for node in ast.walk(view.module):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "load_dotenv"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            dotenv_paths.add(node.args[0].value)

    assert ".env.local" in dotenv_paths
    assert ".env" in dotenv_paths


def test_agent_entrypoint_composes_after_hours_gate_lifecycle_and_initial_greeting() -> None:
    view = _load_agent_module()
    my_agent = view.function_def("my_agent")

    assert "is_after_hours" in view.import_names_from("orchestration.after_hours_gate")
    assert "CallLifecycle" in view.import_names_from("orchestration.call_lifecycle")

    gate_calls = [
        node
        for node in ast.walk(my_agent)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "is_after_hours"
    ]
    assert gate_calls, "Expected my_agent() to evaluate after-hours gate before runtime flow continues"

    lifecycle_calls = [
        node
        for node in ast.walk(my_agent)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "CallLifecycle"
    ]
    assert lifecycle_calls, "Expected my_agent() to construct CallLifecycle"

    lifecycle_var_names: set[str] = set()
    for node in ast.walk(my_agent):
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "CallLifecycle"
        ):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    lifecycle_var_names.add(target.id)

    subscription_calls = [
        node
        for node in ast.walk(my_agent)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"attach", "subscribe", "bind"}
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id in lifecycle_var_names
    ]

    lifecycle_has_session_kw = any(
        any(keyword.arg == "session" for keyword in call.keywords) for call in lifecycle_calls
    )
    assert (
        subscription_calls or lifecycle_has_session_kw
    ), "Expected lifecycle to subscribe to AgentSession events"

    start_awaits = [
        node
        for node in ast.walk(my_agent)
        if isinstance(node, ast.Await)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and node.value.func.attr == "start"
    ]
    generate_reply_awaits = [
        node
        for node in ast.walk(my_agent)
        if isinstance(node, ast.Await)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and node.value.func.attr == "generate_reply"
    ]

    assert start_awaits, "Expected awaited session.start(...) in my_agent()"
    assert generate_reply_awaits, "Expected awaited session.generate_reply(...) in my_agent()"

    assert min(await_node.lineno for await_node in generate_reply_awaits) > min(
        await_node.lineno for await_node in start_awaits
    ), "Expected initial greeting generation after session.start(...)"
