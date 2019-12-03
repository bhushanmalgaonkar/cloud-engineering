#include "MemcacheSetCommand.h"
#include "MemcacheStore.h"

#include <iostream>

MemcacheExchange MemcacheSetCommand::execute(MemcacheStore store, MemcacheExchange input) {
    store.set(input.args[0], stoi(input.args[1]), stoi(input.args[2]), stoi(input.args[3]), input.value);

    MemcacheExchange output;
    output.value = "STORED\n";
    return output;
}