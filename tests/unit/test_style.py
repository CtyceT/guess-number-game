"""Style guard: every function and method needs a docstring and type hints."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = (ROOT / "src", ROOT / "tests")
_IMPLICIT_PARAMS = {"self", "cls"}


def _python_files() -> list[Path]:
    """Lists every Python source file under src/ and tests/.

    Returns:
        Sorted paths of all ``.py`` files to check.
    """
    files: list[Path] = []
    for directory in SCAN_DIRS:
        files.extend(directory.rglob("*.py"))
    return sorted(files)


def _violations(path: Path) -> list[str]:
    """Finds functions in a file that lack a docstring or type hints.

    Args:
        path: The Python file to inspect.

    Returns:
        Human-readable descriptions of each violation found.
    """
    problems: list[str] = []
    relative = path.relative_to(ROOT)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        where = f"{relative}:{node.lineno} {node.name}"
        if ast.get_docstring(node) is None:
            problems.append(f"{where}: missing docstring")
        if node.returns is None:
            problems.append(f"{where}: missing return annotation")
        args = node.args
        every_arg = [*args.posonlyargs, *args.args, *args.kwonlyargs]
        if args.vararg is not None:
            every_arg.append(args.vararg)
        if args.kwarg is not None:
            every_arg.append(args.kwarg)
        for arg in every_arg:
            if arg.arg not in _IMPLICIT_PARAMS and arg.annotation is None:
                problems.append(f"{where}: parameter {arg.arg} not annotated")
    return problems


def test_all_functions_have_docstrings_and_type_hints() -> None:
    """Every function in src/ and tests/ is documented and annotated."""
    problems: list[str] = []
    for path in _python_files():
        problems.extend(_violations(path))
    assert not problems, "\n".join(problems)
