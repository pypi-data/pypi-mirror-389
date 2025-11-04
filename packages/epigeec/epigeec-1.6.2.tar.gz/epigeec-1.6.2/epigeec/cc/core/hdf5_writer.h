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

#ifndef HDF5_WRITER_H
#define HDF5_WRITER_H

#include <vector>
#include "hdf5.h"
#include "hdf5_dataset.h"
#include "genomic_dataset.h"

class Hdf5Writer {
 public:
  explicit Hdf5Writer(const std::string& file_path);
  ~Hdf5Writer() {Close();}
  void AddDataset(const std::string& name,
              hsize_t size,
              const std::vector<float>& data);
  void AddDataset(Hdf5Dataset& hdf5_dataset);
  void AddGenomicDataset(GenomicDataset& genomic_dataset);
  void SetSumX(const std::string name, double sumX);
  void SetSumXX(const std::string name, double sumXX);
  void SetSignal(const std::string name, const std::string signal_path);
  void SetChromSizes(const std::string name, const std::string chrom_sizes_path);
  void SetBin(const std::string name, const int bin);
  void SetInclude(const std::string name, const std::string include_path);
  void SetExclude(const std::string name, const std::string exclude_path);
  hid_t IsValid(const std::string& path);
 private:
  hid_t Open();
  hid_t Create();
  void Close();
  void CreateGroup(const std::string& file_name);
  std::string file_path_;
  hid_t file_id_;
};

bool FileExists(const std::string& file_path);
std::pair<std::string, std::string> SplitPath(std::string& path);

#endif  // HDF5_WRITER_H
