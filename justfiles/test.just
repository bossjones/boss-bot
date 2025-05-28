# run test tasks
[group('test')]
test: test-ci

# test ci
[group('test')]
test-ci:
	uv run pytest --diff-width=60 --diff-symbols --cov-append --cov-branch --cov-report=term-missing --cov-report=xml:cov.xml --cov-report=html:htmlcov --junitxml=junit/test-results.xml --cov=.

ci: test-ci

# fix via pre-commit
[group('test')]
test-fix:
	uv run pre-commit run -a --show-diff-on-failure

fix: test-fix

# lint via pre-commit
[group('test')]
lint: test-fix

# run tests with VCR recording
[group('test')]
test-vcr:
	uv run pytest --record-mode=once --verbose --showlocals --tb=short --cov-append --cov-report=term-missing --junitxml=junit/test-results.xml --cov-report=xml:cov.xml --cov-report=html:htmlcov --cov-report=annotate:cov_annotate --cov=.

# update VCR cassettes - rewrite all recorded network interactions
[group('test')]
update-vcr-tests:
	uv run pytest --record-mode=rewrite --verbose --showlocals --tb=short --cov-append --cov-report=term-missing --junitxml=junit/test-results.xml --cov-report=xml:cov.xml --cov-report=html:htmlcov --cov-report=annotate:cov_annotate --cov=.

# update all VCR cassettes in the test suite
[group('test')]
update-vcr-all:
	uv run pytest --record-mode=rewrite tests/

# run VCR tests without network (use existing cassettes only)
[group('test')]
test-vcr-offline:
	uv run pytest --record-mode=none --verbose --showlocals --tb=short --cov-append --cov-report=term-missing --junitxml=junit/test-results.xml --cov-report=xml:cov.xml --cov-report=html:htmlcov --cov-report=annotate:cov_annotate --cov=.

# clean VCR cassettes (remove all recorded network interactions)
[group('test')]
clean-vcr-cassettes:
	rm -rf tests/cassettes/*.yml tests/cassettes/*.yaml

# delete existing cassettes using script
[group('test')]
delete-existing-cassettes:
	./scripts/delete-existing-cassettes.sh

# force delete existing cassettes (non-interactive)
[group('test')]
force-delete-cassettes:
	FORCE_DELETE_CASSETTES=1 ./scripts/delete-existing-cassettes.sh

# dry run cassette deletion (show what would be deleted)
[group('test')]
dry-run-delete-cassettes:
	DRY_RUN_REGENERATE_CASSETTES=1 FORCE_DELETE_CASSETTES=1 ./scripts/delete-existing-cassettes.sh

# record VCR tests with all mode (for initial recording)
[group('test')]
uv-unittests-vcr-record-final:
	uv run pytest --record-mode=all --verbose --showlocals --tb=short --cov-append --cov-report=term-missing --junitxml=junit/test-results.xml --cov-report=xml:cov.xml --cov-report=html:htmlcov --cov-report=annotate:cov_annotate --cov=.

# delete all cassette files and directories, regenerate all cassette files and rerun tests
[group('test')]
local-regenerate-cassettes:
	@echo -e "\nDelete all cassette files and directories\n"
	just delete-existing-cassettes
	@echo -e "\nRegenerate all cassette files using --record-mode=all\n"
	@echo -e "\nNOTE: This is expected to FAIL the first time when it is recording the cassette files!\n"
	just uv-unittests-vcr-record-final || true
	@echo -e "\nRun regular tests to verify that the cassettes are working\n"
	just test-vcr

# (alias) delete all cassette files and directories, regenerate all cassette files and rerun tests
[group('test')]
local-regenerate-vcr: local-regenerate-cassettes

fix-vcr: local-regenerate-vcr
