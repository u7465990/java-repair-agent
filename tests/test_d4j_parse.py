from java_agent.d4j import parse_failing_tests

SAMPLE = """Running ant (compile.tests)...
Running ant (test)
   [junit] Testsuite: org.apache.commons.lang3.math.NumberUtilsTest
Failing tests: 2
	- org.apache.commons.lang3.math.NumberUtilsTest::testCreateNumber
	- org.apache.commons.lang3.StringUtilsTest::testIsEmpty

BUILD FAILED
"""


def test_parses_failing_block() -> None:
    failing = parse_failing_tests(SAMPLE)
    assert failing == {
        "org.apache.commons.lang3.math.NumberUtilsTest::testCreateNumber",
        "org.apache.commons.lang3.StringUtilsTest::testIsEmpty",
    }


def test_zero_failures_yields_empty_set() -> None:
    assert parse_failing_tests("Failing tests: 0" + chr(10)) == set()


def test_output_without_block_is_empty() -> None:
    assert parse_failing_tests("BUILD SUCCESSFUL") == set()
