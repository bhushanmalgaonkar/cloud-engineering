#ifndef SOCKET_H
#define SOCKET_H

#include <string>

#include "ConnectionArgs.h"

class Socket {
    ConnectionArgs conn_args;

   public:
    Socket(ConnectionArgs args);

    // Read message from socket of length 'length' if provided
    // If length is provided and received message is shorter, this method
    // will wait for futher message and
    // Return whole message as one std::string object
    std::string read_msg(ssize_t length = -1);

    // Sends given data using socket.
    // For longer data, breaks the data into chunks that can fit into buffer
    void send_msg(std::string data);

    // Closes socket
    void cleanup(); 
};

#endif