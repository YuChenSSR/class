# Contributing to CLASS

Thanks for your interest in contributing! This project is a hybrid
**Rust + Python** codebase: the Python package `dqcmap` is accelerated by a
PyO3 extension (`dqcmap._accelerate`) built from the Rust workspace under
`rust/`.

## Development setup

1. Install [Rust](https://www.rust-lang.org/learn/get-started). The pinned
   toolchain is declared in `rust-toolchain.toml`.
2. Create a Python 3.11 environment (`venv`, conda, or
   [uv](https://docs.astral.sh/uv/)).
3. Clone with submodules — the benchmark QASM files used by the test suite
   live in git submodules:

   ```shell
   git clone --recurse-submodules <repo-url>
   cd class
   git submodule update --init   # if you cloned without --recurse-submodules
   ```

4. Build and install in editable mode (this compiles the Rust extension):

   ```shell
   uv sync --all-extras          # preferred (uses uv.lock)
   # or
   pip install -e ".[dev]"
   ```

## Running the tests

Both test suites should pass before you open a pull request. They also run in
CI (see `.github/workflows/test.yml`).

- **Python**:

  ```shell
  pytest tests/
  ```

  Note: several tests read QASM files from `benchmarks/`, so the submodules
  must be checked out (see above).

- **Rust**: the `pyext` crate links `libpython` for standalone test builds, so
  the dynamic linker must be able to find it (see `rust/README.md`):

  ```shell
  export LD_LIBRARY_PATH="$(python -c 'import sys; print(sys.base_prefix)')/lib:$LD_LIBRARY_PATH"
  cargo test --no-default-features
  ```

## Code style and pre-commit hooks

Formatting and linting are enforced with pre-commit (Ruff + isort for Python,
`cargo fmt` + `cargo check` for Rust) and commit messages are checked with
commitlint.

```shell
pip install pre-commit
pre-commit install
# run against everything before committing:
pre-commit run --all-files
```

Commit messages follow the [Conventional Commits](https://www.conventionalcommits.org/)
format (e.g. `fix: ...`, `docs: ...`, `feat: ...`).
