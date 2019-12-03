#ifndef MEMCACHE_STORE_H
#define MEMCACHE_STORE_H

#include <string>

/**
 * Repository of key-value pairs.
 * Also takes care of persisting data on the file system
 **/
class MemcacheStore {
    std::string path;
   public:
    bool init(std::string path);
    std::string set(std::string key, int flags, long exp_time,
                    int size, std::string value);
    std::string get(std::string key);
};

#endif