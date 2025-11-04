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

#ifndef INPUT_LIST_H
#define INPUT_LIST_H

#include <map>
#include <utility>
#include <string>
#include <vector>

class InputList {
 public:
  InputList();
  explicit InputList(const std::string& file_path);
  ~InputList() {}
  std::pair<std::string, std::string> operator[](const int index);
  size_t size();
  int get_index(std::string& s){
    return index_map_[s];
  };
 private:
  std::vector<std::pair<std::string, std::string>> files_;
  std::map<std::string, int> index_map_;
};

#endif  // INPUT_LIST_H
