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

#include <sstream>
#include <string>
#include "genomic_data_line.h"

std::string GenomicDataLine::display() {
    std::stringstream display_stream;
    display_stream<< chromosome_
                  << "\t"
                  << start_position_
                  << "\t"
                  << end_position_
                  << "\t"
                  << score_;
    return display_stream.str();
}
