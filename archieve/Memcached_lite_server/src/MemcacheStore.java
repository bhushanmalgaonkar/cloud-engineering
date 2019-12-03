import java.io.*;

/**
 * Handles file operations.
 * This class does not make any changes to the value.
 * Returns the values as they were stored
  */

public class MemcacheStore {
    private String path;

    // create if not exists directory for storing cache files
    public boolean init(String path) {
        File directory = new File(path);
        if (directory.exists() || (!directory.exists() && directory.mkdirs())) {
            this.path = path;
            return true;
        }
        return false;
    }

    public boolean set(String key, String value) {
        try {
            BufferedWriter bw = new BufferedWriter(new FileWriter(path + "/" + key));
            bw.write(value);
            bw.close();
            return true;
        } catch (IOException e) {
            return false;
        }
    }

    public String get(String key) {
        String value = "", line = "";
        try {
            File file = new File(path + "/" + key);
            if (file.exists()) {
                BufferedReader br = new BufferedReader(new FileReader(path + "/" + key));
                while ((line = br.readLine()) != null) {
                    if (!value.isEmpty()) {
                        value += "\r\n";
                    }
                    value += line;
                }
            }
        } catch (IOException e) {

        }
        return value;
    }
}
