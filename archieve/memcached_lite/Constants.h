#ifndef CONSTANTS_H
#define CONSTANTS_H

#include<string>
#include<unordered_set>

/**
 * Command that client sends to terminate the connection with server
 **/
const std::string CMD_QUIT = "quit\r\n";

/**
 * Error message sent to client when invalid command is entered
 **/
const std::string GENERIC_ERROR = "ERROR\r\n";

/**
 * Error message sent to client when more than required data is received
 **/
const std::string CLIENT_ERROR_BAD_DATA_CHUNK = "CLIENT_ERROR bad data chunk\r\n";

/**
 * Path for storing memcache entries on file system
 **/
const std::string MEMCACHE_STORE_PATH = "./store";

/**
 * Buffer size used to send/receive data to/from socket
 **/
const ssize_t BUFFER_SIZE = 1024;

/**
 * Message sent to newly connected client
 **/
const char* const WELCOME_MESSAGE = "Welcome to Memcached-lite\n";

/**
 * Set of commands that require value parameter (2nd line)
 **/
const std::unordered_set<std::string> COMMANDS_WITH_VALUES = {"set"};

#endif