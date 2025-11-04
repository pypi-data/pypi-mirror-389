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

#include <iostream>
#include <string>
#include <vector>
#include "hdf5_dataset_factory.h"

Hdf5Dataset* Hdf5DatasetFactory::createHdf5Dataset(
  const std::string& dataset_name,
  GenomicFileReader* genomic_file_reader,
  const std::string& chrom,
  int size,
  int bin) {
    std::string name = ExtractName(dataset_name);
    name += "/" + chrom;
    Hdf5Dataset* hdf5_dataset = new Hdf5Dataset(name, size, bin);
    FillDataset(genomic_file_reader, hdf5_dataset, chrom);
    hdf5_dataset->UpdateSum();
    return hdf5_dataset;
}

Hdf5Dataset* Hdf5DatasetFactory::createHdf5Dataset(
  const std::string& filename,
  const std::vector<float>& content,
  const std::string& chrom,
  int bin) {
    std::string name = filename;
    name += "/" + chrom;
    Hdf5Dataset* hdf5_dataset = new Hdf5Dataset(name, content, bin);
    return hdf5_dataset;
}


void FillDataset(GenomicFileReader* genomic_file_reader,
                 Hdf5Dataset* hdf5_dataset,
                 const std::string& chrom) {
  GenomicDataLine token;
  genomic_file_reader->SeekChr(chrom);
  while (!genomic_file_reader->NextToken(token)) {
    // std::cout<< token.display()<< std::endl; // DEBUG
    hdf5_dataset->FeedDataLine(token);
  }
}

std::string ExtractName(const std::string& name) {
  std::string processed_name;
  // processed_name = StripLastDot(name);
  processed_name = StripLastSlash(name);
  return processed_name;
}

std::string StripLastDot(const std::string& name) {
  size_t last_dot = name.find_last_of(".");
  if (last_dot == std::string::npos) return name;
  std::string tmp = name.substr(0, last_dot);
  return tmp;
}

std::string StripLastSlash(const std::string& name) {
  size_t last_slash = name.find_last_of("/");
  if (last_slash == std::string::npos) return name;
  std::string tmp = name.substr(last_slash);
  return tmp;
}
