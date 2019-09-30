package exceptions;

public class MemcacheError extends Exception {
    public MemcacheError(String message) {
        super(message);
    }
}
