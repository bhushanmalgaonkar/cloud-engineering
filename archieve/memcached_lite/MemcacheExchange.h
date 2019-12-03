#ifndef MEMCACHE_EXCHANGE_H
#define MEMCACHE_EXCHANGE_H

#include <string>
#include <vector>

/**
 * Data structure to hold entire command/reponse of Memcache protocol
 **/
struct MemcacheExchange {
    std::string command;
    std::vector<std::string> args;
    std::string value;

    std::string to_str();
};

#endif