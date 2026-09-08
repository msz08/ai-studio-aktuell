package com.porter.tvremote

import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        findViewById<TextView>(R.id.status_text).text = 
            "Legvan TV Text Receiver (Pi Edition)\n\n" +
            "This app just acts as an accessibility service for the Raspberry Pi.\n" +
            "Please enable it in Settings -> Accessibility."

        findViewById<Button>(R.id.start_stop_button).apply {
            text = "Open Accessibility Settings"
            setOnClickListener {
                startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
            }
        }
    }
}
