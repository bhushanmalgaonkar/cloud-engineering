#ifndef MEMCACHE_SET_COMMAND_H
#define MEMCACHE_SET_COMMAND_H

#include "MemcacheAbstractCommand.h"

/**
 * Creats a new value against the key in the map. Overwrites if the key already
 *exists
 **/
class MemcacheSetCommand : public MemcacheAbstractCommand {
   public:
    MemcacheExchange execute(MemcacheExchange input) override;
};

#endif