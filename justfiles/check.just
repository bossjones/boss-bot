# run check tasks
[group('check')]
check: check-code check-type check-format check-security check-coverage

# check code quality
[group('check')]
check-code:
	uv run ruff check src tests

# check code coverage
[group('check')]
check-coverage cov_fail_under="30":
	uv run pytest --cov=. --cov-fail-under={{cov_fail_under}} tests

# check code format
[group('check')]
check-format:
	uv run ruff format --check {{SOURCES}} {{TESTS}}

# check code security
[group('check')]
check-security:
	uv run bandit --recursive --configfile=pyproject.toml {{SOURCES}}

#uv run pytest {{TESTS}}

# check unit tests
[group('check')]
check-test TESTS="tests":
	uv run pytest {{TESTS}}

# check code typing
[group('check')]
check-type-mpy:
	uv run mypy --config-file=pyproject.toml --html-report typingcov --cobertura-xml-report typingcov_cobertura --xml-report typingcov_xml --txt-report typingcov_txt .
	open typingcov/index.html

# # check code typing
# [group('check')]
# check-type path="src":
# 	uv run pyright {{path}}

# check code typing
[group('check')]
check-type path="src/boss_bot":
	uv run pylint --output-format=colorized --disable=all --max-line-length=120 --enable=F,E --rcfile pyproject.toml {{path}}
