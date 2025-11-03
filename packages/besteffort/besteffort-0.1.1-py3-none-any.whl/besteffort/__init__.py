"""Public entry point for the :mod:`besteffort` importer.

Importing :mod:`besteffort` installs the meta path finder that rewrites a
module's abstract syntax tree so that every statement executes inside a
``contextlib.suppress`` block, allowing functions to keep running even when
exceptions occur. ``from besteffort import yourmodule`` triggers the install
automatically because the package is imported before resolving attributes.
"""

from __future__ import annotations

from . import core as _core

install = _core.install
besteffort = _core.besteffort


install()

__all__ = ["install", "besteffort"]

del _core
