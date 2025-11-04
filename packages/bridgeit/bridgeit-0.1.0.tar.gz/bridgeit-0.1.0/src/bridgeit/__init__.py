from .magics import (
    LANGUAGE_CONFIGS,
    LanguageConfig,
    available_languages,
    help,
    install,
    install_kernel_spec_from_dir,
    langs,
    list_installed_kernels,
    make_kernelspec_runner,
    register_magic,
    register_rust_magic,
    use,
)

__version__ = "0.1.1"

__all__ = [
    "__version__",
    "help",
    "langs",
    "install",
    "use",
    "register_rust_magic",
    "register_magic",
    "make_kernelspec_runner",
    "list_installed_kernels",
    "install_kernel_spec_from_dir",
    "available_languages",
    "LANGUAGE_CONFIGS",
    "LanguageConfig",
]


# Show help message when module is imported in a notebook
try:
    __IPYTHON__  # type: ignore
    print("BridgeIt loaded! Try:")
    print("  bridgeit.help()    - Show all commands")
    print("  bridgeit.langs()   - List available languages")
except NameError:
    # Not in IPython/Jupyter, skip the message
    pass
