import java.io.IOException;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.SocketTimeoutException;

public class Server {
    public static void main(String[] args) throws IOException {
        if (args.length < 1) {
            System.err.println("Usage Server <port>");
            System.exit(0);
        }
        int PORT = Integer.parseInt(args[0]);

        // initialize store with path
        MemcacheStore store = new MemcacheStore();
        store.init(Constants.MEMCACHE_STORE_PATH);

        ServerSocket serverSocket = new ServerSocket(PORT);
        while (true) {
            try {
                Socket socket = serverSocket.accept();
                // start new connection in thread
                new Thread(() -> MemcacheProtocol.serveClient(socket, store)).start();
            } catch (SocketTimeoutException e) {
                System.err.println("Socket timed out: " + e.getMessage());
            } catch (Exception e) {
                System.err.println("Error occurred: " + e.getMessage());
            }
        }
    }
}
