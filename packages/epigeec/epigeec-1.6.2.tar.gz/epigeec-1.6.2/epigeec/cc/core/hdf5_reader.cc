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
#include "hdf5_reader.h"
#include "genomic_dataset.h"
#include "hdf5_hl.h"

Hdf5Reader::Hdf5Reader(const std::string& file_path) {
  file_path_ = file_path;
  file_id_ = Open();
}

Hdf5Dataset* Hdf5Reader::GetDataset(std::string& name, int bin) {
  // get dimensions
  hsize_t dims = 0;
  H5T_class_t class_id;
  size_t type_size = 0;
  H5LTget_dataset_info(file_id_, name.c_str(), &dims, &class_id, &type_size);
  // get data
  std::vector<float> data;
  data.reserve(dims);
  data.resize(dims);
  int check = H5LTread_dataset_float(file_id_, name.c_str(), &data[0]);
  Hdf5Dataset* hdf5_dataset = new Hdf5Dataset(name, data, bin, GetSumX(name), GetSumXX(name));
  return hdf5_dataset;
}

GenomicDataset* Hdf5Reader::GetGenomicDataset(std::string& name, std::vector<std::string> chroms, int bin) {
  GenomicDataset* data = new GenomicDataset(name);
  for (std::string chrom : chroms) {
    std::string path = name + "/" + chrom;
    //std::cout<< path<< std::endl;
    Hdf5Dataset* dataset = GetDataset(path, bin);
    data->add_chromosome(chrom, dataset);
  }
  return data;
}

double Hdf5Reader::GetSumX(const std::string& name) {
  double sumX = 0;
  std::string attr_name = "sumX";
  H5LTget_attribute_double(file_id_, name.c_str(), attr_name.c_str(), &sumX);
  //std::cout<< "sumX: " << sumX<< std::endl;
  return sumX;
}

double Hdf5Reader::GetSumXX(const std::string& name) {
  double sumXX = 0;
  std::string attr_name = "sumXX";
  H5LTget_attribute_double(file_id_, name.c_str(), attr_name.c_str(), &sumXX);
  return sumXX;
}

std::string Hdf5Reader::GetSignal() {
  std::string attr_name = "signal_filename";
  std::string value;
  hsize_t dims = 0; 
  H5T_class_t type_class;
  size_t type_size = 0;
  H5LTget_attribute_info(file_id_, "/", attr_name.c_str(), &dims, &type_class, &type_size);
  value.resize(type_size);
  H5LTget_attribute_string(file_id_, "/", attr_name.c_str(), &value[0]);
  value.pop_back();
  return value;
}

bool Hdf5Reader::IsValid(const std::string& path) {
  return H5LTpath_valid(file_id_, path.c_str(), false);
}

hid_t Hdf5Reader::Open() {
  hid_t file_id;
  if (!H5Fis_hdf5(file_path_.c_str())) {   
       // Invalid HDF5 file
       throw std::runtime_error("Failed to open file "+ file_path_);
  }
  file_id = H5Fopen(file_path_.c_str(), H5F_ACC_RDONLY, H5P_DEFAULT);
  return file_id;
}

void Hdf5Reader::Close() {
  H5Fclose(file_id_);
}
