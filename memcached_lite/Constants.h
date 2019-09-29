#ifndef CONSTANTS_H
#define CONSTANTS_H

#include<string>
#include<unordered_set>

/**
 * Number of seconds in 30 days
 * This value is used to distinguish between relative/absolute
 * expiration time. If the expiration time specified by client
 * is less than EXP_TIME_LIMIT, expiration time is set as number
 * of seconds starting from current time, else it is set to unix
 * timestamp as it is.
 **/
#define EXP_TIME_LIMIT 2592000ll

/**
 * Command that client sends to tell server not to send the result of
 * store operation
 **/
std::string CMD_NO_REPLY = "noreply\r\n";

/**
 * Command that client sends to terminate the connection with server
 **/
std::string CMD_QUIT = "quit\r\n";

/**
 * Error message sent to client when invalid command is entered
 **/
std::string GENERIC_ERROR = "ERROR\r\n";

/**
 * Buffer size used to send/receive data to/from socket
 **/
ssize_t BUFFER_SIZE = 1024;

/**
 * Message sent to newly connected client
 **/
const char* WELCOME_MESSAGE = "Welcome to Memcached-lite\n";

/**
 * Set of commands that require value parameter (2nd line)
 **/
std::unordered_set<std::string> COMMANDS_WITH_VALUES = {"set"};

#endif