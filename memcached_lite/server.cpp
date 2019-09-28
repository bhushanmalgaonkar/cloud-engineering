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

/**
 * Number of seconds in 30 days
 * This value is used to distinguish between relative/absolute
 * expiration time. If the expiration time specified by client
 * is less than EXP_TIME_LIMIT, expiration time is set as number
 * of seconds starting from current time, else it is set to unix
 * timestamp as it is.
 **/
#define EXP_TIME_LIMIT 2592000ll

/**
 * Command that client sends to tell server not to send the result of
 * store operation
 **/
#define CMD_NO_REPLY "noreply\r\n"

/**
 * Buffer size used to send/receive data to/from socket
 **/
ssize_t BUFFER_SIZE = 1024;

/**
 * Message sent to newly connected client
 **/
const char* WELCOME_MESSAGE = "Welcome to Memcached-lite\n";

/**
 * Command that client sends to terminate the connection with server
 **/
std::string CMD_QUIT = "quit\r\n";

/**
 * Set of commands that require value parameter (2nd line)
 **/
std::unordered_set<std::string> COMMANDS_WITH_VALUES = {"set"};

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

/**
 * Repository of key-value pairs.
 * Also takes care of persisting data on the file system
 **/
class MemcacheStore {
    std::unordered_map<std::string, Value> key_value_pairs;

   public:
    MemcacheStore() {}
    std::string set(std::string key, int flags, long exp_time,
                    std::string value) {
        Value val_obj(value, flags, exp_time);
        key_value_pairs[key] = val_obj;
        return "STORED";
    }
};

/**
 * Data structure to hold entire command/reponse of Memcache protocol
 **/
struct MemcacheExchange {
    std::string command;
    std::string value;
};

class MemcacheAbstractCommand {
   protected:
    MemcacheExchange data;

   public:
    virtual void parse(std::string command);
    virtual MemcacheExchange execute();
};

/**
 * Creats a new value against the key in the map. Overwrites if the key already
 *exists
 **/
class MemcacheSetCommand : public MemcacheAbstractCommand {
   public:
    void parse(std::string command) {}
    MemcacheExchange execute();
};

/**
 *
 **/
class MemcacheGetCommand : public MemcacheAbstractCommand {
   public:
    void parse(std::string command) {}
    MemcacheExchange execute();
};

class Memcache {};

/**
 * Structure that stores parameters to be passed while starting new thread
 * for new client, allows to add new parameters easily
 **/
struct ConnectionArgs {
    int client_socket;
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
        char buffer[BUFFER_SIZE] = {0};

        std::string data;
        do {
            // clear buffer for next input
            memset(buffer, 0, BUFFER_SIZE);

            // read command
            ssize_t bytes = read(client_socket, buffer, BUFFER_SIZE);

            // collect in one string data
            data.append(buffer, bytes);
        } while ((ssize_t)data.length() < length);

        return data;
    }

    void send_msg(std::string data) {
        int client_socket = conn_args.client_socket;
        char buffer[BUFFER_SIZE] = {0};

        for (size_t start = 0; start < data.length(); start += BUFFER_SIZE) {
            std::size_t length = data.copy(
                buffer, start,
                std::min(BUFFER_SIZE, (ssize_t)data.length()) - start);
            send(client_socket, buffer, length, 0);
        }
    }

    void cleanup() {
        int client_socket = conn_args.client_socket;

        cout << "Closing socket: " << client_socket << std::endl;
        close(client_socket);
    }
};

class MemcacheProtocol {
   public:
    // Indefinitely reads input from the input socket, and calls appropriate
    // function to execute the command Exits when clients sent CMD_QUIT
    static void* serve_client(void* args) {
        ConnectionArgs conn_args = *(ConnectionArgs*)args;
        Socket socket(conn_args);

        // send welcome message
        socket.send_msg(WELCOME_MESSAGE);

        while (1) {
            std::string command = socket.read_msg();

            // close the connection and exit the thread if client sends CMD_QUIT
            cout << "client sent: " << command << " of length "
                 << command.length() << std::endl;
            if (CMD_QUIT.compare(command) == 0) {
                break;
            }

            MemcacheExchange memcacheExchange;
            memcacheExchange.command = command;

            // check if command requires more input (set commands)
            std::vector<std::string> tokens;
            std::istringstream iss(command);
            std::copy(std::istream_iterator<std::string>(iss),
                      std::istream_iterator<std::string>(),
                      std::back_inserter(tokens));

            if (COMMANDS_WITH_VALUES.find(tokens[0]) !=
                COMMANDS_WITH_VALUES.end()) {
                // TODO: error handling
                memcacheExchange.value = socket.read_msg(stoi(tokens[4]));
            }

            // call MemcacheStore::set/MemcacheStore::get

            // write result to buffer
            // send buffer
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