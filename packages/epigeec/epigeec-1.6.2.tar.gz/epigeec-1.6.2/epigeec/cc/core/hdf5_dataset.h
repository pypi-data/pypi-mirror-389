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

#ifndef HDF5_DATASET_H
#define HDF5_DATASET_H

#include <iostream>
#include <sstream>
#include <vector>
#include <string>
#include <utility>
#include <boost/dynamic_bitset.hpp>
#include "genomic_data_line.h"

struct PartialResult {
  float sumX = 0;
  float sumXX = 0;
  float sumY = 0;
  float sumYY = 0;
  float sumXY = 0;
  int size = 0;
  struct PartialResult& operator+=(const PartialResult rhs){
    this->sumX += rhs.sumX;
    this->sumXX += rhs.sumXX;
    this->sumY += rhs.sumY;
    this->sumYY += rhs.sumYY;
    this->sumXY += rhs.sumXY;
    this->size += rhs.size;
    return *this;
  }
};

class Hdf5Dataset {
 public:
  Hdf5Dataset(const std::string& name, int size, int bin);
  Hdf5Dataset(const std::string& name,
              const std::vector<float>& content,
              int bin);
  Hdf5Dataset(const std::string& name,
              const std::vector<float>& content,
              int bin, double sumX, double sumXX);
  ~Hdf5Dataset() {}
  void FeedDataLine(const GenomicDataLine& token);
  std::string name() {return name_;}
  unsigned int size() {return size_;}
  double sumX() {return sumX_;}
  double sumXX() {return sumXX_;}
  void NormaliseContent();
  void ToZScore();
  void UpdateSum();
  void filter(const boost::dynamic_bitset<>& filter) {
    if (filter.size() != size_) {
         std::stringstream error_msg; 
         error_msg << "Filter size not same as dataset, filter_size = " << filter.size() << ", dataset_size = " << size_;
         throw std::runtime_error(error_msg.str());
    }
    std::vector<float> new_content;
    double new_sumX = 0;
    double new_sumXX = 0;
    for (unsigned int i = 0; i < size_; ++i) {
      if (filter[i]){
        new_content.push_back(content_[i]);
        new_sumX += content_[i];
        new_sumXX += content_[i] * content_[i];
      }
    }
    content_ = new_content;
    size_ = content_.size();
    sumX_ = new_sumX;
    sumXX_ = new_sumXX;
  }
  std::vector<float>& GetContent();
  double GetPearson(Hdf5Dataset& hdf5_dataset);
  PartialResult GetPartialPearson(Hdf5Dataset& hdf5_dataset);
  void print() const;
 private:
  std::string name_;
  unsigned int size_;
  int bin_;
  std::vector<float> content_;
  double sumX_;
  double sumXX_;
};

std::vector<float>& zscore(std::vector<float> &v);
std::string to_string(const std::vector<float> &v);

#endif  // HDF5_DATASET_H
