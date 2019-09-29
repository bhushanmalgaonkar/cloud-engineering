#include <sstream>
#include <iostream>
#include <pthread.h>

#include "Socket.h"
#include "Constants.h"
#include "ConnectionArgs.h"
#include "MemcacheAbstractCommand.h"
#include "MemcacheGetCommand.h"
#include "MemcacheSetCommand.h"
#include "MemcacheProtocol.h"

MemcacheAbstractCommand* MemcacheProtocol::resolve(MemcacheExchange exchange) {
    MemcacheAbstractCommand* command = nullptr;
    if (std::string("set").compare(exchange.command) == 0) {
        command = new MemcacheSetCommand();
    } else if (std::string("get").compare(exchange.command) == 0) {
        command = new MemcacheGetCommand();
    }
    return command;
}

void* MemcacheProtocol::serve_client(void* args) {
    ConnectionArgs conn_args = *(ConnectionArgs*)args;
    Socket socket(conn_args);

    // send welcome message
    socket.send_msg(WELCOME_MESSAGE);

    while (1) {
        std::string command_str = socket.read_msg();

        // close the connection and exit the thread if client sends CMD_QUIT
        if (CMD_QUIT.compare(command_str) == 0) {
            break;
        }

        MemcacheExchange memcacheExchange;
        std::stringstream ss(command_str);
        std::string token;

        std::getline(ss, token, ' ');
        memcacheExchange.command = token;
        while (std::getline(ss, token, ' ')) {
            memcacheExchange.args.push_back(token);
        }
        std::cout << "command: " << memcacheExchange.command << std::endl;
        std::cout << "args: ";
        for (int i = 0; i < memcacheExchange.args.size(); ++i) {
            std::cout << memcacheExchange.args[i] << ", ";
        }
        std::cout << std::endl;

        if (COMMANDS_WITH_VALUES.find(memcacheExchange.command) !=
            COMMANDS_WITH_VALUES.end()) {
            // TODO: error handling
            memcacheExchange.value =
                socket.read_msg(stoi(memcacheExchange.args[3]));
        }

        // execute command
        MemcacheAbstractCommand* command = resolve(memcacheExchange);
        if (command == nullptr) {
            std::cerr << GENERIC_ERROR;
            continue;
        }
        MemcacheExchange output = command->execute(memcacheExchange);
        std::cout << "got output: " << output.value << std::endl;
        std::cout << "str: " << output.to_str() << std::endl;
        socket.send_msg(output.to_str());

        delete command;
    }

    socket.cleanup();
    pthread_exit(0);
}