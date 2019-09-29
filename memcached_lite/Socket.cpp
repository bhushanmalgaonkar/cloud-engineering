#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>
#include <cstring>
#include <iostream>

#include "Constants.h"
#include "Socket.h"

Socket::Socket(int socket) { this->socket = socket; }

std::string Socket::read_msg(int length) {
    char buffer[BUFFER_SIZE + 1] = {0};

    int char_count = 0;
    std::string data;
    do {
        // clear buffer for next input
        memset(buffer, 0, BUFFER_SIZE + 1);

        // read command
        ssize_t bytes = read(socket, buffer, BUFFER_SIZE);
        char_count += (int) bytes;

        // if string is not empty, don't count trailing \r\n
        // count \r\n if these are only characters in the line
        if (bytes > 2) {
        //    std::cout << "bytes > 2" << std::endl;
            char_count -= 2;
        }
        //std::cout << "bytes: " << bytes << std::endl;

        // collect in one string data
        data.append(buffer, bytes);
        //std::cout << "data: #" << data << "#" << std::endl;
        //std::cout << "char_count: #" << char_count << "#" << std::endl;
        //std::cout << "data.length: #" << data.length() << ", length: " << length << "#" << std::endl;
    } while (char_count < length);

    // length mismatch, return empty string
    if (length > 0 && char_count != length) {
        data.clear();
    }

    return data;
}

void Socket::send_msg(std::string data) {
    char buffer[BUFFER_SIZE + 1] = {0};

    for (ssize_t start = 0; start < data.length(); start += BUFFER_SIZE) {
        // clear buffer for next input
        memset(buffer, 0, BUFFER_SIZE + 1);

        std::size_t length = data.copy(
            buffer, std::min(BUFFER_SIZE, (ssize_t)data.length() - start),
            start);

        send(socket, buffer, length, 0);
    }
}

void Socket::cleanup() {
    close(socket);
}