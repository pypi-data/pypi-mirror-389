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
#include "bedgraph_reader.h"

BedGraphReader::BedGraphReader(const std::string& file_path,
                               const ChromSize& chrom_size):
                               GenomicFileReader(file_path, chrom_size) {
    OpenStream();
};

void BedGraphReader::NextChr() {
  GenomicDataLine token;
  while (!NextToken(token)) {}
  if (!genomic_file_stream_.fail()) {
    chr_ = token.chromosome();
    chrom_pos_.emplace(chr_, cursor_);
  }
}

void BedGraphReader::SeekChr(const std::string& chromosome) {
  if (cursor_ > last_pos_) {
    last_pos_ = cursor_;
  }
  if (chrom_pos_.find(chromosome) == chrom_pos_.end()) {
    genomic_file_stream_.seekg(last_pos_);
    while (chr_ != chromosome && !genomic_file_stream_.fail()) {
      NextChr();
    }
    genomic_file_stream_.seekg(cursor_);
  } else {
    cursor_ = chrom_pos_.find(chromosome)->second;
    chr_ = chromosome;
    genomic_file_stream_.clear();
    genomic_file_stream_.seekg(cursor_);
  }
}

bool BedGraphReader::NextToken(GenomicDataLine& genomic_data_line) {
  std::string chr;
  int start;
  int end;
  float score;
  cursor_ = genomic_file_stream_.tellg();
  genomic_file_stream_>> chr>> start>> end>> score;
  genomic_data_line = GenomicDataLine(chr, start, end, score);
  //std::cout<< genomic_data_line.display()<< std::endl;
  return genomic_file_stream_.fail() || chr != chr_;
}

void BedGraphReader::OpenStream() {
  genomic_file_stream_.open(file_path_.c_str(), std::ios::in);
  cursor_ = genomic_file_stream_.tellg();
  last_pos_ = cursor_;
}
