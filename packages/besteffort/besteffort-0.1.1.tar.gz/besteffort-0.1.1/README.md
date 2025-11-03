# python-besteffort

`python-besteffort` installs a custom importer that rewrites Python source on
the fly so that every statement executes inside a
``contextlib.suppress(Exception)`` block. When an unexpected exception is
raised, execution simply skips the failing statement and keeps going—perfect
for exploratory data analysis, flaky integrations, or anywhere failure should
not immediately abort a workflow.

## Features

* **Auto-installing importer** – importing :mod:`besteffort` registers the
  meta-path finder so ``from besteffort import yourmodule`` works without any
  additional steps. Call :func:`besteffort.install` manually if you need to
  reinstall it.
* **Function decorator** – use ``@besteffort`` to protect just the functions
  you care about without rewriting entire modules.
* **Preserves module semantics** – relative imports and globals are kept in
  sync with the original module, ensuring wrapped code still behaves like the
  unmodified version whenever no exceptions occur.

## Installation

Install the package from PyPI:

```bash
pip install besteffort
```

Alternatively, install straight from the repository when testing a development
build:

```bash
pip install git+https://github.com/grantjenks/python-besteffort.git
```

## Python compatibility

`python-besteffort` supports CPython 3.10 and newer. The test suite runs on
Python 3.10 through 3.13 and automatically exercises syntax introduced in later
releases (such as structural pattern matching and exception groups) when the
interpreter supports it, while skipping those checks on earlier versions.

## Quick start

### Import best-effort modules

```python
import besteffort  # registers the meta-path finder on import

# ``yourmodule`` is an example module shipped with the project. Importing it
# through ``besteffort`` returns a wrapped version where each statement is
# guarded by ``contextlib.suppress(Exception)``.
from besteffort import yourmodule

yourmodule.example("G")
```

The wrapped module behaves as if ``with suppress(Exception):`` surrounded each
statement. Lines that raise simply fail closed and execution continues. Even a
bare ``from besteffort import yourmodule`` works because Python imports the
package before looking up ``yourmodule``.

### Decorate individual functions

```python
from besteffort import besteffort


@besteffort
def fragile(value: int) -> int:
    print("before divide")
    value /= 0
    print("after divide")
    return value


fragile(10)
```

Only the decorated function is rewritten, allowing the rest of the module to
run normally. Use ``@besteffort`` as the innermost decorator when stacking it
with others.

## Testing

Run the unit test suite locally before contributing:

```bash
pytest
# or, to use our automation profile
nox -s tests
```

## Limitations

* Only rewrites Python source (``.py``). Built-ins and C extensions cannot be
  transformed.
* Top-level module code is not wrapped; if a module raises at import time,
  importing via ``besteffort`` will still fail.
* Relative imports from the instrumented module work by setting
  ``__package__`` to the original package; absolute imports inside the module
  load the normal (unmodified) dependencies.

## Contributing

If you have an issue, give it to Codex. If it's too complex for Codex then :shrug:
Only pull requests opened by Codex will be accepted.