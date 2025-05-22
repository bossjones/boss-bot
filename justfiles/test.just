# run test tasks
[group('test')]
test: test-ci

# test ci
[group('test')]
test-ci:
	uv run pytest --diff-width=60 --diff-symbols --cov-append --cov-report=term-missing --cov-report=xml:cov.xml --cov-report=html:htmlcov --junitxml=junit/test-results.xml --cov=.
	uv run pre-commit run -a --show-diff-on-failure
