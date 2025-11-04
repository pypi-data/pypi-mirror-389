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

#ifndef GENOMIC_DATA_LINE_H
#define GENOMIC_DATA_LINE_H

#include <string>

class GenomicDataLine {
 public:
  GenomicDataLine() {}
  GenomicDataLine(std::string chromosome, int start_position, int end_position,
                  float score) {
    chromosome_ = chromosome;
    start_position_ = start_position;
    end_position_ = end_position;
    score_ = score;
  }
  ~GenomicDataLine() {}
  std::string display();
  std::string chromosome() const {return chromosome_;}
  int start_position() const {return start_position_;}
  int end_position() const {return end_position_;}
  float score() const {return score_;}
 private:
  std::string chromosome_;
  int start_position_;
  int end_position_;
  float score_;
};

#endif  // GENOMIC_DATA_LINE_H
