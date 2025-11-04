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

#ifndef GENOMIC_DATASET_H
#define GENOMIC_DATASET_H

#include <iostream>
#include <map>
#include <utility>
#include <string>
#include <vector>
#include "hdf5_dataset.h"
#include "filter_bitset.h"

class GenomicDataset {
 public:
    GenomicDataset() {}
    explicit GenomicDataset(const std::string& file_name);
    ~GenomicDataset() {}
    void add_chromosome(const std::string& name,
                        Hdf5Dataset* hdf5_dataset);
    std::map<std::string, Hdf5Dataset*>& chromosomes() {return chromosomes_;}
    std::map<std::string, double> Correlate(
        GenomicDataset& genomic_dataset,
        std::vector<std::string>& chromosomes);
    float CorrelateAll(
        GenomicDataset& genomic_dataset,
        std::vector<std::string>& chromosomes);
    std::string get_name();
    std::string get_sizes();
    void filter(FilterBitset& filter) {
      for (std::pair<const std::string, Hdf5Dataset*>& chrom : chromosomes_) {
        chrom.second->filter(filter[chrom.first]);
      }
    }
 private:
     std::map<std::string, Hdf5Dataset*> chromosomes_;
     std::string file_name_;
};

#endif  // GENOMIC_DATASET_H
