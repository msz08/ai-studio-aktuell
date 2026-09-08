package com.example

import android.accessibilityservice.AccessibilityService
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import android.os.Bundle
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo

class TvTextAccessibilityService : AccessibilityService() {

    private val receiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            if (intent?.action == "com.example.action.INJECT_TEXT") {
                val msg = intent.getStringExtra("msg") ?: ""
                val replace = intent.getBooleanExtra("replace", true)
                val action = intent.getStringExtra("action") ?: ""

                when (action) {
                    "enter" -> handleEnter()
                    "backspace" -> handleBackspace()
                    "clear" -> clearText()
                    else -> if (msg.isNotBlank()) injectText(msg, replace)
                }
            }
        }
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        val filter = IntentFilter("com.example.action.INJECT_TEXT")
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(receiver, filter, Context.RECEIVER_EXPORTED)
        } else {
            registerReceiver(receiver, filter)
        }
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}
    
    override fun onKeyEvent(event: android.view.KeyEvent?): Boolean {
        return super.onKeyEvent(event)
    }

    override fun onInterrupt() {}

    override fun onDestroy() {
        super.onDestroy()
        unregisterReceiver(receiver)
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
