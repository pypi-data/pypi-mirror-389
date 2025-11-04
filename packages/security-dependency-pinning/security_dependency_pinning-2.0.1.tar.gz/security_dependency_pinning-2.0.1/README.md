# security_dependency_pinning

<!-- Badges -->
[![CI](https://github.com/bitranox/security_dependency_pinning/actions/workflows/ci.yml/badge.svg)](https://github.com/bitranox/security_dependency_pinning/actions/workflows/ci.yml)
[![CodeQL](https://github.com/bitranox/security_dependency_pinning/actions/workflows/codeql.yml/badge.svg)](https://github.com/bitranox/security_dependency_pinning/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Open in Codespaces](https://img.shields.io/badge/Codespaces-Open-blue?logo=github&logoColor=white&style=flat-square)](https://codespaces.new/bitranox/security_dependency_pinning?quickstart=1)
[![PyPI](https://img.shields.io/pypi/v/security_dependency_pinning.svg)](https://pypi.org/project/security_dependency_pinning/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/security_dependency_pinning.svg)](https://pypi.org/project/security_dependency_pinning/)
[![Code Style: Ruff](https://img.shields.io/badge/Code%20Style-Ruff-46A3FF?logo=ruff&labelColor=000)](https://docs.astral.sh/ruff/)
[![codecov](https://codecov.io/gh/bitranox/security_dependency_pinning/graph/badge.svg?token=UFBaUDIgRk)](https://codecov.io/gh/bitranox/security_dependency_pinning)
[![Maintainability](https://qlty.sh/badges/041ba2c1-37d6-40bb-85a0-ec5a8a0aca0c/maintainability.svg)](https://qlty.sh/gh/bitranox/projects/security_dependency_pinning)
[![Known Vulnerabilities](https://snyk.io/test/github/bitranox/security_dependency_pinning/badge.svg)](https://snyk.io/test/github/bitranox/security_dependency_pinning)

A repository dedicated to maintaining a secure, stable environment by pinning critical library versions to protect against vulnerabilities and ensure compatibility.
- CLI entry point styled with rich-click (rich output + click ergonomics)
- Exit-code and messaging helpers powered by lib_cli_exit_tools

Purpose
-------
The repository is specifically designed to:

- **Ensure a Secure Environment**: By pinning specific versions of critical libraries, the repository helps in safeguarding against potential security threats by avoiding the use of versions known to have vulnerabilities.

- **Maintain Stability**: Stability in the software environment is ensured by using tested and proven versions of libraries, reducing the risk of crashes or errors due to incompatible library updates.

- **Prevent Compatibility Issues**: Compatibility among various libraries and dependencies is crucial for the smooth operation of software projects. Pinning versions help in avoiding conflicts that might arise from updates in dependencies.

- **Protect Against Vulnerabilities**: The focus on pinning critical libraries is also to protect the software from vulnerabilities that could be exploited if newer, untested versions of the libraries are used.

Key Considerations
------------------
- The practice of pinning should be applied judiciously, focusing on libraries that are critical for security and operational stability.

- Regular review of pinned versions is necessary to ensure that updates addressing security vulnerabilities are incorporated in a timely manner, without compromising the stability of the software environment.

- Coordination among team members is essential to manage the pinned versions effectively and to ensure that all aspects of the software's dependencies are considered.

Conclusion
----------
Security dependency pinning is a foundational practice in maintaining the integrity, security, and reliability of software projects. By adhering to this practice, developers can significantly reduce the risk of introducing security vulnerabilities and compatibility issues into their projects.

Pinning
----------

by including this repo as dependency, following libraries will be pinned :  
 - certifi>=2024.2.2
 - pygments>=2.7.4,
 - requests[security]>=2.32.4
 - urllib3>=2.5.0
 - uwsgi>=2.0.21 ; sys_platform != 'win32'
 - zipp>=3.19.1


----

## Install - recommended via UV
UV - the ultrafast installer - written in Rust (10–20× faster than pip/poetry)

```bash
# recommended Install via uv 
pip install --upgrade uv
# Create and activate a virtual environment (optional but recommended)
uv venv
# macOS/Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# install via uv from PyPI
uv pip install security_dependency_pinning
```

For alternative install paths (pip, pipx, uv, uvx source builds, etc.), see
[INSTALL.md](INSTALL.md). All supported methods register both the
`security_dependency_pinning` and `bitranox-template-py-cli` commands on your PATH.



## Usage

The CLI leverages [rich-click](https://github.com/ewels/rich-click) so help output, validation errors, and prompts render with Rich styling while keeping the familiar click ergonomics.
The scaffold keeps a CLI entry point so you can validate packaging flows, but it
currently exposes a single informational command while logging features are
developed:

```bash
security_dependency_pinning info
security_dependency_pinning hello
security_dependency_pinning fail
security_dependency_pinning --traceback fail
bitranox-template-py-cli info
python -m security_dependency_pinning info
uvx security_dependency_pinning info
```

For library use you can import the documented helpers directly:

```python
import security_dependency_pinning as btpc

btpc.emit_greeting()
try:
    btpc.raise_intentional_failure()
except RuntimeError as exc:
    print(f"caught expected failure: {exc}")

btpc.print_info()
```


## Further Documentation

- [Install Guide](INSTALL.md)
- [Development Handbook](DEVELOPMENT.md)
- [Contributor Guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- [Module Reference](docs/systemdesign/module_reference.md)
- [License](LICENSE)
