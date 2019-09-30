package exceptions;

public class MemcacheClientError extends MemcacheError {
    public MemcacheClientError(String message) {
        super("CLIENT_ERROR " + message);
    }
}
