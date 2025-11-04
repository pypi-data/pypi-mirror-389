# bridgeit

An experimental hack to run other languages than python in solve.it.com.

## Requirements

- Python 3.12+
- https://solve.it.com

## Installation

```bash
!pip install -U bridgeit
```

## How it Works

BridgeIt enables running non-Python languages in SolveIt notebooks through a three-step process:

1. **Compiler Installation**: Automatically installs language compilers and toolchains (e.g., evcxr for Rust, Mojo via pixi)

2. **Kernelspec Registration**: Registers Jupyter kernelspecs that define how to execute each language

3. **Cell Magic Binding**: Creates IPython cell magics (e.g., `%%rust`, `%%mojo`) that bridge notebook cells to the installed kernels

When you use `%%rust` or `%%mojo`, BridgeIt sends your code to the appropriate kernel for execution and displays the results inline.

## Usage

### Quick Start

```python
import bridgeit

# Show available commands
bridgeit.help()

# List supported languages
bridgeit.langs()
```

### Rust Example

```python
# Install Rust kernel
bridgeit.install("rust")

# Activate Rust magic
bridgeit.use("rust")
```

```rust
%%rust
fn main() {
    println!("Hello from Rust 🦀");
}
main()
```

```rust
%%rust
let value = 21;
println!("{}", value * 2);
```

### Mojo Example

```python
# Install Mojo kernel
bridgeit.install("mojo")

# Activate Mojo magic
bridgeit.use("mojo")
```

```mojo
%%mojo
fn main():
    print("Hello from Mojo 🔥")
main()
```

```mojo
%%mojo
alias value = 10
print(value * 3)
```


## License
Apache 2.0
