# Best practices


### Unit-tests
Unit-tests in [tests](../tests/) are part of the [pre-commit](#pre-commit-hooks) routine. To execute them manually run `make unit_tests`.

### makefile
[Make](../Makefile) commands are used to simplify project setup and execution.

### pylint black isort
These format and style checkers are also part of the [pre-commit](#pre-commit-hooks) routine. To execute them manually run `make format_check`.

### Integration test

### pre-commit-hooks
Pre-Commit allows to run hooks on every commit automatically to point out issues such as missing semicolons, trailing whitespaces, etc.

1. Install pre-commit as described in the [installation](https://pre-commit.com/) section
2. Pre-Commit configuration file is already configured in `.pre-commit-config.yaml`
3. Execute pre-commit manually by `make pre_commit` or allow it to run automatically at every attemp to `git commit` by installing the tool **once** (`pre-commit install`). Note that this will not allow to commit code until all issues are resolved.

### CI\CD
To be implemented using Git Actions
