package com.batcontroller;

import android.annotation.SuppressLint;
import android.app.AlertDialog;
import android.graphics.Bitmap;
import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import android.webkit.CookieManager;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.HashMap;
import java.util.Map;

/**
 * BAT 任务控制 App
 * 通过 WebView 加载电脑端的控制面板
 */
public class MainActivity extends android.app.Activity {

    private WebView webView;
    private TextView statusText;
    private String serverUrl;
    private String token;
    private static final String PREFS_NAME = "BatControllerPrefs";
    private static final String KEY_URL = "server_url";
    private static final String KEY_TOKEN = "server_token";
    private static final String DEFAULT_URL = "http://192.168.1.100:8010";

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // 保持屏幕常亮
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        webView = findViewById(R.id.webview);
        statusText = findViewById(R.id.status_text);
        ImageButton btnSettings = findViewById(R.id.btn_settings);
        ImageButton btnRefresh = findViewById(R.id.btn_refresh);

        // 加载保存的 URL 和令牌
        serverUrl = getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
                .getString(KEY_URL, DEFAULT_URL);
        token = getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
                .getString(KEY_TOKEN, "");

        // 设置按钮
        btnSettings.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                showUrlDialog();
            }
        });

        btnRefresh.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (webView != null) {
                    webView.reload();
                }
            }
        });

        // 配置 WebView
        setupWebView();
    }

    @SuppressLint("SetJavaScriptEnabled")
    private void setupWebView() {
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(true);
        settings.setSupportZoom(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);

        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, true);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageStarted(WebView view, String url, Bitmap favicon) {
                statusText.setText("正在连接...");
                statusText.setVisibility(View.VISIBLE);
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                statusText.setVisibility(View.GONE);
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                // 仅主页面加载失败才提示，子资源（图片、JS 等）失败不误报
                if (request.isForMainFrame()) {
                    statusText.setText("连接失败 - 请检查网络和服务器地址");
                    statusText.setVisibility(View.VISIBLE);
                }
            }

            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                // 配置了令牌时，为所有请求附加 X-Auth-Token 头
                if (token != null && !token.isEmpty()) {
                    try {
                        URL url = new URL(request.getUrl().toString());
                        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                        conn.setRequestProperty("X-Auth-Token", token);
                        conn.setInstanceFollowRedirects(false);
                        int code = conn.getResponseCode();
                        InputStream is = code >= 400 ? conn.getErrorStream() : conn.getInputStream();
                        Map<String, String> headers = new HashMap<>();
                        headers.put("Access-Control-Allow-Origin", "*");
                        return new WebResourceResponse(
                                guessMimeType(url.getPath()), "UTF-8", code,
                                code >= 400 ? "Error" : "OK", headers, is);
                    } catch (Exception e) {
                        return super.shouldInterceptRequest(view, request);
                    }
                }
                return super.shouldInterceptRequest(view, request);
            }
        });

        webView.setWebChromeClient(new WebChromeClient());
        webView.loadUrl(serverUrl);
    }

    private void showUrlDialog() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(48, 32, 48, 32);

        EditText urlInput = new EditText(this);
        urlInput.setHint("服务器地址，例如 http://192.168.1.100:8010");
        urlInput.setSingleLine(true);
        urlInput.setText(serverUrl);
        layout.addView(urlInput);

        EditText tokenInput = new EditText(this);
        tokenInput.setHint("X-Auth-Token（可选）");
        tokenInput.setSingleLine(true);
        tokenInput.setText(token);
        layout.addView(tokenInput);

        new AlertDialog.Builder(this)
                .setTitle("服务器设置")
                .setView(layout)
                .setPositiveButton("保存", (dialog, which) -> {
                    serverUrl = urlInput.getText().toString().trim();
                    token = tokenInput.getText().toString().trim();
                    getSharedPreferences(PREFS_NAME, MODE_PRIVATE).edit()
                            .putString(KEY_URL, serverUrl)
                            .putString(KEY_TOKEN, token)
                            .apply();
                    webView.loadUrl(serverUrl);
                })
                .setNegativeButton("取消", null)
                .show();
    }

    private String guessMimeType(String path) {
        if (path == null) return "application/octet-stream";
        String lower = path.toLowerCase();
        if (lower.endsWith(".html") || lower.endsWith(".htm")) return "text/html";
        if (lower.endsWith(".css")) return "text/css";
        if (lower.endsWith(".js")) return "application/javascript";
        if (lower.endsWith(".json")) return "application/json";
        if (lower.endsWith(".png")) return "image/png";
        if (lower.endsWith(".jpg") || lower.endsWith(".jpeg")) return "image/jpeg";
        if (lower.endsWith(".svg")) return "image/svg+xml";
        return "application/octet-stream";
    }
}
