import exceptions.MemcacheClientError;
import exceptions.MemcacheError;
import exceptions.MemcacheServerError;

public class MemcacheSetCommand extends MemcacheAbstractCommand {
    String key;
    int flags;
    long expTime;
    int length;
    String value;

    @Override
    public void setCommand(String command) throws MemcacheError {
        this.command = command;
    }

    @Override
    public void setArgs(String[] args) throws MemcacheError {
        if (args.length < 4 || args.length > 5) {
            throw new MemcacheError(Constants.GENERIC_ERROR);
        }
        try {
            key = args[0];
            flags = Integer.parseInt(args[1]);
            expTime = Long.parseLong(args[2]);
            length = Integer.parseInt(args[3]);
        } catch (NumberFormatException e) {
            throw new MemcacheClientError(Constants.BAD_COMMAND_LINE_FORMAT);
        }
    }

    @Override
    public void setValue(String value) throws MemcacheError {
        this.value = value;
    }

    @Override
    public int requiredValueLength() {
        return length;
    }

    @Override
    public String execute(MemcacheStore store) throws MemcacheError {
        String data = String.format("%d %d %d %s", flags, expTime, length, value);
        if (!store.set(key, data)) {
            throw new MemcacheServerError(Constants.GENERIC_ERROR);
        }
        return "STORED\r\n";
    }
}
