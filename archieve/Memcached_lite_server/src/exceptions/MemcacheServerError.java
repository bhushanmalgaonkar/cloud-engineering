package exceptions;

public class MemcacheServerError extends MemcacheError {
    public MemcacheServerError(String message) {
        super("SERVER_ERROR " + message);
    }
}
