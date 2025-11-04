# Copyright (C) 2015 Jonathan Laperle. All Rights Reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# =============================================================================
"""Unit test for end-to-end functionality of EpiGeEC."""
# pylint: disable=import-error, wrong-import-position
import logging
import os
from types import SimpleNamespace

import pytest

import epigeec.python.core.main as epimain
from epigeec.python.core import config, launcher, make_matrix

# --- Helper functions ---


def get_corr_vals(mat):
    """Extract correlation values from a matrix file object."""
    mat.readline()
    vals = []
    for line in mat:
        vals += line.split()[1:]
    return vals


def launch_to_hdf5(sig_path, chrom_path, resolution, hdf5_path):
    """Launch the 'to_hdf5' command."""
    args = ["to_hdf5", "-bw", sig_path, chrom_path, resolution, hdf5_path]
    logging.debug(args)
    epimain.main(args)


def launch_filter(hdf5_path, chrom_path, filtered_path):
    """Launch the 'filter' command."""
    args = ["filter", hdf5_path, chrom_path, filtered_path]
    logging.debug(args)
    epimain.main(args)


def launch_corr(list_path, chrom_path, mat_path):
    """Launch the 'correlate' command."""
    args = ["correlate", list_path, chrom_path, mat_path]
    logging.debug(args)
    epimain.main(args)


def launch_corr_with_options(list_path, chrom_path, mat_path):
    """Launch the 'correlate' command with '--concat' and '--name' options."""
    args = [
        "correlate",
        "--concat",
        "--name",
        "ed 23\t\nsdn",
        list_path,
        chrom_path,
        mat_path,
    ]
    logging.debug(args)
    epimain.main(args)


def launch_corr_nm(list_path1, list_path2, chrom_path, mat_path):
    """Launch non-symmetric correlation that creates a matrix from two lists."""
    launcher.corr_nm(False, list_path1, list_path2, chrom_path, mat_path)


def launch_make_matrix(mat_nn, mat_nm, mat_mm, mat_path):
    """Launch the 'make_matrix' command."""
    args = ["-nm", mat_nm, "-mm", mat_mm, mat_nn, mat_path]
    logging.debug(args)
    make_matrix.main(args)


# --- Pytest Fixtures for Setup and Teardown ---


@pytest.fixture(name="paths")
def paths_fixture():
    """Provides a namespace object with all necessary file paths."""
    p = SimpleNamespace()
    p.files_dir = os.path.join(config.TEST_DIR, "files")
    p.sig_dir = os.path.join(p.files_dir, "signal")
    p.hdf5_dir = os.path.join(p.files_dir, "hdf5")
    p.filtered_dir = os.path.join(p.files_dir, "filtered")
    p.chrom_dir = os.path.join(config.RES_DIR, "chrom_sizes")
    p.list_path = os.path.join(config.TEST_DIR, "test_list.txt")
    p.mat_path = os.path.join(p.files_dir, "test.mat")
    return p


@pytest.fixture(name="file_cleanup")
def file_cleanup_fixture():
    """A fixture to automatically clean up generated files after a test."""
    files_to_remove = []
    yield files_to_remove  # The test function will populate this list
    # --- Teardown code runs after the test is complete ---
    for f in files_to_remove:
        if os.path.exists(f):
            try:
                os.remove(f)
            except OSError as e:
                logging.warning(f"Error removing file {f}: {e}")


# --- Pytest Test Functions ---


def test_e2e_nm(paths, file_cleanup):
    """End-to-end test for non-matching dataset correlation."""
    sig_path = [
        os.path.join(paths.sig_dir, "d9f18e91644bacfee3669d577b661d15"),
        os.path.join(paths.sig_dir, "fd85fe6672c629a116a9b6131883a60b"),
        os.path.join(paths.sig_dir, "70ac0e9e6b4dbdf5d6b5cbf54a8989e3"),
    ]
    hdf5_path1 = [
        os.path.join(paths.hdf5_dir, "d9f18e91644bacfee3669d577b661d15"),
        os.path.join(paths.hdf5_dir, "fd85fe6672c629a116a9b6131883a60b"),
    ]
    hdf5_path2 = [os.path.join(paths.hdf5_dir, "70ac0e9e6b4dbdf5d6b5cbf54a8989e3")]
    list_path2 = os.path.join(config.TEST_DIR, "test_list2.txt")
    mat_path1 = os.path.join(paths.files_dir, "test1.mat")
    mat_path2 = os.path.join(paths.files_dir, "test2.mat")
    mat_path3 = os.path.join(paths.files_dir, "test3.mat")
    chrom_path = os.path.join(paths.chrom_dir, "saccer3.can.chrom.sizes")
    resolution = "10000"

    # Register files for automatic cleanup
    file_cleanup.extend(
        hdf5_path1
        + hdf5_path2
        + [paths.list_path, list_path2, mat_path1, mat_path2, mat_path3, paths.mat_path]
    )

    with open(paths.list_path, "w", encoding="utf8") as test_list:
        test_list.write(f"{hdf5_path1[0]}\n{hdf5_path1[1]}")

    with open(list_path2, "w", encoding="utf8") as test_list:
        test_list.write(f"{hdf5_path2[0]}")

    launch_to_hdf5(sig_path[0], chrom_path, resolution, hdf5_path1[0])
    launch_to_hdf5(sig_path[1], chrom_path, resolution, hdf5_path1[1])
    launch_to_hdf5(sig_path[2], chrom_path, resolution, hdf5_path2[0])

    launch_corr(paths.list_path, chrom_path, mat_path1)
    launch_corr(list_path2, chrom_path, mat_path2)
    launch_corr_nm(paths.list_path, list_path2, chrom_path, mat_path3)

    launch_make_matrix(mat_path1, mat_path3, mat_path2, paths.mat_path)

    expected = os.path.join(paths.files_dir, "expected_nm")
    with (
        open(paths.mat_path, "r", encoding="utf8") as res_file,
        open(expected, "r", encoding="utf8") as exp_file,
    ):
        assert res_file.read() == exp_file.read()


def test_e2e_hg19(paths, file_cleanup):
    """End-to-end test with hg19 chromosome sizes."""
    sig_path = [
        os.path.join(paths.sig_dir, "001f63cdf00286183e32c1bb0fd6d85f"),
        os.path.join(paths.sig_dir, "002f4247fadb6c6e4000a6fc12e5b93a"),
    ]
    hdf5_path = [
        os.path.join(paths.hdf5_dir, "001f63cdf00286183e32c1bb0fd6d85f"),
        os.path.join(paths.hdf5_dir, "002f4247fadb6c6e4000a6fc12e5b93a"),
    ]
    chrom_path = os.path.join(paths.chrom_dir, "hg19.noy.chrom.sizes")
    resolution = "10000"

    file_cleanup.extend(hdf5_path + [paths.list_path, paths.mat_path])

    launch_to_hdf5(sig_path[0], chrom_path, resolution, hdf5_path[0])
    launch_to_hdf5(sig_path[1], chrom_path, resolution, hdf5_path[1])

    with open(paths.list_path, "w", encoding="utf8") as test_list:
        test_list.write(f"{hdf5_path[0]}\n{hdf5_path[1]}")

    launch_corr(paths.list_path, chrom_path, paths.mat_path)

    expected = os.path.join(paths.files_dir, "expected_hg19")
    with (
        open(paths.mat_path, "r", encoding="utf8") as res_file,
        open(expected, "r", encoding="utf8") as exp_file,
    ):
        assert res_file.read() == exp_file.read()


def test_e2e_kent(paths, file_cleanup):
    """End-to-end test with Kent-style options."""
    sig_path = [
        os.path.join(paths.sig_dir, "d9f18e91644bacfee3669d577b661d15"),
        os.path.join(paths.sig_dir, "fd85fe6672c629a116a9b6131883a60b"),
    ]
    hdf5_path = [
        os.path.join(paths.hdf5_dir, "d9f18e91644bacfee3669d577b661d15"),
        os.path.join(paths.hdf5_dir, "fd85fe6672c629a116a9b6131883a60b"),
    ]
    chrom_path = os.path.join(paths.chrom_dir, "saccer3.can.chrom.sizes")
    resolution = "10000"

    file_cleanup.extend(hdf5_path + [paths.list_path, paths.mat_path])

    launch_to_hdf5(sig_path[0], chrom_path, resolution, hdf5_path[0])
    launch_to_hdf5(sig_path[1], chrom_path, resolution, hdf5_path[1])

    with open(paths.list_path, "w", encoding="utf8") as test_list:
        test_list.write(f"{hdf5_path[0]}\n{hdf5_path[1]}")

    launch_corr_with_options(paths.list_path, chrom_path, paths.mat_path)

    expected = os.path.join(paths.files_dir, "expected_w")
    with (
        open(paths.mat_path, "r", encoding="utf8") as res_file,
        open(expected, "r", encoding="utf8") as exp_file,
    ):
        assert res_file.read() == exp_file.read()


def test_e2e_saccer(paths, file_cleanup):
    """End-to-end test with saccer3 and filtering step."""
    sig_path = [
        os.path.join(paths.sig_dir, "d9f18e91644bacfee3669d577b661d15"),
        os.path.join(paths.sig_dir, "fd85fe6672c629a116a9b6131883a60b"),
    ]
    hdf5_path = [
        os.path.join(paths.hdf5_dir, "d9f18e91644bacfee3669d577b661d15"),
        os.path.join(paths.hdf5_dir, "fd85fe6672c629a116a9b6131883a60b"),
    ]
    filtered_path = [
        os.path.join(paths.filtered_dir, "d9f18e91644bacfee3669d577b661d15"),
        os.path.join(paths.filtered_dir, "fd85fe6672c629a116a9b6131883a60b"),
    ]
    chrom_path = os.path.join(paths.chrom_dir, "saccer3.can.chrom.sizes")
    resolution = "10000"

    file_cleanup.extend(hdf5_path + filtered_path + [paths.list_path, paths.mat_path])

    with open(paths.list_path, "w", encoding="utf8") as test_list:
        test_list.write(f"{filtered_path[0]}\n{filtered_path[1]}")

    launch_to_hdf5(sig_path[0], chrom_path, resolution, hdf5_path[0])
    launch_to_hdf5(sig_path[1], chrom_path, resolution, hdf5_path[1])
    launch_filter(hdf5_path[0], chrom_path, filtered_path[0])
    launch_filter(hdf5_path[1], chrom_path, filtered_path[1])

    launch_corr(paths.list_path, chrom_path, paths.mat_path)

    expected = os.path.join(paths.files_dir, "expected")
    with (
        open(paths.mat_path, "r", encoding="utf8") as res_file,
        open(expected, "r", encoding="utf8") as exp_file,
    ):
        assert res_file.read() == exp_file.read()
