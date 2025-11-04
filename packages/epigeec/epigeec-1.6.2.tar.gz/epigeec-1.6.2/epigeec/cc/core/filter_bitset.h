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

#ifndef FILTER_BITSET_H
#define FILTER_BITSET_H

#include <iostream>
#include <math.h>
#include <utility>
#include <boost/dynamic_bitset.hpp>
#include "chrom_size.h"
#include "genomic_file_reader.h"

#define BOOST_DYNAMIC_BITSET_DONT_USE_FRIENDS

class FilterBitset {
 public:
    FilterBitset() {};
    FilterBitset(ChromSize& chrom_size, int bin, GenomicFileReader& genomic_file_reader) {
        bin_ = bin;
        std::vector<std::string> chrom_list = chrom_size.get_chrom_list();
        for (std::string& chrom : chrom_list) {
            int size = ceil(chrom_size[chrom] / bin)+1;
            boost::dynamic_bitset<> filter(size);

            GenomicDataLine token;
            genomic_file_reader.SeekChr(chrom);
            while (!genomic_file_reader.NextToken(token)) {
              feed_data_line(filter, token, chrom);
            }
            content_.emplace(chrom, filter);
        }
    };
    ~FilterBitset() {};
    boost::dynamic_bitset<>& operator[](const std::string& chrom){return content_[chrom];}
    const boost::dynamic_bitset<>& at(const std::string& chrom) const {return content_.at(chrom);}
    void feed_data_line(boost::dynamic_bitset<>& filter, const GenomicDataLine& token, const std::string& chrom) {
        int start_bin, end_bin;
        start_bin = token.start_position() / bin_;
        end_bin = (token.end_position() - 1) / bin_;  // Last base actually in the interval
        for (int i = start_bin; i <= end_bin; ++i) {
            filter.set(i);
        }
    }
    FilterBitset operator~();
    FilterBitset operator&(const FilterBitset &b);
    unsigned int size() {return content_.size();}
    std::map<std::string, boost::dynamic_bitset<>>& content() {return content_;}
 private:
    std::map<std::string, boost::dynamic_bitset<>> content_;
    int bin_;
};

#endif  // FILTER_BITSET_H
