#ifndef CONNECTION_ARGS_H
#define CONNECTION_ARGS_H

/**
 * Structure that stores parameters to be passed while starting new thread
 * for new client, allows to add new parameters easily
 **/
struct ConnectionArgs {
    int client_socket;
};

#endif