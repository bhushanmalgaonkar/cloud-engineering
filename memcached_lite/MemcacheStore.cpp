#include <string>

#include <experimental/filesystem>
#include <fstream>
#include <iostream>

#include "MemcacheStore.h"

bool MemcacheStore::init(std::string path) {
    if (!std::experimental::filesystem::exists(path)) {
        if (!std::experimental::filesystem::create_directories(path)) {
            return false;
        }
    }
    this->path = path;
    return true;
}

std::string MemcacheStore::set(std::string key, int flags, long exp_time,
                               int size, std::string value) {
    std::ofstream file;
    file.open(path + "/" + key, std::fstream::out);
    file << flags << " " << exp_time << " " << size << " " << value;
    file.close();
}

std::string MemcacheStore::get(std::string key) {
    std::ifstream file;
    file.open(path + "/" + key, std::fstream::in);

    std::string value, line;
    if (file.is_open()) {
        while (getline(file, line)) {
            if (!value.empty()) {
                value.append("\n");
            }
            value.append(line);
        }
    }
    return value;
}