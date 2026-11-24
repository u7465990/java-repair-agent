from java_agent.audit import audit_workspace
from java_agent.sandbox.base import ExecResult


class AuditSandbox:
    def __init__(self, status: str, numstat: str) -> None:
        self.status = status
        self.numstat = numstat

    def exec(self, args, cwd=None, timeout=600) -> ExecResult:
        command = " ".join(args)
        if "status" in command:
            return ExecResult(0, self.status, "")
        if "--numstat" in command:
            return ExecResult(0, self.numstat, "")
        return ExecResult(0, "", "")

    def close(self) -> None:
        return None


def test_clean_source_change_passes() -> None:
    sandbox = AuditSandbox(
        " M src/main/java/Foo.java\n",
        "10\t2\tsrc/main/java/Foo.java\n",
    )
    audit = audit_workspace(sandbox, "/workspace/repo")
    assert audit.ok
    assert audit.files == ["src/main/java/Foo.java"]
    assert audit.added == 10


def test_test_file_change_is_rejected() -> None:
    sandbox = AuditSandbox(
        " M src/test/java/FooTest.java\n",
        "3\t1\tsrc/test/java/FooTest.java\n",
    )
    audit = audit_workspace(sandbox, "/workspace/repo")
    assert not audit.ok
    assert any("forbidden path" in v for v in audit.violations)


def test_build_file_change_is_rejected() -> None:
    sandbox = AuditSandbox(" M pom.xml\n", "1\t0\tpom.xml\n")
    audit = audit_workspace(sandbox, "/workspace/repo")
    assert any("forbidden path" in v for v in audit.violations)


def test_untracked_file_outside_src_is_rejected() -> None:
    sandbox = AuditSandbox("?? notes.txt\n", "0\t0\tsrc/main/java/Foo.java\n")
    audit = audit_workspace(sandbox, "/workspace/repo")
    assert any("outside src/main" in v for v in audit.violations)


def test_build_output_is_ignored() -> None:
    sandbox = AuditSandbox(
        "?? target/classes/Foo.class\n M src/main/java/Foo.java\n",
        "2\t1\tsrc/main/java/Foo.java\n",
    )
    audit = audit_workspace(sandbox, "/workspace/repo")
    assert audit.ok


def test_defects4j_report_files_are_ignored() -> None:
    sandbox = AuditSandbox(
        "?? all_tests\n?? failing_tests\n M src/main/java/Foo.java\n",
        "4\t2\tsrc/main/java/Foo.java\n",
    )
    audit = audit_workspace(sandbox, "/workspace/repo")
    assert audit.ok


def test_empty_change_is_rejected() -> None:
    audit = audit_workspace(AuditSandbox("", ""), "/workspace/repo")
    assert any("no source changes" in v for v in audit.violations)


def test_large_diff_is_rejected() -> None:
    sandbox = AuditSandbox(
        " M src/main/java/Foo.java\n",
        "500\t20\tsrc/main/java/Foo.java\n",
    )
    audit = audit_workspace(sandbox, "/workspace/repo")
    assert any("too large" in v for v in audit.violations)
