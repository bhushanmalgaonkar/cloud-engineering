#include <iostream>
#include <unordered_map>
#include <chrono>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <string.h>

// number of seconds in 30 days
#define EXP_TIME_LIMIT 2592000ll

using namespace std;
using namespace std::chrono;

class Value {
    string data;
	long long exp_time; // unix-timestamp for expiration time (milliseconds)
	int flags;
	bool valid;
	int num_set_ops = 0; // used for cas
	long last_access_time; // used for lru
public:
	Value() {}
    Value(string data, int flags, long long exp_time) {
		this->data = data;
		this->flags = flags;
		
	    long long ts = duration_cast<milliseconds>(system_clock::now()
		                            .time_since_epoch()).count();
		if (exp_time <= EXP_TIME_LIMIT) {
			// if exp_time is less than EXP_TIME_LIMIT, 
			// consider it as number of seconds from current time
            this->exp_time = ts + exp_time * 1000; // convert exp_time from seconds to milliseconds
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
    Memcache() {

	}
    string set(string key, int flags, long exp_time, string value) {
		Value val_obj(value, flags, exp_time);
		key_value_pairs[key] = val_obj;
		return "STORED";
	}
};

int main(int argc, char **argv) {
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

	int client_socket;
	if ((client_socket = accept(server_socket, (struct sockaddr*) &address, (socklen_t*) &address_len)) < 0) {
		fprintf(stderr, "Accept failed.\n");
		exit(1);
	}

	char buffer[1024] = {0};
	const char *welcome = "Welcome to Memcached-lite\n";
	send(client_socket, welcome, strlen(welcome), 0);

	while (1) {
		memset(buffer, 0, 1024);
		read(client_socket, buffer, 1024);
		fprintf(stdout, "client sent: %s, %ld\n", buffer, strlen(buffer));
		if (strncmp(buffer, "quit\r\n", strlen(buffer)) == 0) {
			close(client_socket);
			break;
		}
		send(client_socket, buffer, strlen(buffer), 0);
	}


	// cleanup
	close(server_socket);
	return 0;
}