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

#ifndef BEDGRAPH_READER_H
#define BEDGRAPH_READER_H

#include <string>
#include <map>
#include "genomic_file_reader.h"

class BedGraphReader: public GenomicFileReader {
 public:
  BedGraphReader(const std::string& file_path, const ChromSize& chrom_size);
  ~BedGraphReader() {}
  void SeekChr(const std::string& chromosome);
  bool NextToken(GenomicDataLine&);
 private:
  void NextChr();
  void OpenStream();
  std::string chr_;
  std::streampos cursor_;
  std::streampos last_pos_;
  std::map<std::string, std::streampos> chrom_pos_;
};

#endif  // BEDGRAPH_READER_H
