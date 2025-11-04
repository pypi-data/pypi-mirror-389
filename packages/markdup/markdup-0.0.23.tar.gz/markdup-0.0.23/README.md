# MarkDup

[![Pypi Releases](https://img.shields.io/pypi/v/markdup.svg)](https://pypi.python.org/pypi/markdup)
[![Downloads](https://img.shields.io/pepy/dt/markdup)](https://pepy.tech/project/markdup)
[![Development Status](https://img.shields.io/badge/status-alpha-orange.svg)](https://github.com/y9c/markdup)

**A fast, accurate BAM deduplication tool with intelligent UMI detection and correct fragment detection.**

## Why MarkDup?

MarkDup solves critical issues in BAM deduplication:

- **Correct fragment detection:** Proper strand-aware coordinate handling.
- **High performance:** Optimized algorithms and parallel processing.
- **Smart UMI clustering:** Frequency-aware algorithms to prevent over-merging.
- **Automatic detection:** Handles both UMI and non-UMI data seamlessly.

## Quick Start

```bash
# Installation
pip install markdup

# Basic usage (auto-detects everything)
markdup -i input.bam -o output.bam

# With multiple threads
markdup -i input.bam -o output.bam --threads 8

# Force coordinate-based (no UMIs)
markdup -i input.bam -o output.bam --no-umi
```

## Usage

For a full list of options and their descriptions, run:

```bash
markdup --help
```

### Examples

#### Basic Deduplication

```bash
# Auto-detect UMIs and process
markdup -i input.bam -o output.bam

# Force coordinate-based method (no UMIs)
markdup -i input.bam -o output.bam --no-umi
```

#### Advanced Options

```bash
# Custom UMI settings
markdup -i input.bam -o output.bam --umi-tag UB --max-dist-frac 0.15

# Start-only positioning (useful for ChIP-seq)
markdup -i input.bam -o output.bam --start-only

# Keep duplicates and mark them
markdup -i input.bam -o output.bam --keep-duplicates
```

## Output Format

MarkDup adds BAM tags to track deduplication:

| Tag  | Description                             |
| ---- | --------------------------------------- |
| `cn` | Cluster name (chr:start-end:strand:UMI) |
| `cs` | Cluster size (number of reads)          |

## Documentation

- [Installation Guide](docs/installation.md)
- [Usage Guide](docs.usage.md)
- [Algorithm Details](docs/algorithm.md)

## License

MIT License - see [LICENSE](LICENSE) for details.

&nbsp;

<p align="center">
  <img
    src="https://raw.githubusercontent.com/y9c/y9c/master/resource/footer_line.svg?sanitize=true"
  />
</p>
<p align="center">
  Copyright &copy; 2025-present
  <a href="https://github.com/y9c" target="_blank">Chang Y</a>
</p>
<p align="center">
  <a href="https://github.com/y9c/markdup/blob/master/LICENSE">
    <img src="https://img.shields.io/static/v1.svg?style=for-the-badge&label=License&message=MIT&logoColor=d9e0ee&colorA=282a36&colorB=c678dd" />
  </a>
</p>