package com.test.gguflab;

import android.content.Intent;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.OpenableColumns;
import android.text.SpannableStringBuilder;
import android.text.Spanned;
import android.text.style.ForegroundColorSpan;
import android.text.style.RelativeSizeSpan;
import android.text.style.StyleSpan;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ScrollView;
import android.widget.TextView;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends AppCompatActivity {

    private static final int N_CTX = 2048;
    private static final int MAX_TOKENS = 384;
    private static final float TEMPERATURE = 0.2f;   // low = consistent maths
    private static final int HISTORY_TURNS = 2;      // previous Q&A pairs sent with a new question

    private EditText etPrompt;
    private Button btnGenerate, btnLoad, btnStop, btnWhy, btnNew;
    private TextView tvOutput, tvStatus;
    private ScrollView scroll;

    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private final Handler ui = new Handler(Looper.getMainLooper());
    private final SpannableStringBuilder transcript = new SpannableStringBuilder();
    private final List<String[]> history = new ArrayList<>();   // {role, content}

    private String systemPrompt;
    private boolean modelReady = false;
    private boolean busy = false;
    private int threads;
    private SharedPreferences prefs;

    private final ActivityResultLauncher<String[]> pickModel =
            registerForActivityResult(new ActivityResultContracts.OpenDocument(), this::onModelPicked);

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        View root = findViewById(R.id.root);
        ViewCompat.setOnApplyWindowInsetsListener(root, (v, insets) -> {
            Insets b = insets.getInsets(WindowInsetsCompat.Type.systemBars() | WindowInsetsCompat.Type.ime());
            int pad = (int) (12 * getResources().getDisplayMetrics().density);
            v.setPadding(b.left + pad, b.top + pad, b.right + pad, b.bottom + pad);
            return WindowInsetsCompat.CONSUMED;
        });

        etPrompt = findViewById(R.id.etPrompt);
        btnGenerate = findViewById(R.id.btnGenerate);
        btnLoad = findViewById(R.id.btnLoad);
        btnStop = findViewById(R.id.btnStop);
        btnWhy = findViewById(R.id.btnWhy);
        btnNew = findViewById(R.id.btnNew);
        tvOutput = findViewById(R.id.tvChat);
        tvStatus = findViewById(R.id.tvStatus);
        scroll = findViewById(R.id.scroll);

        prefs = getSharedPreferences("gguflab", MODE_PRIVATE);
        systemPrompt = readAsset("system_prompt.txt");
        int cores = Runtime.getRuntime().availableProcessors();
        threads = cores >= 8 ? 4 : Math.max(2, cores / 2);   // performance cores only

        btnLoad.setOnClickListener(v -> pickModel.launch(new String[]{"*/*"}));
        btnGenerate.setOnClickListener(v -> {
            String q = etPrompt.getText().toString().trim();
            if (q.isEmpty()) return;
            etPrompt.setText("");
            ask(q);
        });
        btnWhy.setOnClickListener(v -> {
            if (history.isEmpty()) {
                setStatus("Ask a question first.");
                return;
            }
            ask("Why does that trick work? Explain simply.");
        });
        btnNew.setOnClickListener(v -> {
            if (busy) return;
            history.clear();
            transcript.clear();
            tvOutput.setText("New chat. Ask a CHSL question.");
        });
        btnStop.setOnClickListener(v -> LlamaBridge.nativeStop());

        String saved = prefs.getString("model_path", null);
        if (saved != null && new File(saved).exists()) {
            loadModel(saved);
        }
        refreshButtons();
    }

    // ------------------------------------------------------------------ model loading

    private void onModelPicked(Uri uri) {
        if (uri == null) return;
        String name = displayName(uri);
        if (name == null || !name.toLowerCase().endsWith(".gguf")) {
            setStatus("Please choose a .gguf file.");
            return;
        }
        busy = true;
        refreshButtons();
        setStatus("Copying " + name + " ...");
        worker.execute(() -> {
            File dir = new File(getFilesDir(), "models");
            //noinspection ResultOfMethodCallIgnored
            dir.mkdirs();
            File dst = new File(dir, name);
            long total = fileSize(uri);
            try (InputStream in = getContentResolver().openInputStream(uri);
                 OutputStream out = new FileOutputStream(dst)) {
                if (in == null) throw new Exception("cannot open file");
                byte[] buf = new byte[1 << 20];
                long done = 0, lastShown = 0;
                int n;
                while ((n = in.read(buf)) > 0) {
                    out.write(buf, 0, n);
                    done += n;
                    if (total > 0 && done - lastShown > 50L * 1024 * 1024) {
                        lastShown = done;
                        final int p = (int) (done * 100 / total);
                        ui.post(() -> setStatus("Copying " + name + " ... " + p + "%"));
                    }
                }
            } catch (Exception e) {
                //noinspection ResultOfMethodCallIgnored
                dst.delete();
                ui.post(() -> {
                    busy = false;
                    refreshButtons();
                    setStatus("Copy failed: " + e.getMessage());
                });
                return;
            }
            // keep only the newest model to save storage
            File[] old = dir.listFiles();
            if (old != null) for (File f : old) if (!f.equals(dst)) //noinspection ResultOfMethodCallIgnored
                f.delete();
            ui.post(() -> {
                busy = false;
                loadModel(dst.getAbsolutePath());
            });
        });
    }

    private void loadModel(String path) {
        busy = true;
        modelReady = false;
        refreshButtons();
        String name = new File(path).getName();
        setStatus("Loading " + name + " ...");
        worker.execute(() -> {
            String err = LlamaBridge.nativeLoad(path, threads, N_CTX);
            ui.post(() -> {
                busy = false;
                if (err.isEmpty()) {
                    modelReady = true;
                    prefs.edit().putString("model_path", path).apply();
                    setStatus(name + " | " + threads + " threads");
                } else {
                    setStatus(err);
                }
                refreshButtons();
            });
        });
    }

    // ------------------------------------------------------------------ chat

    private void ask(String question) {
        if (!modelReady || busy) return;
        busy = true;
        refreshButtons();

        appendLabel("You: ");
        transcript.append(question).append("\n\n");
        appendLabel("Coach: ");
        tvOutput.setText(transcript);
        scrollDown();

        final StringBuilder reply = new StringBuilder();
        worker.execute(() -> {
            String result = null;
            for (int keep = HISTORY_TURNS; keep >= 0; keep--) {
                List<String[]> msgs = buildMessages(question, keep);
                String[] roles = new String[msgs.size()];
                String[] contents = new String[msgs.size()];
                for (int i = 0; i < msgs.size(); i++) {
                    roles[i] = msgs.get(i)[0];
                    contents[i] = msgs.get(i)[1];
                }
                result = LlamaBridge.nativeGenerate(roles, contents, MAX_TOKENS, TEMPERATURE, utf8 -> {
                    String piece = new String(utf8, StandardCharsets.UTF_8);
                    reply.append(piece);
                    ui.post(() -> {
                        transcript.append(piece);
                        tvOutput.setText(transcript);
                        scrollDown();
                    });
                });
                if (!"ERROR: PROMPT_TOO_LONG".equals(result)) break;   // otherwise retry with less history
            }
            final String stats = result;
            ui.post(() -> {
                if (stats != null && stats.startsWith("ERROR")) {
                    transcript.append(stats.equals("ERROR: PROMPT_TOO_LONG")
                            ? "(Question is too long for the model's context.)" : stats);
                } else {
                    history.add(new String[]{"user", question});
                    history.add(new String[]{"assistant", reply.toString().trim()});
                    while (history.size() > 2 * HISTORY_TURNS) history.remove(0);
                    int start = transcript.length();
                    transcript.append("\n").append(stats == null ? "" : stats);
                    transcript.setSpan(new RelativeSizeSpan(0.75f), start, transcript.length(), Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
                    transcript.setSpan(new ForegroundColorSpan(0xFF888888), start, transcript.length(), Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
                }
                transcript.append("\n\n");
                tvOutput.setText(transcript);
                scrollDown();
                busy = false;
                refreshButtons();
            });
        });
    }

    private List<String[]> buildMessages(String question, int keepTurns) {
        List<String[]> msgs = new ArrayList<>();
        msgs.add(new String[]{"system", systemPrompt});
        int from = Math.max(0, history.size() - 2 * keepTurns);
        msgs.addAll(history.subList(from, history.size()));
        msgs.add(new String[]{"user", question});
        return msgs;
    }

    // ------------------------------------------------------------------ helpers

    private void appendLabel(String label) {
        int start = transcript.length();
        transcript.append(label);
        transcript.setSpan(new StyleSpan(Typeface.BOLD), start, transcript.length(), Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
    }

    private void refreshButtons() {
        boolean canAsk = modelReady && !busy;
        btnGenerate.setEnabled(canAsk);
        btnWhy.setEnabled(canAsk);
        btnNew.setEnabled(!busy);
        btnLoad.setEnabled(!busy);
        btnStop.setEnabled(busy && modelReady);
    }

    private void setStatus(String s) {
        tvStatus.setText(s);
    }

    private void scrollDown() {
        scroll.post(() -> scroll.fullScroll(View.FOCUS_DOWN));
    }

    private String readAsset(String name) {
        try (BufferedReader r = new BufferedReader(new InputStreamReader(getAssets().open(name), StandardCharsets.UTF_8))) {
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = r.readLine()) != null) sb.append(line).append('\n');
            return sb.toString().trim();
        } catch (Exception e) {
            return "You are CHSL Coach, a speed-solving tutor for the SSC CHSL exam.";
        }
    }

    private String displayName(Uri uri) {
        try (Cursor c = getContentResolver().query(uri, new String[]{OpenableColumns.DISPLAY_NAME}, null, null, null)) {
            if (c != null && c.moveToFirst()) return c.getString(0);
        } catch (Exception ignored) {
        }
        return uri.getLastPathSegment();
    }

    private long fileSize(Uri uri) {
        try (Cursor c = getContentResolver().query(uri, new String[]{OpenableColumns.SIZE}, null, null, null)) {
            if (c != null && c.moveToFirst() && !c.isNull(0)) return c.getLong(0);
        } catch (Exception ignored) {
        }
        return -1;
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (isFinishing()) {
            LlamaBridge.nativeStop();
            worker.execute(LlamaBridge::nativeUnload);
            worker.shutdown();
        }
    }
}
