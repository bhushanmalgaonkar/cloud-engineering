#include <netinet/in.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/socket.h>
#include <iostream>

#include "Constants.h"
#include "ClientArgs.h"
#include "MemcacheProtocol.h"

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << "<port>\n";
        exit(1);
    }
    const int PORT = atoi(argv[1]);

    int server_socket;
    if ((server_socket = socket(AF_INET, SOCK_STREAM, 0)) == 0) {
        std::cerr << "Socket creation failed.\n";
        exit(1);
    }

    struct sockaddr_in address;
    int address_len = sizeof(address);
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);

    if (bind(server_socket, (struct sockaddr*)&address, sizeof(address)) < 0) {
        std::cerr << "Bind failed.\n";
        exit(1);
    }

    if (listen(server_socket, 10) < 0) {
        std::cerr << "Listen failed.\n";
        exit(1);
    }

    MemcacheStore store;
    if (!store.init(MEMCACHE_STORE_PATH)) {
        std::cerr << "Error creating store.\n";
        exit(1);
    }
    
    while (1) {
        int client_socket;
        if ((client_socket = accept(server_socket, (struct sockaddr*)&address,
                                    (socklen_t*)&address_len)) < 0) {
            std::cerr << "Accept failed.\n";
            continue;
        }

        // start a new thread for each accepted connection
        pthread_t thread_id;

        ClientArgs client_args;
        client_args.client_socket = client_socket;
        client_args.store = &store;

        if (pthread_create(&thread_id, nullptr, MemcacheProtocol::serve_client,
                           &client_args) == 0) {
            pthread_detach(thread_id);
        }
    }

    // cleanup
    close(server_socket);
    return 0;
}