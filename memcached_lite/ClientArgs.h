#ifndef CLIENT_ARGS_H 
#define CLIENT_ARGS_H

#include "MemcacheStore.h"

/**
 * Structure that stores parameters to be passed while starting new thread
 * for new client, allows to add new parameters easily
 **/
struct ClientArgs {
    int client_socket;
    MemcacheStore* store;
};

#endif