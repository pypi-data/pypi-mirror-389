<div align="center">
  <img src="docs/images/wandler.svg" alt="Wandler Logo" width="1024" height="180">
  <p>
    <strong>A simple, fast, Python-native task runner that uses a <code>wandler.yaml</code> file.</strong>
  </p>
  <p>
    Think <code>make</code>, but for Python projects—with clean YAML syntax and powerful validation.
  </p>
  <p>
    <a href="https://pypi.org/project/wandler/"><img src="https://img.shields.io/pypi/v/wandler.svg?color=blue" alt="PyPI version"></a>
    <a href="https://github.com/rosshhun/wandler/actions/workflows/ci.yml"><img src="https://github.com/rosshhun/wandler/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
    <a href="https://github.com/rosshhun/wandler/blob/main/LICENSE"><img src="https://img.shields.io/pypi/l/wandler.svg" alt="License"></a>
    <a href="https://img.shields.io/pypi/pyversions/wandler"><img src="https://img.shields.io/pypi/pyversions/wandler.svg" alt="Python versions"></a>
  </p>
</div>

---

## 💡 Why Wandler?

We have `make`, `invoke`, and `Task`. Why build another task runner?

Wandler is built on a simple philosophy: **Your project's task runner should be as simple and reliable as the project's code.**

* **🐍 Python-Native:** Stop installing external Go binaries or fighting with `Makefile`s on Windows. Wandler is a pure Python tool. Install it with `pip` and add it to your `pyproject.toml` dev dependencies.
* **✅ Validated:** Powered by **Pydantic**. Stop guessing why your config is broken. Get clear, human-readable error messages for free if you have a typo in your `wandler.yaml`.
* **🧼 Clean & Simple:** No complex syntax, no tab-vs-space wars. Just a clean, human-readable YAML file that maps task names to shell commands.
* **✨ Lightweight:** Wandler is *not* a complex build system. It's a simple, fast runner for the 90% use case: running your linters, tests, and formatters.

## 🚀 Getting Started in 60 Seconds

1.  **Install Wandler:**

    ```sh
    pip install wandler
    ```

2.  **Create a `wandler.yaml` in your project root:**

    ```yaml
    tasks:
      clean:
        description: "Remove all build artifacts and cache files."
        command: "rm -rf .pytest_cache .mypy_cache build/ dist/ site/"

      build_docs:
        description: "Build the documentation site."
        command: "mkdocs build"
        inputs:
          - "docs/**/*.md"
          - "mkdocs.yml"
        outputs:
          - "site/index.html"

      serve_docs:
        description: "Serve the docs site with live-reloading."
        command: "mkdocs serve"

      build_package:
        description: "Build the wheel and sdist for publishing."
        command: "python -m build"
        depends_on:
          - clean
    ```

3.  **List your tasks:**

    ```sh
    $ wandler list

    Available tasks:
    clean                - Remove all build artifacts and cache files.
    build_docs           - Build the documentation site.
    serve_docs           - Serve the docs site with live-reloading.
    build_package        - Build the wheel and sdist for publishing.
    ```

4.  **Run a task:** (Wandler automatically runs dependencies first)

    ```sh
    $ wandler run build_package

    Running task 'clean': rm -rf .pytest_cache .mypy_cache build/ dist/ site/
    Task 'clean' completed successfully.
    Running task 'build_package': python -m build
    Task 'build_package' completed successfully.
    ```