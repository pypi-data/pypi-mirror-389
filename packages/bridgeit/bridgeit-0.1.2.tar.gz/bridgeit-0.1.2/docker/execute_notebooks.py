"""
Execute the BridgeIt integration notebooks with nbclient.

Usage:
    python -m docker.execute_notebooks [--notebook NOTEBOOK ...]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NOTEBOOKS: list[Path] = [
    REPO_ROOT / "docker" / "notebooks" / "rust_integration.ipynb",
    REPO_ROOT / "docker" / "notebooks" / "mojo_integration.ipynb",
]

# Expected outputs to validate notebook execution
EXPECTED_OUTPUTS = {
    "rust_integration.ipynb": [
        "Hello from Rust 🦀",
        "42",
    ],
    "mojo_integration.ipynb": [
        "Hello from Mojo 🔥",
        "30",
    ],
}


def validate_notebook_outputs(nb: nbformat.NotebookNode, notebook_name: str) -> None:
    """Validate that expected outputs are present in the executed notebook."""
    expected = EXPECTED_OUTPUTS.get(notebook_name, [])
    if not expected:
        return

    # Collect all outputs from all cells
    all_outputs = []
    for cell in nb.cells:
        if cell.cell_type == "code" and hasattr(cell, "outputs"):
            for output in cell.outputs:
                if hasattr(output, "text"):
                    all_outputs.append(output.text)
                elif hasattr(output, "data") and "text/plain" in output.data:
                    all_outputs.append(output.data["text/plain"])

    combined_output = "\n".join(all_outputs)

    # Check each expected output is present
    missing = []
    for expected_text in expected:
        if expected_text not in combined_output:
            missing.append(expected_text)

    if missing:
        raise AssertionError(
            f"Missing expected outputs in {notebook_name}:\n"
            + "\n".join(f"  - {text!r}" for text in missing)
        )

    print(f"✓ All expected outputs found in {notebook_name}")


def execute_notebook(path: Path, output_dir: Path | None = None) -> None:
    """Execute a notebook in-place and optionally persist the executed copy."""
    nb = nbformat.read(path, as_version=4)
    client = NotebookClient(nb, timeout=600, kernel_name="python3", allow_errors=False)
    client.execute()

    # Validate outputs
    validate_notebook_outputs(nb, path.name)

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / path.name
        nbformat.write(nb, output_path)
        print(f"Wrote executed notebook to {output_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute BridgeIt integration notebooks.")
    parser.add_argument(
        "--notebook",
        dest="notebooks",
        action="append",
        help="Relative path to a notebook to execute. Defaults to the curated set.",
    )
    parser.add_argument(
        "--store-executed",
        dest="store_dir",
        type=Path,
        default=REPO_ROOT / "docker" / "notebooks" / "executed",
        help=(
            "Directory where executed notebooks should be written "
            "(default: docker/notebooks/executed)."
        ),
    )
    args = parser.parse_args(argv)

    notebooks: list[Path]
    if args.notebooks:
        notebooks = [REPO_ROOT / nb_path for nb_path in args.notebooks]
    else:
        notebooks = DEFAULT_NOTEBOOKS

    for notebook_path in notebooks:
        if not notebook_path.exists():
            raise FileNotFoundError(f"Notebook {notebook_path} not found.")

        print(f"Executing {notebook_path.relative_to(REPO_ROOT)} ...")
        try:
            execute_notebook(notebook_path, output_dir=args.store_dir)
        except CellExecutionError as exc:  # pragma: no cover - surfaced to caller
            print(f"Notebook execution failed: {exc}", file=sys.stderr)
            return 1
        except AssertionError as exc:  # pragma: no cover - validation failure
            print(f"Notebook validation failed: {exc}", file=sys.stderr)
            return 1

    print(f"\n✓ All {len(notebooks)} notebook(s) executed and validated successfully!")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
