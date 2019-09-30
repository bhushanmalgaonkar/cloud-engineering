import java.io.DataInputStream;
import java.net.Socket;
import java.util.Arrays;

public class MemcacheClient {

    private Socket socket;
    private DataInputStream in;

    public static void main(String[] args) {
        if (args.length < 2) {
            System.err.println("Usage Client <server_host> <server_port>");
            System.exit(0);
        }
        String host = args[0];
        int port = Integer.parseInt(args[1]);

        try {
            MemcacheClient client = new MemcacheClient(host, port);
            client.set("key", "first line\r\nsecond line\r\n\r\nfourth line");
            System.out.println("client.get(key): " + client.get("key"));
        } catch (Exception e) {
            System.err.println(e);
        }
    }

    public MemcacheClient(String host, int port) throws Exception {
        socket = new Socket(host, port);
        in = new DataInputStream(socket.getInputStream());
    }

    /**
     * Generates set command as per Memcached standard and sends it over the socket
     */
    public boolean set(String key, String value) {
        try {
            int length = 0;
            String[] lines = value.split("\r\n", -1);
            for (int i = 0; i < lines.length; ++i) {
                String line = lines[i];

                // count \r\n only if \r\n are the only characters in the line
                length += line.isEmpty() ? 2 : line.length();
            }

            String command = String.format("set %s %d %d %d noreply\r\n%s\r\n", key, 0, 0, length, value);
            socket.getOutputStream().write(command.getBytes(Constants.ENCODING));
            return true;
        } catch (Exception e) {
            return false;
        }
    }

    /**
     * Generates get command as per Memcached standard and sends it over the socket
     */
    public String get(String key) {
        try {
            String command = String.format("get %s\r\n", key);
            socket.getOutputStream().write(command.getBytes(Constants.ENCODING));

            String commandLine = in.readLine();
            if ("END".equals(commandLine)) {
                return null;
            }

            String[] splitCommand = commandLine.split(" ");

            // validate args using commandObj
            String[] args = new String[splitCommand.length - 1];
            System.arraycopy(splitCommand, 1, args, 0, splitCommand.length - 1);

            int requiredLength = Integer.parseInt(splitCommand[3]);
            StringBuilder response = new StringBuilder();
            while (requiredLength > 0) {
                String line = in.readLine();
                if (response.length() > 0)
                    response.append("\r\n");
                response.append(line);

                // count \r\n towards requiredLength only if string contains only \r\n
                requiredLength -= line.length() == 0 ? 2 : line.length();
            }
            // remove "END\r\n" from the stream
            in.readLine();
            return response.toString();
        } catch (Exception e) {
            return null;
        }
    }
}
