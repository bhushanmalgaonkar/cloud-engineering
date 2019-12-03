#ifndef MEMCACHE_GET_COMMAND_H
#define MEMCACHE_GET_COMMAND_H

#include "MemcacheAbstractCommand.h"

/**
 *
 **/
class MemcacheGetCommand : public MemcacheAbstractCommand {
   public:
    MemcacheExchange execute(MemcacheStore store, MemcacheExchange input) override; 
};

#endif