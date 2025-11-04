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
#include "genomic_file_reader_factory.h"
#include "bedgraph_reader.h"
#include "bigwig_reader.h"
#include "bed_reader.h"

enum FileTypeId {
  bw,
  bg,
  bd,
  none
};

FileTypeId file_type_to_id(const std::string& file_type) {
    if (file_type == ".bw" || file_type == ".bigWig" || file_type == ".bigwig") return bw;
    if (file_type == ".bg" || file_type == ".bedGraph" || file_type == ".bedgraph") return bg;
    if (file_type == ".bd" || file_type == ".bed") return bd;
    return bw;
}

GenomicFileReader* GenomicFileReaderFactory::createGenomicFileReader(
    const std::string& file_path,
    const std::string& file_type,
    const ChromSize& chrom_size) {
  GenomicFileReader* file_reader = NULL;
  switch (file_type_to_id(file_type)) {
    case bg:
      file_reader = new BedGraphReader(file_path, chrom_size);
        break;
    case bw:
      file_reader = new BigWigReader(file_path, chrom_size);
        break;
    case bd:
      file_reader = new BedReader(file_path, chrom_size);
        break;
    default:
      std::cout<< "Unknown file type: "<< file_type<< std::endl;
  }
  return file_reader;
}
