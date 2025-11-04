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

#ifndef HDF5_READER_H
#define HDF5_READER_H

#include "hdf5.h"
#include "hdf5_dataset.h"
#include "genomic_dataset.h"
#include <string>

class Hdf5Reader {
 public:
  explicit Hdf5Reader(const std::string& file_path);
  ~Hdf5Reader() {Close();}
  Hdf5Dataset* GetDataset(std::string& name, int bin);
  GenomicDataset* GetGenomicDataset(std::string& name, std::vector<std::string> chroms, int bin);
  double GetSumX(const std::string& name);
  double GetSumXX(const std::string& name);
  std::string GetSignal();
  bool IsValid(const std::string& path);
 private:
  hid_t Open();
  void Close();
  std::string file_path_;
  hid_t file_id_;
};

#endif  // HDF5_READER_H
