package com.test.gguflab;

/** Thin Java wrapper around native-lib.cpp (llama.cpp). Call from a background thread only. */
public final class LlamaBridge {

    static {
        System.loadLibrary("native-lib");
    }

    /** Receives generated text as UTF-8 bytes; every chunk is a complete UTF-8 string. */
    public interface TokenListener {
        void onToken(byte[] utf8);
    }

    private LlamaBridge() {}

    /** @return "" on success, otherwise an error message. */
    public static native String nativeLoad(String path, int nThreads, int nCtx);

    public static native void nativeUnload();

    /**
     * @param roles    "system" / "user" / "assistant" for each message
     * @param contents message text, same length as roles
     * @return stats text, or a string starting with "ERROR:" ("ERROR: PROMPT_TOO_LONG" if history must be trimmed)
     */
    public static native String nativeGenerate(String[] roles, String[] contents, int maxTokens,
                                               float temperature, TokenListener listener);

    public static native void nativeStop();

    public static native String nativeSystemInfo();
}
