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

#ifndef GENOMIC_FILE_READER_H
#define GENOMIC_FILE_READER_H

#include <fstream>
#include <string>
#include "genomic_data_line.h"
#include "chrom_size.h"

class GenomicFileReader {
 public:
  GenomicFileReader(const std::string& file_path, const ChromSize& chrom_size);
  virtual ~GenomicFileReader() {}
  virtual void SeekChr(const std::string& chromosome) = 0;
  virtual bool NextToken(GenomicDataLine&) = 0;
 protected:
  std::string file_path_;
  ChromSize chrom_size_;
  std::ifstream genomic_file_stream_;
};

#endif  // GENOMIC_FILE_READER_H
