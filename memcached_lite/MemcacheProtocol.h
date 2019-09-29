#ifndef MEMCACHE_PROTOCOL_H
#define MEMCACHE_PROTOCOL_H

#include "MemcacheExchange.h"
#include "MemcacheAbstractCommand.h"

class MemcacheProtocol {
    // parses MemcacheExchange object and return appropriate concrete
    // object of MemcacheCommand
    static MemcacheAbstractCommand* resolve(MemcacheExchange exchange);
   public:
    // Indefinitely reads input from the input socket, and calls appropriate
    // function to execute the command Exits when clients sent CMD_QUIT
    static void* serve_client(void* args);
};

#endif