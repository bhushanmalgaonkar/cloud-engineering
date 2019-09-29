#include <string>

#include "MemcacheGetCommand.h"

MemcacheExchange MemcacheGetCommand::execute(MemcacheStore store,
                                             MemcacheExchange input) {
    std::string key = input.args[0];

    // remove trailing \r\n if any
    if (key.length() > 2 && std::string("\r\n").compare(key.substr(
                                key.length() - 2, key.length())) == 0) {
        key = key.substr(0, key.length() - 2);
    }

    std::string value = store.get(key);

    size_t idx, pidx = 0;
    bool corrupt = false;
    MemcacheExchange output;
    if (!value.empty()) {
        output.command = "VALUE";
        output.args.push_back(key);

        // flags
        idx = value.find(' ');
        if (idx == std::string::npos)
            corrupt = true;
        output.args.push_back(value.substr(pidx, idx - pidx));        

        // ignore expiration time
        pidx = idx + 1;
        idx = value.find(' ', pidx);
        if (idx == std::string::npos)
            corrupt = true;

        // size
        pidx = idx + 1;
        idx = value.find(' ', pidx);
        if (idx == std::string::npos)
            corrupt = true;
        output.args.push_back(value.substr(pidx, idx - pidx));        

        // value        
        pidx = idx + 1;
        idx = value.find(' ', pidx);
        if (idx == std::string::npos)
            corrupt = true;
        output.value = value.substr(pidx);
        output.value.append("\r\n");
    }
    output.value += "END\r\n";
    return output;
}