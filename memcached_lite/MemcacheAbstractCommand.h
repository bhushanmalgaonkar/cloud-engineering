#ifndef MEMCACHE_ABSTRACT_COMMAND_H
#define MEMCACHE_ABSTRACT_COMMAND_H

#include "MemcacheStore.h"
#include "MemcacheExchange.h"

class MemcacheAbstractCommand {
   public:
    virtual MemcacheExchange execute(MemcacheStore store, MemcacheExchange input) = 0;
};

#endif