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

#include <fstream>
#include <iostream>
#include <string>
#include <utility>
#include <vector>
#include "hdf5_writer.h"
#include "hdf5_hl.h"

Hdf5Writer::Hdf5Writer(const std::string& file_path){
  file_path_ = file_path;
  file_id_ = Create();
}

void Hdf5Writer::AddDataset(const std::string& name,
                        hsize_t size,
                        const std::vector<float>& data) {
  H5LTmake_dataset_float(file_id_, name.c_str(), 1, &size, &data[0]);
}

void Hdf5Writer::AddDataset(Hdf5Dataset& hdf5_dataset) {
  std::string path;
  hsize_t size;
  std::vector<float> data;

  path = hdf5_dataset.name();
  size = hdf5_dataset.size();
  data = hdf5_dataset.GetContent();

  std::pair<std::string, std::string> split_path;
  split_path = SplitPath(path);
  std::string file_name = split_path.first;
  std::string chr_name = split_path.second;

  if (IsValid(file_name)) {
    AddDataset("/" + path, size, data);
    SetSumX("/" + path, hdf5_dataset.sumX());
    SetSumXX("/" + path, hdf5_dataset.sumXX());
  } else {
    CreateGroup(file_name);
    AddDataset("/" + path, size, data);
    SetSumX("/" + path, hdf5_dataset.sumX());
    SetSumXX("/" + path, hdf5_dataset.sumXX());
  }
}

void Hdf5Writer::AddGenomicDataset(GenomicDataset& genomic_dataset) {
  for (std::pair<const std::string, Hdf5Dataset*> chrom: genomic_dataset.chromosomes()) {
    AddDataset(*chrom.second);
  }
}

void Hdf5Writer::SetSumX(const std::string name, const double sumX) {
  std::string attr_name = "sumX";
  H5LTset_attribute_double(file_id_, name.c_str(), attr_name.c_str(), &sumX, 1);
}

void Hdf5Writer::SetSumXX(const std::string name, const double sumXX) {
  std::string attr_name = "sumXX";
  H5LTset_attribute_double(file_id_, name.c_str(), attr_name.c_str(), &sumXX, 1);
}

void Hdf5Writer::SetSignal(const std::string name, const std::string signal_filename) {
  std::string attr_name = "signal_filename";
  H5LTset_attribute_string(file_id_, name.c_str(), attr_name.c_str(), signal_filename.c_str());
}

void Hdf5Writer::SetChromSizes(const std::string name, const std::string chrom_sizes_filename) {
  std::string attr_name = "chrom_sizes_filename";
  H5LTset_attribute_string(file_id_, name.c_str(), attr_name.c_str(), chrom_sizes_filename.c_str());
}

void Hdf5Writer::SetBin(const std::string name, const int bin) {
  std::string attr_name = "bin";
  H5LTset_attribute_int(file_id_, name.c_str(), attr_name.c_str(), &bin, 1);
}

void Hdf5Writer::SetInclude(const std::string name, const std::string include_filename) {
  std::string attr_name = "include_filename";
  H5LTset_attribute_string(file_id_, name.c_str(), attr_name.c_str(), include_filename.c_str());
}

void Hdf5Writer::SetExclude(const std::string name, const std::string exclude_filename) {
  std::string attr_name = "exclude_filename";
  H5LTset_attribute_string(file_id_, name.c_str(), attr_name.c_str(), exclude_filename.c_str());
}

hid_t Hdf5Writer::Open() {
  hid_t file_id;
  file_id = H5Fopen(file_path_.c_str(), H5F_ACC_RDWR, H5P_DEFAULT);
  return file_id;
}

hid_t Hdf5Writer::Create() {
  hid_t file_id;
  file_id = H5Fcreate(file_path_.c_str(),
                      H5F_ACC_TRUNC,
                      H5P_DEFAULT,
                      H5P_DEFAULT);
  return file_id;
}

void Hdf5Writer::Close() {
  H5Fclose(file_id_);
}

void Hdf5Writer::CreateGroup(const std::string& file_name) {
  H5Gcreate1(file_id_, file_name.c_str(), 24);
}

hid_t Hdf5Writer::IsValid(const std::string& path) {
  return H5LTpath_valid (file_id_, path.c_str(), true);
}

bool FileExists(const std::string& file_path) {
  return std::ifstream(file_path.c_str()).good();
}

std::pair<std::string, std::string> SplitPath(std::string& path) {
  size_t last_slash = path.find_last_of("/");
  if (last_slash == std::string::npos) {throw;}
  std::string first = path.substr(0, last_slash);
  std::string second = path.substr(last_slash);
  return make_pair(first, second);
}
