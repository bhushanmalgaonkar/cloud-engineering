//#ifndef SOCKET_H
//#define SOCKET_H

//class Socket {
    //ConnectionArgs conn_args;

   //public:
    //Socket(ConnectionArgs args) { conn_args = args; }

    //// Read message from socket of length 'length' if provided
    //// If length is provided and received message is shorter, this method
    //// will wait for futher message and
    //// Return whole message as one std::string object
    //std::string read_msg(ssize_t length = -1) {
        //int client_socket = conn_args.client_socket;
        //char buffer[BUFFER_SIZE + 1] = {0};

        //std::string data;
        //do {
            //// clear buffer for next input
            //memset(buffer, 0, BUFFER_SIZE + 1);

            //// read command
            //ssize_t bytes = read(client_socket, buffer, BUFFER_SIZE);

            //// collect in one string data
            //data.append(buffer, bytes);
        //} while ((ssize_t)data.length() < length);

        //return data;
    //}

    //void send_msg(std::string data) {
        //int client_socket = conn_args.client_socket;
        //char buffer[BUFFER_SIZE + 1] = {0};

        //for (ssize_t start = 0; start < data.length(); start += BUFFER_SIZE) {
            //cout << "send_msg: data.length: " << data.length() << endl;
            //// clear buffer for next input
            //memset(buffer, 0, BUFFER_SIZE + 1);

            //cout << "start: " << start << ", len: " << (std::min(BUFFER_SIZE, (ssize_t)data.length() - start)) << endl;

            //std::size_t length = data.copy(
                //buffer, std::min(BUFFER_SIZE, (ssize_t)data.length() - start),
                //start);

            //cout << "send msg: buffer: " << buffer << endl;
            //send(client_socket, buffer, length, 0);
        //}
    //}

    //void cleanup() {
        //int client_socket = conn_args.client_socket;
        //close(client_socket);
    //}
//};

//#endif