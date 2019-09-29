#include <string>

#include "MemcacheExchange.h"

std::string MemcacheExchange::to_str() {
    std::string joined;

    joined.append(command);
    for (int i = 0; i < args.size(); ++i) {
        if (!joined.empty()) {
            joined.append(" ");
        }
        joined.append(args[i]);
    }
    if (!joined.empty()) {
        joined.append("\n");
    }
    joined.append(value);

    return joined;
}