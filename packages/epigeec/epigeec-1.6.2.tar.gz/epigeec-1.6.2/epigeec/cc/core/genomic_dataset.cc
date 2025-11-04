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
#include <limits>
#include <map>
#include <string>
#include <vector>
#include "genomic_dataset.h"

GenomicDataset::GenomicDataset(const std::string& file_name) {
  file_name_ = file_name;
}

void GenomicDataset::add_chromosome(const std::string& name,
                                    Hdf5Dataset* hdf5_dataset) {
  chromosomes_.emplace(name, hdf5_dataset);
  chromosomes_.find(name);
}

std::string GenomicDataset::get_name() {
  return file_name_;
}

std::string GenomicDataset::get_sizes() {
  std::string sizes = "";
  for (auto chr : chromosomes_) {
    sizes += "\t" + chr.first + ":" + std::to_string(chr.second->size());
  }
  return sizes;
}

std::map<std::string, double>  GenomicDataset::Correlate(
    GenomicDataset& genomic_dataset,
    std::vector<std::string>& chromosomes) {
  std::map<std::string, double> results;
  for (const std::string& chr : chromosomes) {
    chromosomes_.find(chr);
    if (chromosomes_.find(chr) != chromosomes_.end() &&
        genomic_dataset.chromosomes_.find(chr) !=
        genomic_dataset.chromosomes_.end()) {
      double r;
      try{
        r = chromosomes_.at(chr)->GetPearson(
        *(genomic_dataset.chromosomes().at(chr)));
      } catch (...) {
        r = 0;
      }
      results.emplace(chr, r);
    } else {
      results.emplace(chr, std::numeric_limits<double>::quiet_NaN());
    }
  }
  return results;
}

float GenomicDataset::CorrelateAll(
    GenomicDataset& genomic_dataset,
    std::vector<std::string>& chromosomes) {

  float r, num, denum;
  PartialResult results = PartialResult();

  for (const std::string& chr : chromosomes) {
    if (chromosomes_.find(chr) != chromosomes_.end() &&
        genomic_dataset.chromosomes_.find(chr) !=
        genomic_dataset.chromosomes_.end()) {
    results += chromosomes_.at(chr)->GetPartialPearson(*genomic_dataset.chromosomes().at(chr));
    }
  }
  if (results.size == 0) {
    r = std::numeric_limits<float>::quiet_NaN();
  } else {
    num = results.sumXY - (results.sumX * results.sumY / results.size);
    denum = (results.sumXX - pow(results.sumX, 2) / results.size) * (results.sumYY - pow(results.sumY, 2) / results.size);
    r = num / pow(denum, 0.5);
  }
  return r;
}
