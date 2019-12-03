import exceptions.MemcacheClientError;
import exceptions.MemcacheError;

import java.io.DataInputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.net.Socket;


public class MemcacheProtocol {
    /**
     * Returns concrete instance of MemcacheAbstractCommand corresponding to 'command'
     */
    public static MemcacheAbstractCommand resolve(String command) throws MemcacheError {
        MemcacheAbstractCommand commandObj = null;
        switch (command) {
            case "set":
                commandObj = new MemcacheSetCommand();
                break;
            case "get":
                commandObj = new MemcacheGetCommand();
                break;
            default:
                throw new MemcacheError(Constants.GENERIC_ERROR);
        }
        return commandObj;
    }

    /**
     * Serves one client until the client break of the connection using CMD_QUIT command
     * @param socket socket to send/receive data
     * @param store store to use
     */
    public static void serveClient(Socket socket, MemcacheStore store) {
        try {
            DataInputStream in = new DataInputStream(socket.getInputStream());
            OutputStream out = socket.getOutputStream();

            // send welcome message
            while (true) {
                String command = in.readLine();

                // ignore empty lines in commands
                if (command == null || command.isEmpty()) {
                    continue;
                }

                // break if CMD_QUIT
                String[] splitCommand = command.split(" ");
                if (Constants.CMD_QUIT.equals(splitCommand[0])) {
                    break;
                }

                String value = "";
                String response;
                try {
                    MemcacheAbstractCommand commandObj = resolve(splitCommand[0]);
                    commandObj.setCommand(splitCommand[0]);

                    // validate args using commandObj
                    String[] args = new String[splitCommand.length - 1];
                    System.arraycopy(splitCommand, 1, args, 0, splitCommand.length - 1);
                    commandObj.setArgs(args);

                    int requiredLength = commandObj.requiredValueLength();
                    while (requiredLength > 0) {
                        String line = in.readLine();
                        value += line + "\r\n";

                        // count \r\n towards requiredLength only if string contains only \r\n
                        requiredLength -= line.length() == 0 ? 2 : line.length();
                    }
                    if (requiredLength < 0) {
                        throw new MemcacheClientError(Constants.BAD_DATA_CHUNK);
                    }
                    commandObj.setValue(value);

                    // execute command
                    response = commandObj.execute(store);
                } catch (MemcacheError e) {
                    response = e.getMessage();
                }

                // don't respond if NOREPLY is specified
                if (!command.endsWith(Constants.NOREPLY)) {
                    out.write(response.getBytes(Constants.ENCODING));
                }
            }

            socket.close();
        } catch (IOException e) {
            System.err.println("Error opening in/out stream for " + socket.getRemoteSocketAddress() + ". Exiting..");
        }
    }
}
