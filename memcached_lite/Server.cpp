#include <netinet/in.h>
#include <pthread.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>
#include <algorithm>
#include <chrono>
#include <iostream>
#include <iterator>
#include <sstream>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#include "Constants.h"
#include "MemcacheStore.h"
#include "ConnectionArgs.h"
#include "MemcacheExchange.h"

using namespace std;
using namespace std::chrono;

class Value {
    std::string data;

    /**
     * unix-timestamp for expiration time (milliseconds)
     **/
    long long exp_time;

    /**
     * client specific flags, server does not care the value
     **/
    int flags;

    /**
     * number of storage/modify opearation, used for cas
     **/
    int num_modify_ops = 0;

    /**
     * timestamp of last read/modify operation, used for lru
     **/
    long last_access_time;

   public:
    Value() {}
    Value(std::string data, int flags, long long exp_time) {
        this->data = data;
        this->flags = flags;

        long long ts =
            duration_cast<milliseconds>(system_clock::now().time_since_epoch())
                .count();
        if (exp_time <= EXP_TIME_LIMIT) {
            // if exp_time is less than EXP_TIME_LIMIT,
            // consider it as number of seconds from current time
            // convert exp_time from seconds to milliseconds
            this->exp_time = ts + exp_time * 1000;
        } else {
            // else treat it as unix timestamp in seconds
            this->exp_time = exp_time * 1000;
        }

        this->last_access_time = ts;
        this->num_modify_ops = 1;
    };
};

class MemcacheAbstractCommand {
   public:
    virtual MemcacheExchange execute(MemcacheExchange input) = 0;
};

/**
 * Creats a new value against the key in the map. Overwrites if the key already
 *exists
 **/
class MemcacheSetCommand : public MemcacheAbstractCommand {
   public:
    MemcacheExchange execute(MemcacheExchange input) override {
        MemcacheExchange output;
        return output;
    }
};

/**
 *
 **/
class MemcacheGetCommand : public MemcacheAbstractCommand {
   public:
    MemcacheExchange execute(MemcacheExchange input) override {
        cout << "Executing get" << endl;
        MemcacheExchange output;
        output.value = "got it!!\r\n";
        return output;
    }
};

class Socket {
    ConnectionArgs conn_args;

   public:
    Socket(ConnectionArgs args) { conn_args = args; }

    // Read message from socket of length 'length' if provided
    // If length is provided and received message is shorter, this method
    // will wait for futher message and
    // Return whole message as one std::string object
    std::string read_msg(ssize_t length = -1) {
        int client_socket = conn_args.client_socket;
        char buffer[BUFFER_SIZE + 1] = {0};

        std::string data;
        do {
            // clear buffer for next input
            memset(buffer, 0, BUFFER_SIZE + 1);

            // read command
            ssize_t bytes = read(client_socket, buffer, BUFFER_SIZE);

            // collect in one string data
            data.append(buffer, bytes);
        } while ((ssize_t)data.length() < length);

        return data;
    }

    void send_msg(std::string data) {
        int client_socket = conn_args.client_socket;
        char buffer[BUFFER_SIZE + 1] = {0};

        for (ssize_t start = 0; start < data.length(); start += BUFFER_SIZE) {
            cout << "send_msg: data.length: " << data.length() << endl;
            // clear buffer for next input
            memset(buffer, 0, BUFFER_SIZE + 1);

            cout << "start: " << start << ", len: " << (std::min(BUFFER_SIZE, (ssize_t)data.length() - start)) << endl;

            std::size_t length = data.copy(
                buffer, std::min(BUFFER_SIZE, (ssize_t)data.length() - start),
                start);

            cout << "send msg: buffer: " << buffer << endl;
            send(client_socket, buffer, length, 0);
        }
    }

    void cleanup() {
        int client_socket = conn_args.client_socket;
        close(client_socket);
    }
};

class MemcacheProtocol {
    // parses MemcacheExchange object and return appropriate concrete
    // object of MemcacheCommand
    static MemcacheAbstractCommand* resolve(MemcacheExchange exchange) {
        MemcacheAbstractCommand* command = nullptr;
        if (std::string("set").compare(exchange.command) == 0) {
            command = new MemcacheSetCommand();
        } else if (std::string("get").compare(exchange.command) == 0) {
            cout << "matched with get" << endl;
            command = new MemcacheGetCommand();
        }
        return command;
    }

   public:
    // Indefinitely reads input from the input socket, and calls appropriate
    // function to execute the command Exits when clients sent CMD_QUIT
    static void* serve_client(void* args) {
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
            cout << "command: " << memcacheExchange.command << endl;
            cout << "args: ";
            for (int i = 0; i < memcacheExchange.args.size(); ++i) {
                cout << memcacheExchange.args[i] << ", ";
            }
            cout << endl;

            if (COMMANDS_WITH_VALUES.find(memcacheExchange.command) !=
                COMMANDS_WITH_VALUES.end()) {
                // TODO: error handling
                memcacheExchange.value =
                    socket.read_msg(stoi(memcacheExchange.args[3]));
            }

            // execute command
            MemcacheAbstractCommand* command = resolve(memcacheExchange);
            if (command == nullptr) {
                cerr << GENERIC_ERROR;
                continue;
            }
            MemcacheExchange output = command->execute(memcacheExchange);
            cout << "got output: " << output.value << endl;
            cout << "str: " << output.to_str() << endl;
            socket.send_msg(output.to_str());

            delete command;
        }

        socket.cleanup();
        pthread_exit(0);
    }
};

int main(int argc, char** argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <port>\n", argv[0]);
        exit(1);
    }
    const int PORT = atoi(argv[1]);

    int server_socket;
    if ((server_socket = socket(AF_INET, SOCK_STREAM, 0)) == 0) {
        fprintf(stderr, "Socket creation failed.\n");
        exit(1);
    }

    struct sockaddr_in address;
    int address_len = sizeof(address);
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);

    if (bind(server_socket, (struct sockaddr*)&address, sizeof(address)) < 0) {
        fprintf(stderr, "Bind failed.\n");
        exit(1);
    }

    if (listen(server_socket, 10) < 0) {
        fprintf(stderr, "Listen failed.\n");
        exit(1);
    }

    while (1) {
        int client_socket;
        if ((client_socket = accept(server_socket, (struct sockaddr*)&address,
                                    (socklen_t*)&address_len)) < 0) {
            fprintf(stderr, "Accept failed.\n");
            continue;
        }

        // start a new thread for each accepted connection
        pthread_t thread_id;
        ConnectionArgs conn_args;
        conn_args.client_socket = client_socket;

        if (pthread_create(&thread_id, nullptr, MemcacheProtocol::serve_client,
                           &conn_args) == 0) {
            pthread_detach(thread_id);
        }
    }

    // cleanup
    close(server_socket);
    return 0;
}