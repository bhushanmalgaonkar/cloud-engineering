#include <string>

#include "MemcacheStore.h"

std::string MemcacheStore::set(std::string key, int flags, long exp_time,
                   std::string value) {
    return "STORED";
}