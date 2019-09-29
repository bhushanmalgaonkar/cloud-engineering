#ifndef MEMCACHE_STORE_H
#define MEMCACHE_STORE_H

#include <string>

/**
 * Repository of key-value pairs.
 * Also takes care of persisting data on the file system
 **/
class MemcacheStore {
   public:
    MemcacheStore() {}
    std::string set(std::string key, int flags, long exp_time,
                    std::string value);
};

#endif