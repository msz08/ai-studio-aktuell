plugins {
    id("com.android.application")
    // org.jetbrains.kotlin.android is applied automatically by AGP 9.x (builtInKotlin=true)
}
android {
    namespace = "com.porter.tvremote"
    compileSdk = 36
    defaultConfig {
        applicationId = "com.porter.tvremote.receiver"
        minSdk = 26
        targetSdk = 36
        versionCode = 6
        versionName = "1.5"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_21
        targetCompatibility = JavaVersion.VERSION_21
    }
}
kotlin {
    jvmToolchain(21)
}
dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
    implementation("androidx.leanback:leanback:1.0.0")
}
