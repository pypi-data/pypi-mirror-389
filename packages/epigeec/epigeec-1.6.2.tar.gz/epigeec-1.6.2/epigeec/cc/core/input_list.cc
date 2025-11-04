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

#include <utility>
#include <string>
#include <fstream>
#include <boost/filesystem.hpp>
#include "input_list.h"

InputList::InputList(const std::string& file_path) {
  std::ifstream flot(file_path);
  std::string path, name;
  int count = 0;
  bool success = 0;
  while (flot>> path) {
    name = boost::filesystem::path(path).stem().string();
    success = this->index_map_.emplace(path, count).second; // ensures no duplicates
    if (success) {
      this->files_.push_back(std::make_pair(path, name));
      ++count;
    }
  }
}

std::pair<std::string, std::string> InputList::operator[](const int index) {
  return this->files_[index];
}

size_t InputList::size() {
  return this->files_.size();
}
