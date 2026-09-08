package com.example

import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
                    Column(
                        modifier = Modifier.fillMaxSize().padding(16.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Text("TV Text Empfänger (ADB)", style = MaterialTheme.typography.headlineMedium)
                        Spacer(modifier = Modifier.height(16.dp))
                        Text("1. Klicke auf den Button unten, um die Android-Bedienungshilfen zu öffnen.")
                        Text("2. Aktiviere den Dienst 'TV Text'.")
                        Spacer(modifier = Modifier.height(16.dp))
                        Text("Die App wartet nun unsichtbar im Hintergrund auf ADB Broadcasts.")
                        Spacer(modifier = Modifier.height(8.dp))
                        Text("Beispiel-Befehl für den Raspberry Pi / Legvan:", style = MaterialTheme.typography.labelLarge)
                        Text("adb shell am broadcast -a com.example.action.INJECT_TEXT -e msg 'Hallo'", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.primary)
                        Spacer(modifier = Modifier.height(32.dp))
                        Button(onClick = {
                            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
                        }) {
                            Text("Einstellungen öffnen")
                        }
                    }
                }
            }
        }
    }
}
