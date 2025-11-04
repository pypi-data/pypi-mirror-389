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

#ifndef BIGWIG_READER_H
#define BIGWIG_READER_H

#include <string>
#include "BBFileReader.h"
#include "genomic_file_reader.h"

class BigWigReader: public GenomicFileReader {
 public:
  BigWigReader(const std::string& file_path, const ChromSize& chrom_size);
  ~BigWigReader() {delete bigwig_;}
  void SeekChr(const std::string& chromosome);
  bool NextToken(GenomicDataLine&);
 private:
  BBFileReader* bigwig_;
  BigWigIterator bigwig_it_;
  void OpenStream();
};

#endif  // BIGWIG_READER_H
