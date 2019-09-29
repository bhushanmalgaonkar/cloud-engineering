#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>
#include <cstring>
#include <iostream>

#include "Constants.h"
#include "Socket.h"

Socket::Socket(ConnectionArgs args) { conn_args = args; }

std::string Socket::read_msg(ssize_t length) {
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

void Socket::send_msg(std::string data) {
    int client_socket = conn_args.client_socket;
    char buffer[BUFFER_SIZE + 1] = {0};

    for (ssize_t start = 0; start < data.length(); start += BUFFER_SIZE) {
        std::cout << "send_msg: data.length: " << data.length() << std::endl;
        // clear buffer for next input
        memset(buffer, 0, BUFFER_SIZE + 1);

        std::cout << "start: " << start << ", len: "
                  << (std::min(BUFFER_SIZE, (ssize_t)data.length() - start))
                  << std::endl;

        std::size_t length = data.copy(
            buffer, std::min(BUFFER_SIZE, (ssize_t)data.length() - start),
            start);

        std::cout << "send msg: buffer: " << buffer << std::endl;
        send(client_socket, buffer, length, 0);
    }
}

void Socket::cleanup() {
    int client_socket = conn_args.client_socket;
    close(client_socket);
}