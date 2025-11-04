# epiGeEC

The **epiGenomic Efficient Correlator** tool is designed to efficiently perform pairwise correlations of thousands of epigenomic datasets. It supports a growing number of file formats and offers the possibility to compute correlations at any resolution on custom or predefined filtered regions. Please refer to the following paper for a description of epiGeEC : <https://academic.oup.com/bioinformatics/article/35/4/674/5058096>

A galaxy implementation including thousands of pre-computed public datasets is available at <http://epigeec.genap.ca/galaxy/> and also includes support for the WIG format and Spearman correlation. It also offers [tools](https://bitbucket.org/labjacquespe/epigeec_analysis/src/master/) for further annotation and analysis of the matrix files created by epiGeEC.

## Installation

Precompiled wheels are available for **Linux (x86_64, aarch64)** and **macOS (x86_64, arm64)** on [PyPI](https://pypi.org/project/epigeec/).

### 1. Install epiGeEC

```bash
pip install epigeec
```

This will automatically install all required dependencies. If you encounter issues, please see the troubleshooting steps section.

### Summary

Most users can simply run `pip install epigeec`. If pip fails to build dependencies like `h5py`, install system headers or use a modern Python environment (e.g. via `uv` or `conda`) to ensure compatible wheels are found.

## How To Use

The process is done in 2 or 3 steps, conversion to hdf5, filtering(optional) and correlation.

The signal files (bedgraph, wig or bigwig) need to first be converted to hdf5 format, this will require a chromSizes file(available [here](epigeec/resource) or from [UCSC](http://hgdownload.cse.ucsc.edu/downloads.html)) for the assembly used by your signal files. The chromSizes file can be truncated. For example, keeping only canonical chromosomes will work even if the bigwig countains non-canonical chromosomes. You will also need to choose a resolution, we suggest a resolution of 1000 or 10000 base pair to obtain biologically interesting results.

The hdf5 files can be filtered over certain regions (such as regions corresponding to genes) using your own bed files or those available [here](epigeec/resource).

The final step, the correlation itself, will require a list of all hdf5 files to be correlated(one file path per line) as well as the chromSizes file used to generate the hdf5 files. It is not possible to correlate files from different assemblies.

For more info on each parameter use the help flag

```bash
epigeec [tool] --help
```

Conversion of a signal file to the hdf5 format

```bash
usage: epigeec to_hdf5 [-h] (-bw | -bg) signalFile chromSizes resolution outHdf5
```

Filter an hdf5 file (optional)

```bash
usage: epigeec filter [-h] [--select SELECT] [--exclude EXCLUDE] hdf5 chromSizes outHdf5
```

Generate an NxN Pearson correlation matrix

```bash
usage: epigeec correlate [-h] [--concat] [--name] hdf5List chromSizes outMatrix 
```

### Resources and filters

List of assemblies and filters offered in the [resource](epigeec/resource) folder:

1. hg19
    * blklst: blacklisted regions from [here](https://sites.google.com/site/anshulkundaje/projects/blacklists)
    * gene: regions corresponding to genes (from refSeq annotation)
    * tss: transcription sites (from refSeq annotation)
1. hg38
    * gene: regions corresponding to genes (from refSeq annotation)
    * tss: transcription sites (from refSeq annotation)
1. mm10
    * blklst: blacklisted regions from [here](https://sites.google.com/site/anshulkundaje/projects/blacklists)
1. saccer3

## Example

Create a directory structure to hold the data

```text
myfolder
├── signal
├── hdf5
├── filtered
└── resource
```

Start running the tools

```bash
epigeec to_hdf5 -bw signal/myfile.bw resource/chrom_sizes 1000 hdf5/myfile.hdf5
epigeec filter hdf5/myfile.hdf5 resource/chrom_sizes filtered/myfile.hdf5 -s resource/sel.bed -e resource/excl.bed
epigeec correlate filtered_list resource/chrom_sizes mymatrix.mat --name 5dts_1kb 
```

The output is a tab separated matrix file with your correlations

```text
5dts_1kb file1 file2 file3 file4 file5
file1 1.0000 0.0225 0.0579 0.0583 0.0603
file2 0.0225 1.0000 0.0625 0.0523 0.0642
file3 0.0579 0.0625 1.0000 0.7535 0.7917
file4 0.0583 0.0523 0.7535 1.0000 0.7754
file5 0.0603 0.0642 0.7917 0.7754 1.0000
```

## Installation troubleshooting

### 1. Recommended: Use a clean environment

Using an isolated Python environment helps avoid version conflicts:

**Using `venv` (built-in):**

```bash
python3 -m venv env
source env/bin/activate
pip install epigeec
```

**Using [`uv`](https://github.com/astral-sh/uv) (fastest option):**

```bash
uv venv
source .venv/bin/activate
uv pip install epigeec
```

**Using `conda`:**

```bash
conda create -n epigeec python=3.11
conda activate epigeec
pip install epigeec
```

### 2. Dependency issues

`pip` will usually install all dependencies automatically.
However, installation can fail on some systems if binary wheels are unavailable or incompatible (e.g., older distributions, minimal Docker images, or systems missing compilers or libraries).

Common solutions:

* **Update pip and setuptools:**

  ```bash
  pip install -U pip setuptools wheel
  ```

* **Install missing system libraries** (Debian/Ubuntu):

  ```bash
  sudo apt install python3-dev libhdf5-dev
  ```

* **Manually install dependencies:**

  ```bash
  pip install -U numpy pandas h5py
  ```

### 3. Getting pip

If pip is not available on your system:

**Debian/Ubuntu:**

```bash
sudo apt install python3-pip
```

**macOS (via Homebrew):**

```bash
brew install python
```

### 4. Build from source

If installation via pip fails (e.g., missing wheels or system compilers), you can build epiGeEC from source.

**Prerequisites (Linux/macOS):**

You may need to install development tools first:

```bash
# Debian/Ubuntu
sudo apt install build-essential python3-dev cmake libhdf5-dev

# macOS (Homebrew)
brew install cmake hdf5
```

#### Clone the repository

```bash
git clone https://github.com/rabyj/epigeec.git
cd epigeec
```

#### Create and activate a virtual environment

```bash
python3 -m venv env
source env/bin/activate
pip install setuptools wheel
```

#### Build and install epiGeEC

```bash
cmake .
make -j $(nproc --all) # build with all available cores
pip install .
```

## License

[GNU General Public License v3](LICENSE)
