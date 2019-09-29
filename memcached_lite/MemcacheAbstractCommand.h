#ifndef MEMCACHE_ABSTRACT_COMMAND_H
#define MEMCACHE_ABSTRACT_COMMAND_H

#include "MemcacheExchange.h"

class MemcacheAbstractCommand {
   public:
    virtual MemcacheExchange execute(MemcacheExchange input) = 0;
};

#endif