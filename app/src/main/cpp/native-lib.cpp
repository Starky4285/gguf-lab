// GGUF Lab - JNI bridge to llama.cpp
//
// Java side: com.test.gguflab.LlamaBridge
//   String  nativeLoad(String path, int nThreads, int nCtx)   -> "" on success, else error text
//   void    nativeUnload()
//   String  nativeGenerate(String[] roles, String[] contents, int maxTokens, float temp, TokenListener cb)
//              -> stats text, or text starting with "ERROR:" (PROMPT_TOO_LONG is a special error)
//   void    nativeStop()
//   String  nativeSystemInfo()
//
// Tokens are streamed to cb.onToken(byte[]) as complete UTF-8 chunks.

#include <jni.h>
#include <android/log.h>

#include <atomic>
#include <chrono>
#include <cstdio>
#include <mutex>
#include <string>
#include <vector>

#include "llama.h"

#define LOG_TAG "GGUFLAB_NATIVE"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGW(...) __android_log_print(ANDROID_LOG_WARN, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

namespace {

std::mutex          g_mutex;
llama_model *       g_model    = nullptr;
int                 g_threads  = 4;
int                 g_ctx      = 2048;
std::atomic<bool>   g_stop{false};
bool                g_backend_ready = false;

void log_cb(ggml_log_level level, const char * text, void *) {
    if (level == GGML_LOG_LEVEL_ERROR) {
        __android_log_print(ANDROID_LOG_ERROR, "llama.cpp", "%s", text);
    } else if (level == GGML_LOG_LEVEL_WARN) {
        __android_log_print(ANDROID_LOG_WARN, "llama.cpp", "%s", text);
    }
}

std::string jstr(JNIEnv * env, jstring s) {
    if (!s) return {};
    const char * c = env->GetStringUTFChars(s, nullptr);
    std::string out(c ? c : "");
    if (c) env->ReleaseStringUTFChars(s, c);
    return out;
}

// Java's GetStringUTFChars returns "modified UTF-8": characters outside the BMP
// (emoji) arrive as surrogate pairs (6 bytes). Convert those to real UTF-8.
std::string java_utf8(JNIEnv * env, jstring s) {
    if (!s) return {};
    const jsize n = env->GetStringLength(s);
    const jchar * u = env->GetStringChars(s, nullptr);
    std::string out;
    out.reserve(n * 2);
    for (jsize i = 0; i < n; ++i) {
        uint32_t cp = u[i];
        if (cp >= 0xD800 && cp <= 0xDBFF && i + 1 < n && u[i + 1] >= 0xDC00 && u[i + 1] <= 0xDFFF) {
            cp = 0x10000 + ((cp - 0xD800) << 10) + (u[i + 1] - 0xDC00);
            ++i;
        }
        if (cp < 0x80) {
            out += char(cp);
        } else if (cp < 0x800) {
            out += char(0xC0 | (cp >> 6));
            out += char(0x80 | (cp & 0x3F));
        } else if (cp < 0x10000) {
            out += char(0xE0 | (cp >> 12));
            out += char(0x80 | ((cp >> 6) & 0x3F));
            out += char(0x80 | (cp & 0x3F));
        } else {
            out += char(0xF0 | (cp >> 18));
            out += char(0x80 | ((cp >> 12) & 0x3F));
            out += char(0x80 | ((cp >> 6) & 0x3F));
            out += char(0x80 | (cp & 0x3F));
        }
    }
    env->ReleaseStringChars(s, u);
    return out;
}

// Moves every complete UTF-8 character from `pending` into `out`.
// An incomplete sequence at the end stays in `pending` (the next token completes it).
// Invalid bytes are replaced with U+FFFD so the stream can never get stuck.
void drain_utf8(std::string & pending, std::string & out, bool flush_all) {
    size_t i = 0;
    const size_t n = pending.size();
    while (i < n) {
        const unsigned char c = (unsigned char) pending[i];
        // strict UTF-8 (RFC 3629): no overlongs, no surrogates, nothing above U+10FFFF
        size_t len = 0;
        unsigned char lo = 0x80, hi = 0xBF;   // allowed range of the 2nd byte
        if (c < 0x80)                    len = 1;
        else if (c >= 0xC2 && c <= 0xDF) len = 2;
        else if (c >= 0xE0 && c <= 0xEF) { len = 3; if (c == 0xE0) lo = 0xA0; if (c == 0xED) hi = 0x9F; }
        else if (c >= 0xF0 && c <= 0xF4) { len = 4; if (c == 0xF0) lo = 0x90; if (c == 0xF4) hi = 0x8F; }
        if (len == 0) {                       // stray continuation / invalid lead byte
            out += "\xEF\xBF\xBD";
            ++i;
            continue;
        }
        bool ok = true;
        size_t have = 1;
        for (size_t k = 1; k < len && i + k < n; ++k, ++have) {
            const unsigned char b = (unsigned char) pending[i + k];
            if (k == 1 ? (b < lo || b > hi) : (b >> 6) != 0x2) { ok = false; break; }
        }
        if (ok && have < len) {               // valid so far but incomplete at the end
            if (flush_all) { out += "\xEF\xBF\xBD"; i = n; }
            break;
        }
        if (!ok) {
            out += "\xEF\xBF\xBD";
            ++i;
            continue;
        }
        out.append(pending, i, len);
        i += len;
    }
    pending.erase(0, i);
}

bool emit(JNIEnv * env, jobject cb, jmethodID mid, const std::string & text) {
    if (text.empty() || !cb || !mid) return true;
    jbyteArray arr = env->NewByteArray((jsize) text.size());
    if (!arr) return false;
    env->SetByteArrayRegion(arr, 0, (jsize) text.size(), reinterpret_cast<const jbyte *>(text.data()));
    env->CallVoidMethod(cb, mid, arr);
    env->DeleteLocalRef(arr);
    if (env->ExceptionCheck()) {
        env->ExceptionClear();
        return false;
    }
    return true;
}

double ms_since(std::chrono::steady_clock::time_point t0) {
    return std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count();
}

} // namespace

extern "C" JNIEXPORT jstring JNICALL
Java_com_test_gguflab_LlamaBridge_nativeLoad(JNIEnv * env, jclass, jstring jpath, jint n_threads, jint n_ctx) {
    std::lock_guard<std::mutex> lock(g_mutex);
    if (!g_backend_ready) {
        llama_log_set(log_cb, nullptr);
        llama_backend_init();
        g_backend_ready = true;
    }
    if (g_model) {
        llama_model_free(g_model);
        g_model = nullptr;
    }
    const std::string path = jstr(env, jpath);
    llama_model_params mp = llama_model_default_params();
    mp.n_gpu_layers = 0;                 // CPU only on Android
    g_model = llama_model_load_from_file(path.c_str(), mp);
    if (!g_model) {
        return env->NewStringUTF("Could not load the model. Is it a valid .gguf file?");
    }
    g_threads = n_threads > 0 ? n_threads : 4;
    g_ctx     = n_ctx > 0 ? n_ctx : 2048;
    char desc[256] = {0};
    llama_model_desc(g_model, desc, sizeof(desc));
    LOGI("loaded %s (%s), threads=%d ctx=%d", path.c_str(), desc, g_threads, g_ctx);
    return env->NewStringUTF("");
}

extern "C" JNIEXPORT void JNICALL
Java_com_test_gguflab_LlamaBridge_nativeUnload(JNIEnv *, jclass) {
    std::lock_guard<std::mutex> lock(g_mutex);
    if (g_model) {
        llama_model_free(g_model);
        g_model = nullptr;
    }
}

extern "C" JNIEXPORT void JNICALL
Java_com_test_gguflab_LlamaBridge_nativeStop(JNIEnv *, jclass) {
    g_stop.store(true);
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_test_gguflab_LlamaBridge_nativeSystemInfo(JNIEnv * env, jclass) {
    return env->NewStringUTF(llama_print_system_info());
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_test_gguflab_LlamaBridge_nativeGenerate(JNIEnv * env, jclass,
                                                 jobjectArray jroles, jobjectArray jcontents,
                                                 jint max_tokens, jfloat temperature, jobject cb) {
    std::lock_guard<std::mutex> lock(g_mutex);
    g_stop.store(false);
    if (!g_model) return env->NewStringUTF("ERROR: no model loaded");

    // ---- 1. build the chat prompt with the model's own template (ChatML for Qwen)
    const jsize n_msg = env->GetArrayLength(jroles);
    std::vector<std::string> roles(n_msg), contents(n_msg);
    std::vector<llama_chat_message> msgs(n_msg);
    size_t total_chars = 0;
    for (jsize i = 0; i < n_msg; ++i) {
        auto r = (jstring) env->GetObjectArrayElement(jroles, i);
        auto c = (jstring) env->GetObjectArrayElement(jcontents, i);
        roles[i]    = jstr(env, r);
        contents[i] = java_utf8(env, c);
        env->DeleteLocalRef(r);
        env->DeleteLocalRef(c);
        total_chars += roles[i].size() + contents[i].size();
    }
    for (jsize i = 0; i < n_msg; ++i) msgs[i] = { roles[i].c_str(), contents[i].c_str() };

    const char * tmpl = llama_model_chat_template(g_model, nullptr);
    if (!tmpl) tmpl = "chatml";
    std::vector<char> buf(total_chars * 2 + 512);
    int32_t len = llama_chat_apply_template(tmpl, msgs.data(), msgs.size(), true, buf.data(), (int32_t) buf.size());
    if (len > (int32_t) buf.size()) {
        buf.resize(len + 1);
        len = llama_chat_apply_template(tmpl, msgs.data(), msgs.size(), true, buf.data(), (int32_t) buf.size());
    }
    if (len < 0) return env->NewStringUTF("ERROR: chat template not supported by this model");
    const std::string prompt(buf.data(), len);

    // ---- 2. tokenize
    const llama_vocab * vocab = llama_model_get_vocab(g_model);
    int32_t n_prompt = -llama_tokenize(vocab, prompt.c_str(), (int32_t) prompt.size(), nullptr, 0, true, true);
    if (n_prompt <= 0) return env->NewStringUTF("ERROR: tokenization failed");
    std::vector<llama_token> tokens(n_prompt);
    if (llama_tokenize(vocab, prompt.c_str(), (int32_t) prompt.size(), tokens.data(), n_prompt, true, true) < 0) {
        return env->NewStringUTF("ERROR: tokenization failed");
    }
    const int n_predict = max_tokens > 0 ? max_tokens : 384;
    if (n_prompt + n_predict > g_ctx) {
        return env->NewStringUTF("ERROR: PROMPT_TOO_LONG");
    }

    // ---- 3. fresh context for every request (simple and version-proof)
    llama_context_params cp = llama_context_default_params();
    cp.n_ctx           = g_ctx;
    cp.n_batch         = g_ctx;          // whole prompt in one llama_decode call
    cp.n_threads       = g_threads;
    cp.n_threads_batch = g_threads;
    cp.no_perf         = true;
    llama_context * ctx = llama_init_from_model(g_model, cp);
    if (!ctx) return env->NewStringUTF("ERROR: could not create context (out of memory?)");

    // ---- 4. sampler: low temperature for exact maths
    llama_sampler * smpl = llama_sampler_chain_init(llama_sampler_chain_default_params());
    if (temperature <= 0.0f) {
        llama_sampler_chain_add(smpl, llama_sampler_init_greedy());
    } else {
        llama_sampler_chain_add(smpl, llama_sampler_init_top_k(40));
        llama_sampler_chain_add(smpl, llama_sampler_init_top_p(0.9f, 1));
        llama_sampler_chain_add(smpl, llama_sampler_init_temp(temperature));
        llama_sampler_chain_add(smpl, llama_sampler_init_dist(LLAMA_DEFAULT_SEED));
    }

    jmethodID on_token = nullptr;
    if (cb) {
        jclass cls = env->GetObjectClass(cb);
        on_token = env->GetMethodID(cls, "onToken", "([B)V");
        env->DeleteLocalRef(cls);
    }

    // ---- 5. prefill + generate
    std::string error, pending, ready;
    int n_gen = 0;
    double prefill_ms = 0, gen_ms = 0;
    const auto t0 = std::chrono::steady_clock::now();

    llama_batch batch = llama_batch_get_one(tokens.data(), (int32_t) tokens.size());
    if (llama_decode(ctx, batch) != 0) {
        error = "ERROR: prompt decode failed";
    } else {
        prefill_ms = ms_since(t0);
        const auto t1 = std::chrono::steady_clock::now();
        llama_token tok;
        char piece[256];
        while (n_gen < n_predict && !g_stop.load()) {
            tok = llama_sampler_sample(smpl, ctx, -1);
            if (llama_vocab_is_eog(vocab, tok)) break;
            const int n = llama_token_to_piece(vocab, tok, piece, sizeof(piece), 0, false);
            if (n > 0) pending.append(piece, n);
            ++n_gen;
            ready.clear();
            drain_utf8(pending, ready, false);
            if (!emit(env, cb, on_token, ready)) { error = "ERROR: callback failed"; break; }
            batch = llama_batch_get_one(&tok, 1);
            if (llama_decode(ctx, batch) != 0) { error = "ERROR: decode failed"; break; }
        }
        ready.clear();
        drain_utf8(pending, ready, true);
        emit(env, cb, on_token, ready);
        gen_ms = ms_since(t1);
    }

    llama_sampler_free(smpl);
    llama_free(ctx);

    if (!error.empty()) return env->NewStringUTF(error.c_str());
    char stats[256];
    snprintf(stats, sizeof(stats), "%d prompt tok in %.1fs | %d tok at %.1f tok/s%s",
             n_prompt, prefill_ms / 1000.0, n_gen, n_gen > 0 && gen_ms > 0 ? n_gen * 1000.0 / gen_ms : 0.0,
             g_stop.load() ? " | stopped" : "");
    return env->NewStringUTF(stats);
}
