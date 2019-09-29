#include "MemcacheGetCommand.h"

MemcacheExchange MemcacheGetCommand::execute(MemcacheExchange input) {
    MemcacheExchange output;
    output.value = "got it!!\r\n";
    return output;
}