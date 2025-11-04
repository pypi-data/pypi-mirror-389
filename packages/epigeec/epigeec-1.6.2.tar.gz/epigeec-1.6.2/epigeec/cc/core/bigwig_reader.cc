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
#include "bigwig_reader.h"

BigWigReader::BigWigReader(const std::string& file_path,
                           const ChromSize& chrom_size):
                           GenomicFileReader(file_path, chrom_size) {
    OpenStream();
    bigwig_ = new BBFileReader(file_path_, genomic_file_stream_);
};

void BigWigReader::SeekChr(const std::string& chromosome) {
  bigwig_it_ = bigwig_->getBigWigIterator(chromosome,
                                          0,
                                          chromosome,
                                          chrom_size_[chromosome],
                                          false);
}

bool BigWigReader::NextToken(GenomicDataLine& genomic_data_line) {
  if (bigwig_it_.isEnd()) {return true;}
  std::string chr;
  int start;
  int end;
  float score;
  chr = (*bigwig_it_).getChromosome().c_str();
  start = (*bigwig_it_).getStartBase();
  end = (*bigwig_it_).getEndBase();
  score = (*bigwig_it_).getWigValue();
  genomic_data_line = GenomicDataLine(chr, start, end, score);
  ++bigwig_it_;
  return false;
}

void BigWigReader::OpenStream() {
    genomic_file_stream_.open(file_path_.c_str(),
                              std::ios::in | std::ios::binary);
}
