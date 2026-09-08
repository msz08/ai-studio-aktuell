package com.example

import android.accessibilityservice.AccessibilityService
import android.os.Build
import android.os.Bundle
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import io.ktor.http.ContentType
import io.ktor.server.application.*
import io.ktor.server.cio.*
import io.ktor.server.engine.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import io.ktor.server.plugins.cors.routing.CORS
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch

class TvTextAccessibilityService : AccessibilityService() {
    private var server: EmbeddedServer<*, *>? = null
    private val serviceJob = Job()
    private val serviceScope = CoroutineScope(Dispatchers.IO + serviceJob)

    override fun onServiceConnected() {
        super.onServiceConnected()
        startServer()
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}
    
    override fun onKeyEvent(event: android.view.KeyEvent?): Boolean {
        return super.onKeyEvent(event)
    }

    override fun onInterrupt() {}

    override fun onDestroy() {
        super.onDestroy()
        server?.stop(1000, 2000)
        serviceJob.cancel()
    }

    private fun startServer() {
        serviceScope.launch {
            try {
                server = embeddedServer(CIO, port = 8080) {
                    install(CORS) {
                        anyHost()
                        allowHeader(io.ktor.http.HttpHeaders.ContentType)
                    }
                    routing {
                        get("/") {
                            val html = """
                                <!DOCTYPE html>
                                <html lang="de">
                                <head>
                                    <meta charset="utf-8">
                                    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
                                    <title>TV Fernbedienung</title>
                                    <style>
                                        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 20px; background: #f4f4f9; text-align: center; margin: 0; }
                                        .container { max-width: 600px; margin: 0 auto; background: white; padding: 24px; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
                                        h2 { color: #111; margin-top: 0; }
                                        input { width: 100%; padding: 16px; font-size: 18px; margin-bottom: 16px; border: 2px solid #ddd; border-radius: 12px; box-sizing: border-box; }
                                        input:focus { border-color: #007bff; outline: none; }
                                        .btn-row { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }
                                        button { flex: 1; min-width: 120px; background: #007bff; color: white; border: none; padding: 16px; font-size: 18px; font-weight: bold; border-radius: 12px; cursor: pointer; transition: background 0.2s; }
                                        button:active { background: #0056b3; }
                                        .btn-secondary { background: #6c757d; }
                                        .btn-danger { background: #dc3545; }
                                    </style>
                                </head>
                                <body>
                                    <div class="container">
                                        <h2>Text an TV senden</h2>
                                        <p style="font-size: 14px; color: #666; margin-top: -10px; margin-bottom: 20px;">Textfeld auf dem TV auswählen, dann hier tippen.</p>
                                        <input type="text" id="msg" placeholder="Text eingeben..." autofocus />
                                        <div class="btn-row">
                                            <button onclick="sendAction('/clear')" class="btn-danger" style="background: #ff9800;">✗ Feld leeren</button>
                                            <button onclick="sendAction('/backspace')" class="btn-danger">⌫ Zurück</button>
                                            <button onclick="sendAction('/enter')" class="btn-secondary">↵ Enter</button>
                                        </div>
                                        <div class="btn-row" style="margin-top: 12px;">
                                            <button onclick="sendText(false)" style="background: #17a2b8;">➕ Text anfügen</button>
                                            <button onclick="sendText(true)" style="background: #28a745;">🔄 Text ersetzen</button>
                                        </div>
                                    </div>
                                    <script>
                                        const input = document.getElementById('msg');
                                        input.addEventListener("keydown", function(event) {
                                            if (event.key === "Enter") {
                                                event.preventDefault();
                                                sendText(true);
                                            }
                                        });
                                        function sendText(replace = true) {
                                            let msg = input.value;
                                            if (!msg) return;
                                            fetch('/send', {
                                                method: 'POST',
                                                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                                                body: 'message=' + encodeURIComponent(msg) + '&replace=' + replace
                                            }).then(() => {
                                                input.value = '';
                                                input.focus();
                                            });
                                        }
                                        function sendAction(path) {
                                            fetch(path, { method: 'POST' }).then(() => {
                                                input.focus();
                                            });
                                        }
                                    </script>
                                </body>
                                </html>
                            """.trimIndent()
                            call.respondText(html, ContentType.Text.Html)
                        }
                        post("/send") {
                            val params = call.receiveParameters()
                            val msg = params["message"] ?: ""
                            val replace = params["replace"]?.toBoolean() ?: true
                            if (msg.isNotBlank()) injectText(msg, replace)
                            call.respondText("OK", ContentType.Text.Plain)
                        }
                        post("/enter") {
                            handleEnter()
                            call.respondText("OK", ContentType.Text.Plain)
                        }
                        post("/backspace") {
                            handleBackspace()
                            call.respondText("OK", ContentType.Text.Plain)
                        }
                        post("/clear") {
                            clearText()
                            call.respondText("OK", ContentType.Text.Plain)
                        }
                    }
                }.start(wait = false)
            } catch (e: Throwable) {
                e.printStackTrace()
            }
        }
    }

    private fun getFocusedNode(): AccessibilityNodeInfo? {
        val root = rootInActiveWindow ?: return null
        return root.findFocus(AccessibilityNodeInfo.FOCUS_INPUT)
    }

    private fun injectText(msg: String, replace: Boolean) {
        val node = getFocusedNode()
        if (node != null && node.isEditable) {
            val newText = if (replace) {
                msg
            } else {
                val currentText = node.text?.toString() ?: ""
                currentText + msg
            }
            val arguments = Bundle()
            arguments.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, newText)
            node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, arguments)
        }
    }

    private fun clearText() {
        val node = getFocusedNode()
        if (node != null && node.isEditable) {
            val arguments = Bundle()
            arguments.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, "")
            node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, arguments)
        }
    }

    private fun handleBackspace() {
        val node = getFocusedNode()
        if (node != null && node.isEditable) {
            val currentText = node.text?.toString() ?: ""
            if (currentText.isNotEmpty()) {
                val newText = currentText.dropLast(1)
                val arguments = Bundle()
                arguments.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, newText)
                node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, arguments)
            }
        }
    }

    private fun handleEnter() {
        val node = getFocusedNode()
        if (node != null) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                node.performAction(AccessibilityNodeInfo.AccessibilityAction.ACTION_IME_ENTER.id)
            }
        }
    }
}
