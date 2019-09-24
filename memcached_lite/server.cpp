#include <netinet/in.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>
#include <chrono>
#include <iostream>
#include <unordered_map>
#include <pthread.h>

// number of seconds in 30 days
#define EXP_TIME_LIMIT 2592000ll
#define CMD_QUIT "quit\r\n"

const char* welcome = "Welcome to Memcached-lite\n";

using namespace std;
using namespace std::chrono;

class Value {
    string data;
    long long exp_time;  // unix-timestamp for expiration time (milliseconds)
    int flags;
    bool valid;
    int num_set_ops = 0;    // used for cas
    long last_access_time;  // used for lru
   public:
    Value() {}
    Value(string data, int flags, long long exp_time) {
        this->data = data;
        this->flags = flags;

        long long ts =
            duration_cast<milliseconds>(system_clock::now().time_since_epoch())
                .count();
        if (exp_time <= EXP_TIME_LIMIT) {
            // if exp_time is less than EXP_TIME_LIMIT,
            // consider it as number of seconds from current time
            this->exp_time =
                ts + exp_time *
                         1000;  // convert exp_time from seconds to milliseconds
        } else {
            // else treat it as unix timestamp in seconds
            this->exp_time = exp_time * 1000;
        }

        this->last_access_time = ts;
        this->num_set_ops = 1;
    };
};

class Memcache {
    unordered_map<string, Value> key_value_pairs;

   public:
    Memcache() {}
    string set(string key, int flags, long exp_time, string value) {
        Value val_obj(value, flags, exp_time);
        key_value_pairs[key] = val_obj;
        return "STORED";
    }
};

// structure that stores parameters to be passed while starting new thread
// for new client, allows to add new parameters easily 
struct ConnectionArgs {
	int client_socket;
};

// indefinitely reads input from the input socket, and echoes back
// exits when clients sent CMD_QUIT
void* serve_client(void* args) {
	ConnectionArgs* conn_args = (ConnectionArgs*) args;
	int client_socket = conn_args->client_socket;
	
	char buffer[1024] = {0};
    send(client_socket, welcome, strlen(welcome), 0);

    while (1) {
		// clear buffer for next input
		memset(buffer, 0, 1024);

        read(client_socket, buffer, 1024);
        
		// close the connection and exit the thread if client sends CMD_QUIT
		fprintf(stdout, "client sent: %s, %ld\n", buffer, strlen(buffer));
        if (strncmp(buffer, CMD_QUIT, strlen(buffer)) == 0) {
			break;
        }

        send(client_socket, buffer, strlen(buffer), 0);
    }

	fprintf(stdout, "Closing socket %d\n", client_socket);
	close(client_socket);
	pthread_exit(0);
}

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

		pthread_create(&thread_id, nullptr, serve_client, &conn_args);
	}

    // cleanup
    close(server_socket);
    return 0;
}