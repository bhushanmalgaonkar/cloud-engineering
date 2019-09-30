public class Constants {

    // path where memcache files will be persisted
    public static final String MEMCACHE_STORE_PATH = "./store";

    // error message sent to client when either command is invalid or
    // command has incorrect number of arguments
    public static final String GENERIC_ERROR = "ERROR\r\n";

    // error message sent to client when data length doesn't match command
    public static final String BAD_DATA_CHUNK = "bad data chunk\r\n";

    // error message sent to client when command has required number of arguments
    // but not the required type
    public static final String BAD_COMMAND_LINE_FORMAT = "bad command line format\r\n";

    // specified as last argument of set command by client when it doesn't
    // expect the result of operation as response
    public static final String NOREPLY = "noreply";

    // command sent by client to close its connection from server side
    public static final String CMD_QUIT = "quit";

    // encoding used for data transfer over socket
    public static final String ENCODING = "UTF-8";
}
