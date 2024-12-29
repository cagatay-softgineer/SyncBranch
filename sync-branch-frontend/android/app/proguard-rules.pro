# Don’t warn about missing errorprone annotations 
-dontwarn com.google.errorprone.annotations.**
-keep class com.google.errorprone.annotations.** { *; }

# Don’t warn about missing javax.annotation
-dontwarn javax.annotation.**
-keep class javax.annotation.** { *; }

# If you see references to concurrency annotations
-dontwarn javax.annotation.concurrent.**
-keep class javax.annotation.concurrent.** { *; }
