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

#ifndef BED_READER_H
#define BED_READER_H

#include <string>
#include "genomic_file_reader.h"

class BedReader: public GenomicFileReader {
/*class used to generate tokens from a bed file
tokens contain chromosome, start, end, score

see the parent class GenomicFileReader for more information

Usage:
BedReader bed_reader = BedReader(file_path, chrom_size)
GenomicDataLine genomic_data_line;
bed_reader.SeekChr("chr1")
while(NextToken(genomic_data_line)){
    //do something with token
}

note: since entries in the bed format do not contain a score
    it is set to 1 for all tokens

IMPORTANT: the bed file MUST be ordered to use SeekChr
*/
 public:
  BedReader(const std::string& file_path, const ChromSize& chrom_size);
  ~BedReader() {}
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

#endif  // BED_READER_H
