#include <pthread.h>
#include <iostream>
#include <sstream>

#include "ClientArgs.h"
#include "Constants.h"
#include "MemcacheAbstractCommand.h"
#include "MemcacheGetCommand.h"
#include "MemcacheProtocol.h"
#include "MemcacheSetCommand.h"
#include "Socket.h"

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
    ClientArgs conn_args = *(ClientArgs*)args;
    MemcacheStore store = *(conn_args.store);
    Socket socket(conn_args.client_socket);

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

        if (COMMANDS_WITH_VALUES.find(memcacheExchange.command) !=
            COMMANDS_WITH_VALUES.end()) {
            // TODO: error handling
            int len = stoi(memcacheExchange.args[3]);
            if (len > 0) {
                std::string value = socket.read_msg(len);
                if (value.empty()) {
                    socket.send_msg(CLIENT_ERROR_BAD_DATA_CHUNK);
                    continue;                
                }
                memcacheExchange.value = value;
            }
        }

        // execute command
        MemcacheAbstractCommand* command = resolve(memcacheExchange);
        if (command == nullptr) {
            socket.send_msg(GENERIC_ERROR);
            continue;
        }
        MemcacheExchange output = command->execute(store, memcacheExchange);
        socket.send_msg(output.to_str());

        delete command;
    }

    socket.cleanup();
    pthread_exit(0);
}