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

#ifndef CHROM_SIZE_H
#define CHROM_SIZE_H

#include <string>
#include <map>
#include <vector>

class ChromSize {
 public:
  ChromSize();
  explicit ChromSize(const std::string&);
  ~ChromSize() {}
  int operator[](const std::string&);
  size_t count(const std::string&) const;
  std::vector<std::string> get_chrom_list() const;
 private:
  std::map<std::string, int> chrom_sizes_;
  std::vector<std::string> chrom_list_;
};

#endif  // CHROM_SIZE_H
