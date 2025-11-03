from __future__ import annotations

import ast
import functools
import importlib.abc
import importlib.machinery
import importlib.util
import inspect
import io
import os
import sys
import textwrap
from types import ModuleType
from typing import Any, Callable, Optional, TypeVar, Union

_PREFIX = "besteffort."
_SUPPRESS_ALIAS = "__besteffort_suppress__"

_FuncNode = Union[ast.FunctionDef, ast.AsyncFunctionDef]
_CallableT = TypeVar("_CallableT", bound=Callable[..., Any])


class _BestEffortTransformer(ast.NodeTransformer):
    def visit_Module(self, node: ast.Module) -> ast.Module:
        self.generic_visit(node)
        import_node = ast.ImportFrom(
            module="contextlib",
            names=[ast.alias(name="suppress", asname=_SUPPRESS_ALIAS)],
            level=0,
        )
        ast.fix_missing_locations(import_node)
        insert_at = 0
        if node.body and isinstance(node.body[0], ast.Expr):
            v = node.body[0].value
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                insert_at = 1
        while insert_at < len(node.body):
            stmt = node.body[insert_at]
            if isinstance(stmt, ast.ImportFrom) and stmt.module == "__future__":
                insert_at += 1
            else:
                break
        node.body.insert(insert_at, import_node)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        self.generic_visit(node)
        node.body = self._guard_block(node.body)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        self.generic_visit(node)
        node.body = self._guard_block(node.body)
        return node

    def visit_If(self, node: ast.If) -> ast.If:
        self.generic_visit(node)
        node.body = self._guard_block(node.body)
        node.orelse = self._guard_block(node.orelse)
        return node

    def visit_For(self, node: ast.For) -> ast.For:
        self.generic_visit(node)
        node.body = self._guard_block(node.body)
        node.orelse = self._guard_block(node.orelse)
        return node

    def visit_AsyncFor(self, node: ast.AsyncFor) -> ast.AsyncFor:
        self.generic_visit(node)
        node.body = self._guard_block(node.body)
        node.orelse = self._guard_block(node.orelse)
        return node

    def visit_While(self, node: ast.While) -> ast.While:
        self.generic_visit(node)
        node.body = self._guard_block(node.body)
        node.orelse = self._guard_block(node.orelse)
        return node

    def visit_With(self, node: ast.With) -> ast.With:
        self.generic_visit(node)
        node.body = self._guard_block(node.body)
        return node

    def visit_AsyncWith(self, node: ast.AsyncWith) -> ast.AsyncWith:
        self.generic_visit(node)
        node.body = self._guard_block(node.body)
        return node

    def visit_Try(self, node: ast.Try) -> ast.Try:
        self.generic_visit(node)
        node.body = self._guard_block(node.body)
        node.orelse = self._guard_block(node.orelse)
        node.finalbody = self._guard_block(node.finalbody)
        for h in node.handlers:
            h.body = self._guard_block(h.body)
        return node

    if hasattr(ast, "TryStar"):

        def visit_TryStar(self, node: ast.TryStar) -> ast.TryStar:  # Python 3.11+
            self.generic_visit(node)
            node.body = self._guard_block(node.body)
            node.orelse = self._guard_block(node.orelse)
            node.finalbody = self._guard_block(node.finalbody)
            for h in node.handlers:
                h.body = self._guard_block(h.body)
            return node

    def visit_Match(self, node: ast.Match) -> ast.Match:  # Python 3.10+
        self.generic_visit(node)
        for c in node.cases:
            c.body = self._guard_block(c.body)
        return node

    @staticmethod
    def _guard_block(stmts):
        return [_BestEffortTransformer._wrap(stmt) for stmt in stmts]

    @staticmethod
    def _wrap(stmt: ast.stmt) -> ast.stmt:
        withitem = ast.withitem(
            context_expr=ast.Call(
                func=ast.Name(id=_SUPPRESS_ALIAS, ctx=ast.Load()),
                args=[ast.Name(id="Exception", ctx=ast.Load())],
                keywords=[],
            ),
            optional_vars=None,
        )
        wrapped = ast.With(items=[withitem], body=[stmt], type_comment=None)
        wrapped = ast.copy_location(wrapped, stmt)
        ast.fix_missing_locations(wrapped)
        return wrapped


def _instrument_source(source: str, filename: str = "<string>"):
    tree = ast.parse(source, filename=filename, mode="exec")
    tree = _BestEffortTransformer().visit(tree)
    ast.fix_missing_locations(tree)
    return compile(tree, filename=filename, mode="exec")


class _BestEffortLoader(importlib.abc.Loader):
    def __init__(self, fullname: str, target_name: str, orig_spec: importlib.machinery.ModuleSpec):
        self.fullname = fullname
        self.target_name = target_name
        self.orig_spec = orig_spec

    def create_module(self, spec):
        return None

    def exec_module(self, module: ModuleType) -> None:
        spec = self.orig_spec
        source = None

        loader = spec.loader
        if hasattr(loader, "get_source"):
            try:
                source = loader.get_source(spec.name)  # type: ignore[attr-defined]
            except Exception:
                source = None

        if source is None and spec.origin and spec.origin.endswith(".py") and os.path.exists(spec.origin):
            with open(spec.origin, "r", encoding="utf-8") as f:
                source = f.read()

        if source is None:
            if hasattr(loader, "exec_module"):
                loader.exec_module(module)  # type: ignore[attr-defined]
                module.__dict__.setdefault("__besteffort_unmodified__", True)
                module.__dict__.setdefault("__original_name__", self.target_name)
                return
            raise ImportError(f"besteffort: cannot instrument non-source module '{self.target_name}'")

        code = _instrument_source(source, filename=spec.origin or self.target_name)

        original_package = self.target_name.rpartition(".")[0]
        module.__dict__.update(
            {
                "__file__": spec.origin,
                "__loader__": self,
                "__package__": original_package,
                "__besteffort__": True,
                "__original_name__": self.target_name,
            }
        )

        if spec.submodule_search_locations is not None:
            module.__path__ = spec.submodule_search_locations  # type: ignore[attr-defined]

        exec(code, module.__dict__)


class _BestEffortFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname: str, path=None, target=None):
        if not fullname.startswith(_PREFIX) or fullname == _PREFIX[:-1]:
            return None

        target_name = fullname[len(_PREFIX):]
        if not target_name:
            return None

        try:
            orig_spec = importlib.util.find_spec(target_name)
        except (ImportError, ValueError):
            orig_spec = None

        if orig_spec is None:
            return None

        loader = _BestEffortLoader(fullname, target_name, orig_spec)
        is_pkg = orig_spec.submodule_search_locations is not None
        spec = importlib.machinery.ModuleSpec(fullname, loader, is_package=is_pkg)
        spec.origin = orig_spec.origin
        spec.has_location = orig_spec.has_location
        if is_pkg:
            spec.submodule_search_locations = orig_spec.submodule_search_locations
        return spec


def install() -> None:
    for f in sys.meta_path:
        if isinstance(f, _BestEffortFinder):
            return
    sys.meta_path.insert(0, _BestEffortFinder())


def _strip_besteffort_decorators(func_node: _FuncNode) -> None:
    func_node.decorator_list = [
        d
        for d in func_node.decorator_list
        if not (
            isinstance(d, ast.Name) and d.id == "besteffort"
            or (
                isinstance(d, ast.Attribute)
                and isinstance(d.value, ast.Name)
                and d.value.id == "besteffort"
                and d.attr == "besteffort"
            )
        )
    ]


def _find_target_function(tree: ast.Module, name: str) -> Optional[_FuncNode]:
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def besteffort(func: _CallableT) -> _CallableT:
    """Return a best-effort version of *func*.

    The returned function executes each statement inside ``contextlib.suppress``
    so that individual failures do not abort the overall call. The decorator is
    intended to be used as the innermost decorator on the target function.
    """

    if not callable(func):
        raise TypeError("@besteffort can only be applied to callables")

    try:
        source_lines, _ = inspect.getsourcelines(func)
    except (OSError, TypeError) as exc:  # pragma: no cover - defensive guard
        raise TypeError("besteffort decorator requires Python source to be available") from exc

    source = textwrap.dedent("".join(source_lines))
    filename = inspect.getsourcefile(func) or inspect.getfile(func)

    tree = ast.parse(source, filename=filename)
    func_node = _find_target_function(tree, func.__name__)
    if func_node is None:
        raise ValueError(f"Could not locate function definition for {func.__name__!r}")

    _strip_besteffort_decorators(func_node)
    tree = _BestEffortTransformer().visit(tree)
    ast.fix_missing_locations(tree)

    globals_dict = func.__globals__
    original_binding = globals_dict.get(func.__name__)

    code = compile(tree, filename=filename, mode="exec")
    exec(code, globals_dict)

    new_func = globals_dict.get(func.__name__)
    if not callable(new_func):  # pragma: no cover - defensive guard
        raise RuntimeError("besteffort: failed to recompile function")

    if original_binding is not None:
        globals_dict[func.__name__] = original_binding

    functools.update_wrapper(new_func, func)  # type: ignore[arg-type]
    return new_func  # type: ignore[return-value]
