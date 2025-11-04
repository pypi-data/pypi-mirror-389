# vcf2bedgraph

Convert DeepVariant VCF files to BedGraph format with Variant Allele Frequency (VAF) values. The output is automatically compressed with bgzip and indexed with tabix for efficient querying.

## Features

- 🚀 **Efficient streaming**: Processes large VCF files without loading everything into memory
- 🧬 **DeepVariant support**: Extracts VAF directly from DeepVariant FORMAT fields
- 📦 **Automatic compression**: Output is bgzipped and indexed by default
- 🎯 **Flexible filtering**: Control quality thresholds with command-line parameters
- 📊 **BedGraph format**: Standard genomics format compatible with UCSC and other tools

## Installation

### From PyPI

```bash
pip install vcf2bedgraph
```

### From source with uv

```bash
git clone https://github.com/fcliquet/vcf2bedgraph.git
cd vcf2bedgraph
uv sync
```

## Usage

### Basic usage

```bash
vcf2bedgraph input.vcf.gz -o output.bedgraph
```

This will:

1. Process the VCF file
2. Extract VAF for the first sample
3. Apply default filters (QUAL >= 20, GQ >= 0, DP >= 10)
4. Compress output to `output.bedgraph.gz`
5. Create tabix index `output.bedgraph.gz.tbi`
6. Remove the uncompressed file

### Command-line options

```bash
vcf2bedgraph [-h] [-o OUTPUT] [--filter-gq FILTER_GQ]
             [--filter-dp FILTER_DP] [--filter-qual FILTER_QUAL]
             [--no-compress] VCF
```

Arguments:

- `VCF`: Path to the input VCF file (required)
- `-o, --output OUTPUT`: Path to the output BedGraph file (required)
- `--filter-gq FILTER_GQ`: Minimum genotype quality threshold (default: 0)
- `--filter-dp FILTER_DP`: Minimum depth threshold (default: 10)
- `--filter-qual FILTER_QUAL`: Minimum variant quality threshold (default: 20)
- `--no-compress`: Skip compression and indexing of the output BedGraph file

### Examples

#### Basic conversion with defaults

```bash
vcf2bedgraph sample.vcf.gz -o sample.bedgraph
```

Output: `sample.bedgraph.gz` (compressed) and `sample.bedgraph.gz.tbi` (index)

#### Custom filters

```bash
vcf2bedgraph sample.vcf.gz -o sample.bedgraph \
  --filter-qual 30 --filter-gq 20 --filter-dp 15
```

#### Skip compression

```bash
vcf2bedgraph sample.vcf.gz -o sample.bedgraph --no-compress
```

Output: `sample.bedgraph` (uncompressed only)

#### Query the indexed file

```bash
python3 << 'EOF'
import pysam
tbx = pysam.TabixFile('sample.bedgraph.gz')
for record in tbx.fetch('chr1', 1000, 2000):
    print(record)
EOF
```

## Output Format

The output is a standard BedGraph file with the following columns:

```text
chr1  15273  15274  0.5625
chr1  15819  15820  0.7317
chr1  47959  47960  1.0000
```

- **Column 1**: Chromosome
- **Column 2**: Start position (0-based, converted from VCF 1-based)
- **Column 3**: End position
- **Column 4**: VAF (Variant Allele Frequency, 0.0-1.0)

## Filtering

The tool applies the following filters to variants:

1. **FILTER column**: Only PASS variants are included
2. **QUAL**: Minimum variant quality (default: 20)
3. **GQ**: Minimum genotype quality (default: 0)
4. **DP**: Minimum depth (default: 10)

Adjust these with command-line options to match your quality requirements.

## Publishing to PyPI

### Prerequisites

1. **PyPI Account**: Create an account at [pypi.org](https://pypi.org)
2. **GitHub Trusted Publisher**: Configure PyPI to trust GitHub Actions
   - Go to PyPI project settings
   - Add a trusted publisher with:
     - Owner: `fcliquet`
     - Repository: `vcf2bedgraph`
     - Workflow name: `publish.yml`
     - Environment name: `pypi`

### Versioning

The version is managed directly in `pyproject.toml` and read dynamically by the package at runtime using `importlib.metadata`.

To manage the version, use the `uv version` command which automatically updates `pyproject.toml`, `uv.lock`, and rebuilds the lock file.

### Bumping the version

Use the `uv version` command to bump versions automatically:

```bash
# Show current version
uv version

# Bump patch version (0.1.0 -> 0.1.1)
uv version --bump patch

# Bump minor version (0.1.0 -> 0.2.0)
uv version --bump minor

# Bump major version (0.1.0 -> 1.0.0)
uv version --bump major

# Set a specific version
uv version 0.2.0
```

The `uv version` command automatically:

- Updates `src/vcf2bedgraph/__about__.py`
- Updates `pyproject.toml`
- Re-locks dependencies (`uv.lock`)

### Creating a release

1. Bump the version:

```bash
uv version --bump minor
```

1. Commit the changes:

```bash
git add src/vcf2bedgraph/__about__.py pyproject.toml uv.lock
git commit -m "chore: bump version to $(uv version --short)"
```

1. Create a git tag:

```bash
git tag v$(uv version --short)
git push origin main
git push origin v$(uv version --short)
```

### Publishing workflow

When you push a tag matching `v*`, GitHub Actions automatically:

1. Builds the package (wheel and sdist)
2. Tests the build
3. Publishes to PyPI using trusted publisher authentication

Monitor progress at: [GitHub Actions](https://github.com/fcliquet/vcf2bedgraph/actions)

### Semver versioning guide

- **Patch** (0.0.X): Bug fixes, minor improvements
- **Minor** (0.X.0): New features, backward compatible
- **Major** (X.0.0): Breaking changes

## Development

### Setup development environment

```bash
git clone https://github.com/fcliquet/vcf2bedgraph.git
cd vcf2bedgraph
uv sync
```

### Run the CLI in development mode

```bash
uv run vcf2bedgraph --help
uv run vcf2bedgraph tests/B00EYQO.vcf.gz -o output.bedgraph
```

### Dependencies

- **cyvcf2**: High-performance VCF parsing
- **pysam**: Compression and indexing with htslib

## License

MIT License - see LICENSE file for details

## Author

Created by fcliquet
