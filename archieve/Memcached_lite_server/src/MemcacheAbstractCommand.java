import exceptions.MemcacheError;

public abstract class MemcacheAbstractCommand {
    String command = null;
    String value = null;

    /**
     * validates and sets command
     **/
    public abstract void setCommand(String command) throws MemcacheError;

    /**
     * validates and sets args
     **/
    public abstract void setArgs(String[] args) throws MemcacheError;

    /**
     * validates and sets value
     **/
    public abstract void setValue(String value) throws MemcacheError;


    /**
     * returns the length of further data/value required for the command
     * must be called after setArgs
     **/
    public abstract int requiredValueLength();

    /**
     * execute the command and return the result as string
     **/
    public abstract String execute(MemcacheStore store) throws MemcacheError;
}
