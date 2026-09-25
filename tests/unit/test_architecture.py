"""Architecture guard: the logic layer must stay free of I/O and the CLI."""

import ast
from pathlib import Path

ENGINE_PATH = (
    Path(__file__).resolve().parents[2] / "src" / "guessing_game" / "engine.py"
)


def _parse_engine() -> ast.Module:
    """Parses engine.py into an AST.

    Returns:
        The parsed module.
    """
    return ast.parse(ENGINE_PATH.read_text(encoding="utf-8"))


def _imported_names(tree: ast.Module) -> list[str]:
    """Collects every module or name imported anywhere in the tree.

    Args:
        tree: The parsed module.

    Returns:
        Dotted module names plus imported member names, e.g. both
        ``guessing_game.cli`` and ``cli`` for ``from guessing_game import cli``.
    """
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.append(node.module)
            names.extend(alias.name for alias in node.names)
    return names


def test_engine_does_not_call_input_or_print() -> None:
    """engine.py contains no call to input() or print()."""
    banned = {"input", "print"}
    for node in ast.walk(_parse_engine()):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned, (
                f"engine.py calls {node.func.id}() at line {node.lineno}"
            )


def test_engine_does_not_import_cli() -> None:
    """engine.py never imports the cli module in any form."""
    for name in _imported_names(_parse_engine()):
        parts = name.split(".")
        assert "cli" not in parts, f"engine.py imports {name}"


def test_engine_does_not_import_logging() -> None:
    """engine.py never imports logging; logging belongs to the CLI layer."""
    for name in _imported_names(_parse_engine()):
        assert name.split(".")[0] != "logging", f"engine.py imports {name}"
