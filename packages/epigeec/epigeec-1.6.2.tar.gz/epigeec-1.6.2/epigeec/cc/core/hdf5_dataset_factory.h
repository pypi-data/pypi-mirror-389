/* Copyright (C) 2015 Jonathan Laperle. All Rights Reserved.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
==============================================================================*/

#ifndef HDF5_DATASET_FACTORY_H
#define HDF5_DATASET_FACTORY_H

#include <string>
#include <vector>
#include "hdf5_dataset.h"
#include "genomic_file_reader.h"

class Hdf5DatasetFactory {
 public:
  static Hdf5Dataset* createHdf5Dataset(
    const std::string& file_path,
    GenomicFileReader* genomic_file_reader,
    const std::string& chrom,
    int size,
    int bin);
  static Hdf5Dataset* createHdf5Dataset(
    const std::string& name,
    const std::vector<float>& content,
    const std::string& chrom,
    int bin);
};

void FillDataset(GenomicFileReader* genomic_file_reader,
                 Hdf5Dataset* hdf5_dataset,
                 const std::string& chroms);

std::string ExtractName(const std::string& name);

std::string StripLastDot(const std::string& name);

std::string StripLastSlash(const std::string& name);

#endif  // HDF5_DATASET_FACTORY_H
