import atexit
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from queue import Empty
from typing import Any

from IPython import get_ipython  # type: ignore[attr-defined]

try:
    from jupyter_client import KernelManager  # type: ignore[attr-defined]
    from jupyter_client.kernelspec import KernelSpecManager

    _KernelManager: type[KernelManager] | None = KernelManager
    _KernelSpecManager: type[KernelSpecManager] | None = KernelSpecManager
except ImportError:  # pragma: no cover - optional dependency
    _KernelManager = None
    _KernelSpecManager = None


@dataclass
class LanguageConfig:
    """Configuration describing how to bridge a language into IPython."""

    magic_name: str
    kernelspec_name: str
    fallback_command: Sequence[str] | None = None
    fallback_env: Iterable[tuple[str, str]] | None = None
    fallback_via_file: bool = False
    fallback_file_arg: str = "{file}"
    fallback_file_suffix: str = ".tmp"
    install_commands: Sequence[Sequence[str]] = field(default_factory=tuple)


LANGUAGE_CONFIGS: dict[str, LanguageConfig] = {
    "rust": LanguageConfig(
        magic_name="rust",
        kernelspec_name="rust",
        fallback_command=("evcxr",),
        install_commands=(("python", "-m", "bridgeit.installers", "rust"),),
    ),
    "mojo": LanguageConfig(
        magic_name="mojo",
        kernelspec_name="mojo",
        fallback_command=("mojo", "run", "{file}"),
        fallback_env=(("MODULAR_SKIP_CRASHPAD", "1"), ("MODULAR_CRASHPAD_DISABLE", "1")),
        fallback_via_file=True,
        fallback_file_suffix=".mojo",
        install_commands=(("python", "-m", "bridgeit.installers", "mojo"),),
    ),
}


def _ensure_ipython() -> Any:
    ip = get_ipython()  # type: ignore[no-untyped-call]
    if ip is None:
        raise RuntimeError("No active IPython shell; cannot register magics.")
    return ip


def _ensure_kernel_manager() -> type[KernelManager]:
    if _KernelManager is None:
        raise RuntimeError("jupyter_client is required for kernel orchestration; install it first.")
    return _KernelManager


def _ensure_kernelspec_manager() -> KernelSpecManager:
    if _KernelSpecManager is None:
        raise RuntimeError(
            "jupyter_client is required for kernelspec management; install it first."
        )
    return _KernelSpecManager()


def available_languages() -> list[str]:
    """Return the language keys bundled with this bridge."""
    return sorted(LANGUAGE_CONFIGS)


def help() -> None:
    """Print available commands and languages."""
    print("BridgeIt - Bridge multiple languages into SolveIt!")
    print()
    print("Available commands:")
    print("  bridgeit.help()                  - Show this help message")
    print("  bridgeit.langs()                 - List available languages")
    print("  bridgeit.install(lang)           - Install kernelspec for a language")
    print("  bridgeit.install(lang, force=True) - Force reinstall even if already installed")
    print("  bridgeit.use(lang)               - Enable cell magic for a language")
    print()
    print("Available languages:")
    for lang in available_languages():
        print(f"  - {lang}")
    print()
    print("Example usage:")
    print("  import bridgeit")
    print("  bridgeit.install('rust')")
    print("  bridgeit.use('rust')")
    print("  # Then use %%rust in cells")
    print()
    print("  # Force reinstall:")
    print("  bridgeit.install('rust', force=True)")


def langs() -> list[str]:
    """List available languages with friendly output."""
    available = available_languages()
    print("Available languages:")
    for lang in available:
        print(f"  - {lang}")
    return available


def install(
    language: str, *, force: bool = False, dry_run: bool = False, step: int | None = None
) -> str:
    """
    Install kernelspec for a language.

    Args:
        language: Language name (e.g., "rust", "mojo")
        force: Force reinstallation even if already installed
        dry_run: Show installation steps without running them
        step: Optional step number to run a specific step only (e.g., 1, 2, 3)

    Returns:
        Path to the installed kernelspec directory (empty string for dry_run)
    """
    language_key = language.lower()
    config = LANGUAGE_CONFIGS.get(language_key)
    if config is None:
        raise ValueError(f"Unknown language {language!r}. Known: {available_languages()}")

    # Handle dry_run
    if dry_run:
        from . import installers

        print(f"\n{language.title()} Installation Steps:")
        print("=" * 50)
        if language_key == "rust":
            steps = installers.get_rust_steps()
        elif language_key == "mojo":
            steps = installers.get_mojo_steps()
        else:
            print(f"No step information available for {language}")
            return ""

        for i, step_desc in enumerate(steps, 1):
            print(f"  Step {i}/{len(steps)}: {step_desc}")
        print("\nUsage:")
        print(f"  bridgeit.install('{language}')              # Run all steps")
        print(f"  bridgeit.install('{language}', step=N)      # Run specific step")
        print(f"  bridgeit.install('{language}', force=True)  # Force reinstall")
        return ""

    manager = _ensure_kernelspec_manager()

    # Check if already installed (skip if forcing or running specific step)
    if not force and step is None:
        try:
            spec = manager.get_kernel_spec(config.kernelspec_name)
            resource_dir: str = spec.resource_dir
            print(f"✓ {language.title()} kernelspec already installed at {resource_dir}")
            return resource_dir
        except KeyError:
            pass

    if step is not None:
        print(f"Running {language.title()} installation step {step}...")
    elif force:
        print(f"Force reinstalling {language.title()} kernelspec...")
    else:
        print(f"Installing {language.title()} kernelspec...")

    commands = config.install_commands
    if not commands:
        raise RuntimeError(
            f"No install instructions for language {language!r}. "
            "Provide `kernelspec_dir` or `install_commands`."
        )

    # Build command with step parameter if provided
    for i, command in enumerate(commands, 1):
        cmd_list = list(command)
        if step is not None:
            cmd_list.extend(["--step", str(step)])

        print(f"  [{i}/{len(commands)}] Running: {' '.join(cmd_list)}")
        proc = subprocess.run(
            tuple(cmd_list),
            text=True,
            check=False,
        )
        if proc.returncode:
            raise RuntimeError(
                f"Install command {tuple(cmd_list)!r} failed with status {proc.returncode}"
            )

    # Skip verification if running specific step (not complete installation)
    if step is not None:
        print(f"✓ {language.title()} step {step} complete")
        return ""

    try:
        spec = manager.get_kernel_spec(config.kernelspec_name)
        installed_dir: str = spec.resource_dir
        print(f"✓ {language.title()} kernelspec installed at {installed_dir}")
        return installed_dir
    except KeyError as exc:  # pragma: no cover - defensive
        raise RuntimeError(
            f"Failed to locate kernelspec {config.kernelspec_name!r} after installation."
        ) from exc


def use(language: str) -> None:
    """
    Enable cell magic for a language.

    Raises RuntimeError if the kernelspec is not installed.

    Args:
        language: Language name (e.g., "rust", "mojo")
    """
    language_key = language.lower()
    config = LANGUAGE_CONFIGS.get(language_key)
    if config is None:
        raise ValueError(f"Unknown language {language!r}. Known: {available_languages()}")

    manager = _ensure_kernelspec_manager()
    try:
        manager.get_kernel_spec(config.kernelspec_name)
    except KeyError:
        raise RuntimeError(
            f"Kernelspec for {language!r} not installed. Run: bridgeit.install('{language}')"
        ) from None

    # Register the magic
    magic = config.magic_name
    kernel = config.kernelspec_name
    handler = make_kernelspec_runner(
        kernel_name=kernel,
        startup_timeout=30.0,
    )
    register_magic(magic_name=magic, handler=handler)
    print(f"{language.title()} enabled. Add %%{magic} to your cells to use it.")


def make_kernelspec_runner(
    *,
    kernel_name: str = "rust",
    startup_timeout: float = 30.0,
) -> Callable[[str], None]:
    """
    Build a BridgeIt handler that executes cells through a Jupyter kernelspec.

    The returned callable keeps the kernel alive across invocations, printing
    stdout/stderr to the current notebook. Requires ``jupyter_client`` and a
    matching kernelspec to be installed.
    """
    km_cls = _ensure_kernel_manager()
    km = km_cls(kernel_name=kernel_name)
    km.start_kernel(stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    kc = km.client()
    kc.start_channels()
    kc.wait_for_ready(timeout=startup_timeout)

    def _cleanup() -> None:
        try:
            kc.stop_channels()
        finally:
            km.shutdown_kernel(now=True)

    atexit.register(_cleanup)

    def _run(cell: str) -> None:
        msg_id = kc.execute(cell, store_history=False)
        errors: list[str] = []
        while True:
            try:
                msg = kc.get_iopub_msg(timeout=startup_timeout)
            except Empty as exc:
                raise TimeoutError(
                    f"No response from {kernel_name!r} kernel within {startup_timeout}s"
                ) from exc

            if msg["parent_header"].get("msg_id") != msg_id:
                continue

            msg_type = msg["header"]["msg_type"]
            content = msg["content"]

            if msg_type == "status" and content.get("execution_state") == "idle":
                break
            if msg_type == "stream":
                text = content.get("text", "")
                print(text, end="" if text.endswith("\n") else "\n")
            elif msg_type in {"execute_result", "display_data"}:
                data = content.get("data", {})
                text = data.get("text/plain")
                if text:
                    print(text)
            elif msg_type == "error":
                traceback = "\n".join(content.get("traceback", []))
                if traceback:
                    print(
                        traceback,
                        file=sys.stderr,
                        end="" if traceback.endswith("\n") else "\n",
                    )
                    errors.append(traceback)
                else:
                    err_text = f"{content.get('ename')}: {content.get('evalue')}"
                    print(err_text, file=sys.stderr)
                    errors.append(err_text)

        reply = kc.get_shell_msg(timeout=startup_timeout)
        if reply["content"].get("status") != "ok" and not errors:
            err_text = f"{kernel_name!r} kernel execution failed: {reply}"
            print(err_text, file=sys.stderr)

    return _run


def list_installed_kernels() -> dict[str, str]:
    """
    Return a mapping of kernelspec names to display names.

    Requires ``jupyter_client``; otherwise raises ``RuntimeError``.
    """
    manager = _ensure_kernelspec_manager()
    return {
        name: spec["spec"].get("display_name", name)
        for name, spec in manager.get_all_specs().items()
    }


def install_kernel_spec_from_dir(
    source_dir: str,
    *,
    kernel_name: str | None = None,
    user: bool = True,
    replace: bool = False,
) -> str:
    """
    Install a kernelspec from ``source_dir`` using the Jupyter KernelSpecManager.

    Returns the destination path of the installed kernelspec. The caller is
    responsible for ensuring that ``source_dir`` contains a valid ``kernel.json``.
    """
    manager = _ensure_kernelspec_manager()

    # If replacing, manually remove symlinks first (shutil.rmtree can't handle them)
    if replace and kernel_name:
        kernel_dir = Path(manager.kernel_dirs[0] if user else manager.kernel_dirs[-1])
        dest = kernel_dir / kernel_name
        if dest.exists() or dest.is_symlink():
            if dest.is_symlink():
                dest.unlink()
            elif dest.is_dir():
                shutil.rmtree(dest)

    result: str = manager.install_kernel_spec(
        source_dir,
        kernel_name=kernel_name,
        user=user,
        replace=replace,
    )
    return result


def register_magic(
    magic_name: str,
    *,
    handler: Callable[[str], object] | None = None,
) -> None:
    """
    Register a cell magic for use in Jupyter notebooks.

    The handler will be invoked with the cell contents as a string.
    """
    ip = _ensure_ipython()

    if handler is None:
        handler = ip.user_ns.get("r")
        if handler is None:
            raise RuntimeError("No handler supplied and `r` not found in namespace.")

    def cell_magic(line: str, cell: str | None = None) -> object:
        payload = cell if cell is not None else line
        return handler(payload)

    ip.register_magic_function(
        cell_magic,
        magic_kind="cell",
        magic_name=magic_name,
    )


def register_rust_magic(
    magic_name: str = "rust",
    *,
    handler: Callable[[str], object] | None = None,
    startup_timeout: float = 30.0,
) -> None:
    """
    Register Rust magic for Jupyter notebooks.
    """
    if handler is None:
        handler = make_kernelspec_runner(
            kernel_name="rust",
            startup_timeout=startup_timeout,
        )

    register_magic(magic_name=magic_name, handler=handler)
