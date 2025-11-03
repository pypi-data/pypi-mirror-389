MODE: STRICT_GENERATION
TASK: Produce one complete pytest file for a given Python module.

REQUIREMENTS:
- Output only valid Python code (no text, no markdown).
- Target: full behavioral + branch coverage (100%).
- Tests follow AAA pattern (# Arrange, # Act, # Assert).
- Exactly ONE assert or ONE pytest.raises() per test.
- Use tmp_path fixture for filesystem isolation.
- Include an autouse=True fixture for global patching if needed.
- No external I/O or network calls.
- All tests independent, self-contained.

STYLE:
- File starts with module docstring describing AAA, single assert rule, autouse fixture.
- Group tests with comment headers: 
  # --- Success paths --- / # --- Error paths --- / # --- Edge cases ---
- Function names: test_<function>_<expected_behavior>_<condition>
- Variables descriptive (rel, path, new_content, etc.).
- Use direct asserts (assert result is True, assert path.read_text() == "x").
- For errors: 
  with pytest.raises(ExceptionType, match=r"text"): function_call()

COVERAGE:
- Include success, failure, and rare edge branches (e.g., conditional exceptions).
- Ensure 100% of conditional branches executed.

OUTPUT:
- Single .py file, runnable via: pytest -v --disable-warnings --maxfail=1 --cov=<target_module>
- No explanations or prose, only the test code.

END
