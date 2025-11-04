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
"""Unit tests for 'utils' module."""
from __future__ import absolute_import, division, print_function

import os.path

from epigeec.python.core import config, utils


def test_read_chrom_sizes():
    """Tests reading a chromosome sizes file into a dictionary."""
    expected = {
        "chrV": "576874",
        "chrII": "813184",
        "chrVI": "270161",
        "chrIV": "1531933",
        "chrXIV": "784333",
        "chrXVI": "948066",
        "chrXI": "666816",
        "chrVII": "1090940",
        "chrX": "745751",
        "chrXV": "1091291",
        "chrIX": "439888",
        "chrM": "85779",
        "chrXII": "1078177",
        "chrIII": "316620",
        "chrXIII": "924431",
        "chrI": "230218",
        "chrVIII": "562643",
    }
    chrom_path = os.path.join(config.RES_DIR, "chrom_sizes", "saccer3.can.chrom.sizes")
    chroms = utils.read_chrom_sizes(chrom_path)
    assert chroms == expected


def test_read_compatibility_data():
    """Tests reading compatibility data from HDF5 and chrom sizes."""
    expected = {
        "bin": 10000,
        "chrV": 58,
        "chrII": 82,
        "chrVI": 28,
        "chrXIV": 79,
        "chrXVI": 95,
        "chrXI": 67,
        "chrVII": 110,
        "chrXV": 110,
        "chrIX": 44,
        "chrIII": 32,
        "chrXII": 108,
        "chrXIII": 93,
        "chrM": 9,
        "chrX": 75,
        "chrIV": 154,
        "chrI": 24,
        "chrVIII": 57,
    }

    chrom_path = os.path.join(config.RES_DIR, "chrom_sizes", "saccer3.can.chrom.sizes")
    hdf5_path = os.path.join(config.TEST_DIR, "files", "hdf5", "test.hdf5")

    compat_data = utils.read_compatibility_data(hdf5_path, chrom_path)
    assert compat_data == expected
