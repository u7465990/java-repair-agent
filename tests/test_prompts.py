from java_agent.agent.prompts import next_action_hint
from java_agent.audit import DiffAudit
from java_agent.verify import VerifyReport


def _report(kind: str, **overrides) -> VerifyReport:
    values = {
        "ok": False,
        "compile_ok": True,
        "kind": kind,
    }
    values.update(overrides)
    return VerifyReport(**values)


def test_no_changes_demands_an_edit() -> None:
    hint = next_action_hint(_report("no_changes"))
    assert "MUST edit" in hint


def test_audit_violation_lists_paths() -> None:
    audit = DiffAudit(ok=False, violations=["forbidden path: src/test/Foo.java"])
    hint = next_action_hint(_report("audit_violation", audit=audit))
    assert "src/test/Foo.java" in hint


def test_compile_error_mentions_compile() -> None:
    assert "does not compile" in next_action_hint(_report("compile_error"))


def test_trigger_failing_names_the_test() -> None:
    hint = next_action_hint(
        _report(
            "trigger_failing",
            failing={"org.example.FooTest::bar"},
            trigger={"org.example.FooTest::bar"},
        )
    )
    assert "FooTest::bar" in hint


def test_new_failure_names_the_test() -> None:
    hint = next_action_hint(
        _report("new_failure", new_failures={"org.example.OtherTest::baz"})
    )
    assert "OtherTest::baz" in hint


def test_passed_has_no_hint() -> None:
    assert next_action_hint(_report("passed")) == ""
