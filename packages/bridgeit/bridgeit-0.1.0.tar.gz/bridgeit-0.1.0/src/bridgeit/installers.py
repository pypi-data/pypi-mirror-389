"""Language installers invoked by :func:`bridgeit.install`.

This module provides opt-in bootstrap routines for languages that require more
than a kernelspec copy. Each installer should be idempotent and safe to re-run.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
from collections.abc import Sequence
from pathlib import Path


def _run_with_progress(
    command: Sequence[str],
    *,
    cwd: str | Path | None = None,
    env: dict[str, str] | None = None,
    indent: str = "    ",
    interval: float = 2.5,
) -> tuple[str, str]:
    """Run ``command`` suppressing output while emitting a heartbeat."""

    cmd_tuple = tuple(command)
    proc = subprocess.Popen(  # noqa: PLW1510 - intentional manual management
        cmd_tuple,
        cwd=str(cwd) if isinstance(cwd, Path) else cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    done = threading.Event()
    printed = False

    def spinner() -> None:
        nonlocal printed
        while not done.wait(interval):
            if indent and not printed:
                sys.stdout.write(indent)
            sys.stdout.write(".")
            sys.stdout.flush()
            printed = True

    thread = threading.Thread(target=spinner, daemon=True)
    thread.start()

    stdout, stderr = proc.communicate()
    done.set()
    thread.join()

    if printed:
        sys.stdout.write("\n")
        sys.stdout.flush()

    if proc.returncode:
        if stdout:
            print(stdout, end="" if stdout.endswith("\n") else "\n")
        if stderr:
            print(
                stderr,
                file=sys.stderr,
                end="" if stderr.endswith("\n") else "\n",
            )
        raise RuntimeError(f"Command {cmd_tuple!r} failed with exit code {proc.returncode}")

    return stdout or "", stderr or ""


def _cargo_env() -> dict[str, str]:
    """Return an environment with Cargo binaries added to PATH."""
    home = Path.home()
    cargo_home = Path(os.environ.get("CARGO_HOME", home / ".cargo"))
    rustup_home = Path(os.environ.get("RUSTUP_HOME", home / ".rustup"))

    env = os.environ.copy()
    env.setdefault("CARGO_HOME", str(cargo_home))
    env.setdefault("RUSTUP_HOME", str(rustup_home))
    env["PATH"] = f"{cargo_home / 'bin'}:{env.get('PATH', '')}"
    return env


def _command_exists(cmd: str, env: dict[str, str]) -> bool:
    return shutil.which(cmd, path=env.get("PATH")) is not None


def install_rust() -> None:
    """Install Rust toolchain and evcxr_jupyter kernelspec."""
    print("  → Step 1/3: Checking Rust toolchain...", flush=True)
    env = _cargo_env()

    if not _command_exists("rustup", env):
        print("    Installing rustup (stable, minimal profile)...", flush=True)
        install_script = (
            "curl https://sh.rustup.rs -sSf | "
            "sh -s -- -y --profile minimal --default-toolchain stable"
        )
        _run_with_progress(["bash", "-lc", install_script], env=env, indent="      ")
        print("    ✓ Rustup installed", flush=True)
    else:
        print("    ✓ Rustup already installed", flush=True)

    if not _command_exists("cargo", env):
        raise RuntimeError("Cargo missing after rustup installation; aborting.")

    print(
        "  → Step 2/3: Installing evcxr_jupyter kernel (this may take a few minutes)...",
        flush=True,
    )
    print("    Running: cargo install evcxr_jupyter", flush=True)
    _run_with_progress(
        ["cargo", "install", "evcxr_jupyter", "--locked", "--force"],
        env=env,
        indent="      ",
    )

    print("    ✓ evcxr_jupyter installed", flush=True)

    print("  → Step 3/3: Registering Jupyter kernelspec...", flush=True)
    _run_with_progress(
        [
            "evcxr_jupyter",
            "--install",
        ],
        env=env,
        indent="      ",
    )
    print("    ✓ Kernelspec registered", flush=True)


def _pixi_env() -> dict[str, str]:
    env = os.environ.copy()
    pixi_bin = Path(env.get("PIX_BIN", Path.home() / ".pixi" / "bin"))
    env.setdefault("PIX_BIN", str(pixi_bin))
    env["PATH"] = f"{pixi_bin}:{env.get('PATH', '')}"
    env.setdefault("MODULAR_SKIP_CRASHPAD", "1")
    env.setdefault("MODULAR_CRASHPAD_DISABLE", "1")
    return env


def _ensure_pixi(env: dict[str, str]) -> None:
    if shutil.which("pixi", path=env.get("PATH")):
        return

    print("    Pixi not found; installing (this may take a moment)...", flush=True)
    _run_with_progress(
        ["bash", "-lc", "curl -fsSL https://pixi.sh/install.sh | bash"],
        env=env,
        indent="      ",
    )
    print("    ✓ Pixi installed", flush=True)
    if not shutil.which("pixi", path=env.get("PATH")):
        raise RuntimeError("Pixi installation failed; 'pixi' not found on PATH.")


def install_mojo(mojo_version: str = "0.25.6") -> None:
    """Install Mojo toolchain and kernelspec using pixi."""

    from . import magics

    print("  → Step 1/7: Setting up pixi environment...", flush=True)
    env = _pixi_env()
    _ensure_pixi(env)

    print("  → Step 2/7: Creating pixi project directory...", flush=True)
    project_dir = Path.home() / ".bridgeit" / "mojo-pixi"
    project_dir.mkdir(parents=True, exist_ok=True)
    print(f"    Using project directory: {project_dir}", flush=True)

    pixi_toml = project_dir / "pixi.toml"
    if not pixi_toml.exists():
        print("  → Step 3/7: Initializing pixi project...", flush=True)
        _run_with_progress(
            [
                "pixi",
                "init",
                str(project_dir),
                "-c",
                "https://conda.modular.com/max-nightly/",
                "-c",
                "conda-forge",
            ],
            env=env,
            indent="      ",
        )
        print("    ✓ Project initialized", flush=True)
    else:
        print("  → Step 3/7: Pixi project already initialized", flush=True)

    print(f"  → Step 4/7: Adding mojo=={mojo_version} to environment...", flush=True)
    _run_with_progress(
        ["pixi", "add", f"mojo=={mojo_version}"],
        cwd=project_dir,
        env=env,
        indent="      ",
    )
    print("    ✓ Mojo package added", flush=True)

    print("  → Step 5/7: Adding jupyterlab to environment...", flush=True)
    _run_with_progress(
        ["pixi", "add", "jupyterlab"],
        cwd=project_dir,
        env=env,
        indent="      ",
    )
    print("    ✓ JupyterLab added", flush=True)

    print("  → Step 6/7: Installing pixi environment (downloading packages)...", flush=True)
    _run_with_progress(
        ["pixi", "install"],
        cwd=project_dir,
        env=env,
        indent="      ",
    )
    print("    ✓ Environment installed", flush=True)

    print("  → Step 7/7: Finalizing Mojo setup...", flush=True)
    print("    Validating Mojo CLI...", flush=True)
    mojo_stdout, _ = _run_with_progress(
        [
            "pixi",
            "run",
            "--manifest-path",
            str(project_dir / "pixi.toml"),
            "mojo",
            "--version",
        ],
        env=env,
        indent="      ",
    )
    version_line = mojo_stdout.strip().splitlines()
    if version_line:
        print(f"    ✓ Mojo CLI available ({version_line[-1]})", flush=True)
    else:
        print("    ✓ Mojo CLI available", flush=True)

    print("    Creating mojo shim script...", flush=True)
    shim_dir = Path.home() / ".local" / "bin"
    shim_dir.mkdir(parents=True, exist_ok=True)
    shim_path = shim_dir / "mojo"

    # Use full path to pixi in the shim script
    pixi_path = shutil.which("pixi", path=env.get("PATH"))
    if not pixi_path:
        pixi_path = str(Path.home() / ".pixi" / "bin" / "pixi")

    shim_path.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'export MODULAR_SKIP_CRASHPAD="${MODULAR_SKIP_CRASHPAD:-1}"\n'
        'export MODULAR_CRASHPAD_DISABLE="${MODULAR_CRASHPAD_DISABLE:-1}"\n'
        f'exec {pixi_path} run --manifest-path {project_dir / "pixi.toml"} mojo "$@"\n'
    )
    shim_path.chmod(0o755)
    os.environ["PATH"] = f"{shim_dir}:{os.environ.get('PATH', '')}"
    print(f"    ✓ Shim created at {shim_path}", flush=True)

    candidates: list[Path] = []
    env_override = os.environ.get("MOJO_KERNELSPEC_DIR")
    if env_override:
        candidates.append(Path(env_override))

    pixi_kernelspec = (
        project_dir / ".pixi" / "envs" / "default" / "share" / "jupyter" / "kernels" / "mojo"
    )
    candidates.append(pixi_kernelspec)

    kernelspec_src: Path | None = None
    for candidate in candidates:
        if candidate.exists() and (candidate / "kernel.json").exists():
            kernelspec_src = candidate
            break

    if kernelspec_src is None:
        raise RuntimeError(
            "Unable to locate a Mojo kernelspec. Provide MOJO_KERNELSPEC_DIR="
            " pointing to a valid kernelspec directory or ensure the pixi install"
            " completed successfully."
        )

    print(f"    Installing kernelspec from {kernelspec_src} ...", flush=True)
    installed_path = magics.install_kernel_spec_from_dir(
        str(kernelspec_src),
        kernel_name="mojo",
        user=True,
        replace=True,
    )

    kernel_json = Path(installed_path) / "kernel.json"
    try:
        data = json.loads(kernel_json.read_text())
    except Exception as exc:  # pragma: no cover - defensive
        raise RuntimeError(f"Failed to read installed kernel spec at {kernel_json}") from exc

    env_block = data.setdefault("env", {})
    env_block.setdefault("MODULAR_SKIP_CRASHPAD", "1")
    env_block.setdefault("MODULAR_CRASHPAD_DISABLE", "1")
    kernel_json.write_text(json.dumps(data, indent=2))
    print("    ✓ Kernelspec installed", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install language runtimes for BridgeIt.")
    parser.add_argument(
        "language",
        choices=("rust", "mojo"),
        help="Language runtime to install.",
    )
    args = parser.parse_args(argv)

    if args.language == "rust":
        install_rust()
    elif args.language == "mojo":
        install_mojo()
    else:  # pragma: no cover - argparse choices protect this.
        raise ValueError(f"Unsupported language {args.language}")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
