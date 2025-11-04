"""Additional unit tests for filter subcommand edge cases."""

# pylint: disable=import-outside-toplevel, wrong-import-position, import-error
import os
import shutil
import tempfile

import h5py
import numpy as np
import pytest

import epigeec.python.core.main as epimain


@pytest.fixture(name="temp_dir")
def temp_dir_fixture():
    """Create a temporary directory for test files."""
    test_dir = tempfile.mkdtemp()
    yield test_dir
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)


@pytest.fixture(name="file_paths")
def file_paths_fixture(temp_dir):
    """Generate paths for temporary files."""
    return {
        "chrom_sizes": os.path.join(temp_dir, "test.chrom.sizes"),
        "bed": os.path.join(temp_dir, "test.bed"),
        "bigwig": os.path.join(temp_dir, "test.bw"),
        "hdf5_input": os.path.join(temp_dir, "input.hdf5"),
        "hdf5_output": os.path.join(temp_dir, "output.hdf5"),
    }


def create_chrom_sizes(path, sizes_dict):
    """Create a chromosome sizes file."""
    with open(path, "w", encoding="utf8") as f:
        for chrom, size in sizes_dict.items():
            f.write(f"{chrom}\t{size}\n")


def create_bed_file(path, regions):
    """Create a BED file with specified regions."""
    with open(path, "w", encoding="utf8") as f:
        for chrom, start, end in regions:
            f.write(f"{chrom}\t{start}\t{end}\n")


def create_bigwig(path, chrom_data, chrom_sizes):
    """Create a bigWig file with signal data."""
    try:
        import pyBigWig
    except ImportError:
        pytest.skip("pyBigWig not installed")

    bw = pyBigWig.open(path, "w")
    header = [(chrom, size) for chrom, size in chrom_sizes.items()]
    bw.addHeader(header)

    for chrom, intervals in chrom_data.items():
        chroms = [chrom] * len(intervals)
        starts = [x[0] for x in intervals]
        ends = [x[1] for x in intervals]
        values = [x[2] for x in intervals]
        bw.addEntries(chroms, starts, ends=ends, values=values)

    bw.close()


def count_filtered_bins(hdf5_path):
    """Count total number of bins (non-NaN values) in filtered HDF5."""
    counts = {}
    with h5py.File(hdf5_path, "r") as f:
        signal_id = os.path.basename(hdf5_path)
        if signal_id in f:
            group = f[signal_id]
        else:
            for group in f.values():
                if isinstance(group, h5py.Group):
                    break
            else:
                return {}

        for chrom_name, chrom_arr in group.items():
            data = chrom_arr[:]
            counts[chrom_name] = np.sum(~np.isnan(data))
    return counts


def test_exact_bin_boundaries(file_paths):
    """Test filtering with BED regions that exactly match bin boundaries."""
    resolution = 10000
    chrom_size = 100000  # Exactly 10 bins

    create_chrom_sizes(file_paths["chrom_sizes"], {"chr1": chrom_size})
    create_bigwig(
        file_paths["bigwig"], {"chr1": [(0, chrom_size, 1.0)]}, {"chr1": chrom_size}
    )

    args = [
        "to_hdf5",
        "-bw",
        file_paths["bigwig"],
        file_paths["chrom_sizes"],
        str(resolution),
        file_paths["hdf5_input"],
    ]
    epimain.main(args)

    create_bed_file(
        file_paths["bed"],
        [
            ("chr1", 20000, 30000),
            ("chr1", 30000, 40000),
            ("chr1", 40000, 50000),
        ],
    )

    args = [
        "filter",
        "--select",
        file_paths["bed"],
        file_paths["hdf5_input"],
        file_paths["chrom_sizes"],
        file_paths["hdf5_output"],
    ]
    epimain.main(args)

    counts = count_filtered_bins(file_paths["hdf5_output"])
    assert (
        counts["chr1"] == 3
    ), "Should keep exactly 3 bins for regions matching 3 exact bins"


def test_last_bin_of_chromosome(file_paths):
    """Test that the last bin of a chromosome is handled correctly."""
    resolution = 10000
    chrom_size = 95000

    create_chrom_sizes(file_paths["chrom_sizes"], {"chr1": chrom_size})
    create_bigwig(
        file_paths["bigwig"], {"chr1": [(0, chrom_size, 1.0)]}, {"chr1": chrom_size}
    )

    args = [
        "to_hdf5",
        "-bw",
        file_paths["bigwig"],
        file_paths["chrom_sizes"],
        str(resolution),
        file_paths["hdf5_input"],
    ]
    epimain.main(args)

    create_bed_file(file_paths["bed"], [("chr1", 90000, 95000)])

    args = [
        "filter",
        "--select",
        file_paths["bed"],
        file_paths["hdf5_input"],
        file_paths["chrom_sizes"],
        file_paths["hdf5_output"],
    ]
    epimain.main(args)

    counts = count_filtered_bins(file_paths["hdf5_output"])
    assert (
        counts.get("chr1", 0) == 1
    ), "Should keep exactly 1 bin for last chromosome bin"


def test_region_spanning_bin_boundary(file_paths):
    """Test region that spans exactly from one bin boundary to another."""
    resolution = 10000
    chrom_size = 100000

    create_chrom_sizes(file_paths["chrom_sizes"], {"chr1": chrom_size})
    create_bigwig(
        file_paths["bigwig"], {"chr1": [(0, chrom_size, 1.0)]}, {"chr1": chrom_size}
    )

    args = [
        "to_hdf5",
        "-bw",
        file_paths["bigwig"],
        file_paths["chrom_sizes"],
        str(resolution),
        file_paths["hdf5_input"],
    ]
    epimain.main(args)

    create_bed_file(file_paths["bed"], [("chr1", 20000, 50000)])

    args = [
        "filter",
        "--select",
        file_paths["bed"],
        file_paths["hdf5_input"],
        file_paths["chrom_sizes"],
        file_paths["hdf5_output"],
    ]
    epimain.main(args)

    counts = count_filtered_bins(file_paths["hdf5_output"])
    assert (
        counts["chr1"] == 3
    ), "Region [20000, 50000) should cover exactly 3 bins (2, 3, 4)"


def test_single_base_at_bin_boundary(file_paths):
    """Test that a single base at a bin boundary is handled correctly."""
    resolution = 10000
    chrom_size = 100000

    create_chrom_sizes(file_paths["chrom_sizes"], {"chr1": chrom_size})
    create_bigwig(
        file_paths["bigwig"], {"chr1": [(0, chrom_size, 1.0)]}, {"chr1": chrom_size}
    )

    args = [
        "to_hdf5",
        "-bw",
        file_paths["bigwig"],
        file_paths["chrom_sizes"],
        str(resolution),
        file_paths["hdf5_input"],
    ]
    epimain.main(args)

    create_bed_file(file_paths["bed"], [("chr1", 30000, 30001)])

    args = [
        "filter",
        "--select",
        file_paths["bed"],
        file_paths["hdf5_input"],
        file_paths["chrom_sizes"],
        file_paths["hdf5_output"],
    ]
    epimain.main(args)

    counts = count_filtered_bins(file_paths["hdf5_output"])
    assert counts["chr1"] == 1, "Single base at bin boundary should touch exactly 1 bin"


def test_off_by_one_regression(file_paths):
    """Regression test: ensure we don't include the bin at end position."""
    resolution = 1000
    chrom_size = 10000

    create_chrom_sizes(file_paths["chrom_sizes"], {"chr1": chrom_size})
    create_bigwig(
        file_paths["bigwig"], {"chr1": [(0, chrom_size, 1.0)]}, {"chr1": chrom_size}
    )

    args = [
        "to_hdf5",
        "-bw",
        file_paths["bigwig"],
        file_paths["chrom_sizes"],
        str(resolution),
        file_paths["hdf5_input"],
    ]
    epimain.main(args)

    create_bed_file(file_paths["bed"], [("chr1", 0, 5000)])

    args = [
        "filter",
        "--select",
        file_paths["bed"],
        file_paths["hdf5_input"],
        file_paths["chrom_sizes"],
        file_paths["hdf5_output"],
    ]
    epimain.main(args)

    counts = count_filtered_bins(file_paths["hdf5_output"])
    assert (
        counts["chr1"] == 5
    ), "Half-open interval [0, 5000) should include exactly 5 bins, not 6"


def test_multiple_chromosomes_last_bins(file_paths):
    """Test filtering with multiple chromosomes, focusing on last bins."""
    resolution = 10000
    chrom_sizes = {
        "chr1": 95000,
        "chr2": 105000,
        "chr3": 100000,
    }

    create_chrom_sizes(file_paths["chrom_sizes"], chrom_sizes)
    bigwig_data = {chrom: [(0, size, 1.0)] for chrom, size in chrom_sizes.items()}
    create_bigwig(file_paths["bigwig"], bigwig_data, chrom_sizes)

    args = [
        "to_hdf5",
        "-bw",
        file_paths["bigwig"],
        file_paths["chrom_sizes"],
        str(resolution),
        file_paths["hdf5_input"],
    ]
    epimain.main(args)

    create_bed_file(
        file_paths["bed"],
        [
            ("chr1", 90000, 95000),
            ("chr2", 100000, 105000),
            ("chr3", 90000, 100000),
        ],
    )

    args = [
        "filter",
        "--select",
        file_paths["bed"],
        file_paths["hdf5_input"],
        file_paths["chrom_sizes"],
        file_paths["hdf5_output"],
    ]
    epimain.main(args)

    counts = count_filtered_bins(file_paths["hdf5_output"])
    assert counts.get("chr1", 0) == 1, "chr1 should have 1 bin"
    assert counts.get("chr2", 0) == 1, "chr2 should have 1 bin"
    assert counts.get("chr3", 0) == 1, "chr3 should have 1 bin"
