import exceptions.MemcacheError;

/**
 * Get comand accepts one or more key and returns correponding value stored in cache as
 * VALUE <key> <flags> <size>
 * <data_block>
 * END
 * ...
 * Syntax: get key_1 key_2...
 */
public class MemcacheGetCommand extends MemcacheAbstractCommand {
    String[] keys;

    @Override
    public void setCommand(String command) throws MemcacheError {
        this.command = command;
    }

    @Override
    public void setArgs(String[] args) throws MemcacheError {
        keys = new String[args.length];
        System.arraycopy(args, 0, keys, 0, args.length);
    }

    @Override
    public void setValue(String value) throws MemcacheError {

    }

    @Override
    public int requiredValueLength() {
        return 0;
    }

    @Override
    public String execute(MemcacheStore store) throws MemcacheError {
        StringBuilder response = new StringBuilder();

        for (String key : keys) {
            String value = store.get(key);

            if (!value.isEmpty()) {
                int endOfFlag = value.indexOf(' ');
                int endOfExpTime = value.indexOf(' ', endOfFlag + 1);
                int endOfLength = value.indexOf(' ', endOfExpTime + 1);

                response.append("VALUE ");
                response.append(key + " ");
                response.append(value.substring(0, endOfFlag) + " ");
                response.append(value, endOfExpTime + 1, endOfLength);
                response.append("\r\n");
                response.append(value.substring(endOfLength + 1));
                response.append("\r\n");
            }

            response.append("END\r\n");
        }
        return response.toString();
    }
}
