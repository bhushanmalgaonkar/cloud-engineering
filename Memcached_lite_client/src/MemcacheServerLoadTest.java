import java.util.List;
import java.util.ArrayList;
import java.util.Random;

public class MemcacheServerLoadTest {
    public static String str = "bkIzDAVKPmAiabPelRWIAlctbeClhhDjgLyxXaoihrupJPkFAePHOdTBOdElbymrmHUDdDKXsZSpWBeh";
    public static Random random = new Random();

    public static String host;
    public static int port;

    public static int NUM_REQUESTS_PER_CLIENT = 2000;
    public static int NUM_CLIENTS = 2000;

    public static int activeClients = 0;
    public static int maxConcurrentClients = 0;
    public static int failedConnections = 0;

    public static void main(String[] args) {
        if (args.length < 2) {
            System.err.println("Usage Client <server_host> <server_port>");
            System.exit(0);
        }
        host = args[0];
        port = Integer.parseInt(args[1]);

        List<Thread> threads = new ArrayList<Thread>();
        for (int i = 0; i < NUM_CLIENTS; ++i) {
            try {
                Thread t = new Thread(() -> runClient());
                threads.add(t);
                t.start();
            } catch (Exception e) {
                System.err.println(e);
            }
        }

        for (Thread t : threads) {
            try {
                t.join();
            } catch (Exception e) {}
        }
        System.out.println("Max concurrent clients: " + maxConcurrentClients);
        System.out.println("Failed connections: " + failedConnections);
    }

    public static void runClient() {
        MemcacheClient client = null;
        try {
            client = new MemcacheClient(host, port);
        } catch (Exception e) {
            failedConnections++;
            return;
        }

        try {
            updateCounter(1);
            for (int i = 0; i < NUM_REQUESTS_PER_CLIENT; ++i) {
                client.set(randomString(3), "first line\r\nsecond line\r\n\r\nfourth line");
            }
            updateCounter(-1);
        } catch (Exception e) {
            System.err.println("Error");
        } finally {
            client.close();
        }
    }

    public static String randomString(int length) {
        int start = random.nextInt(str.length() - length);
        return str.substring(start, start + length);
    }

    public static synchronized void updateCounter(int change) {
        activeClients += change;
        maxConcurrentClients = Math.max(maxConcurrentClients, activeClients);
    }
}
