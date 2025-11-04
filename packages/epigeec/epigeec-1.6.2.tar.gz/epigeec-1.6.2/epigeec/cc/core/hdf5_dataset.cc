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

#include <string>
#include <math.h>
#include <cmath>
#include <utility>
#include <numeric>
#include <iostream>
#include <vector>
#include "hdf5_dataset.h"

Hdf5Dataset::Hdf5Dataset(const std::string& name, int size, int bin) {
  name_ = name;
  bin_ = bin;
  //  initialise content vector based on the genome size and bin
  int content_size;
  content_size = ceil(size / bin_)+1;
  content_.resize(content_size);
  size_ = content_size;
}

Hdf5Dataset::Hdf5Dataset(const std::string& name,
                         const std::vector<float>& content,
                         int bin) {
  name_ = name;
  content_ = content;
  size_ = content.size();
  bin_ = bin;
  UpdateSum();
}

Hdf5Dataset::Hdf5Dataset(const std::string& name,
                         const std::vector<float>& content,
                         int bin,
                         double sumX,
                         double sumXX) {
  name_ = name;
  content_ = content;
  size_ = content.size();
  bin_ = bin;
  sumX_ = sumX;
  sumXX_ = sumXX;
}

void Hdf5Dataset::FeedDataLine(const GenomicDataLine& token) {
  int start_bin, end_bin;
  start_bin = token.start_position() / bin_;
  end_bin = token.end_position() / bin_;
  if (start_bin == end_bin) {
    content_[start_bin] += token.score() *
                           (token.end_position() - token.start_position());
  } else {
    content_[start_bin] += token.score() *
                           (bin_ - token.start_position() % bin_);
    content_[end_bin] += token.score() * (token.end_position() % bin_);
    for (int i = start_bin+1; i < end_bin; ++i) {
      content_[i] += token.score() * bin_;
    }
  }
}

void Hdf5Dataset::NormaliseContent() {
  sumX_ = 0;
  sumXX_ = 0;
  int last_index = content_.size()-1;
  for (int i = 0; i < last_index; ++i) {
    content_[i] /= bin_;
    sumX_ += content_[i];
    sumXX_ += content_[i] * content_[i];
  }
  content_[last_index] /= bin_;
  sumX_ += content_[last_index];
  sumXX_ += content_[last_index] * content_[last_index];
}

void Hdf5Dataset::UpdateSum() {
  double new_sumX = 0;
  double new_sumXX = 0;
  for (unsigned int i = 0; i < size_; ++i) {
    new_sumX += content_[i];
    new_sumXX += content_[i] * content_[i];
  }
  sumX_ = new_sumX;
  sumXX_ = new_sumXX;
}

void Hdf5Dataset::ToZScore() {
  content_ = zscore(content_);
}

std::vector<float>& Hdf5Dataset::GetContent() {
  return content_;
}

std::string to_string(const std::vector<float> &v) {
  std::string s = "[";
  for (float d : v) {
    s += std::to_string(d) + ", ";
  }
  s += "]";
  return s;
}

std::vector<float>& zscore(std::vector<float> &v) {
    float stdev = 0;
    float mean = 0;
    size_t n = v.size();
    mean = std::accumulate(v.begin(), v.end(), mean);
    mean = mean / n;
    for (unsigned int i = 0; i < n ; ++i) {
        v[i] -= mean;
        stdev += pow(v[i], 2.0);
    }
    stdev /= n;
    stdev = pow(stdev, 0.5);
    if (stdev == 0) {
      for (unsigned int i = 0; i < n ; ++i) {
        v[i] = 0;
      }
    } else {
      for (unsigned int i = 0; i < n ; ++i) {
        v[i] /= stdev;
      }
    }
    return v;
}

double Hdf5Dataset::GetPearson(Hdf5Dataset& hdf5_dataset) {
  //TODO: find out why the sumXX and sumYY in the hdf5 are sometimes wrong
  //assert(size_ == hdf5_dataset.size());
  if (!(size_ == hdf5_dataset.size())) {
    throw std::runtime_error("Attemping to correlate vectors of different lenghts");
  }
  std::vector<float>& v1 = content_;
  std::vector<float>& v2 = hdf5_dataset.GetContent();

  double sumXY = 0;

  //float sumX = sumX_;
  double sumX = sumX_;
  double sumXX = sumXX_;

  //float sumY = hdf5_dataset.sumX();
  double sumY = hdf5_dataset.sumX();
  double sumYY = hdf5_dataset.sumXX();

  double r;

  for (unsigned int i = 0; i < size_; ++i) {
    sumXY += v1[i] * v2[i];
    //sumXX += v1[i] * v1[i];
    //sumYY += v2[i] * v2[i];
    //sumX += v1[i];
    //sumY += v2[i];
  }

  double num = sumXY - (sumX * sumY / size_);
  double denum = (sumXX - pow(sumX, 2) / size_) * (sumYY - pow(sumY, 2) / size_);
  r = num / pow(denum, 0.5);
  return r;
}

PartialResult Hdf5Dataset::GetPartialPearson(Hdf5Dataset& hdf5_dataset) {
  if (!(size_ == hdf5_dataset.size())) {
    throw std::runtime_error("Attemping to correlate vectors of different lenghts");
  }
  PartialResult results = PartialResult();

  std::vector<float>& v1 = content_;
  std::vector<float>& v2 = hdf5_dataset.GetContent();

  for (unsigned int i = 0; i < size_; ++i) {
    results.sumXY += v1[i] * v2[i];
    results.sumXX += v1[i] * v1[i];
    results.sumYY += v2[i] * v2[i];
    results.sumX += v1[i];
    results.sumY += v2[i];
  }
  results.size = size_;
  return results;
}


void Hdf5Dataset::print() const {
  for (float i : content_) {
    std::cout<< i<< ", ";
  }
  std::cout<< std::endl;
}
