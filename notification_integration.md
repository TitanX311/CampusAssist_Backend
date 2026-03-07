# Campus Assist — Android Notification Integration

## Overview

The notification service exposes two real-time channels and a full REST API:

| Channel | When to use |
|---------|-------------|
| **WebSocket** `wss://host/api/notifications/ws?token=<jwt>` | App is open/foreground |
| **FCM push** via stored device token | App is backgrounded or closed |
| **REST** `GET /api/notifications` | On app open — catch up on missed |

---

## Base URLs

```
REST + WebSocket : http://172.21.11.121:8080
WebSocket scheme : ws://172.21.11.121:8080   (wss:// in production)
```

---

## Authentication

Every REST call requires:
```
Authorization: Bearer <jwt_token>
```
The WebSocket passes the token as a query parameter:
```
ws://172.21.11.121:8080/api/notifications/ws?token=<jwt_token>
```

---

## REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/notifications` | List notifications (paginated) |
| `GET` | `/api/notifications/unread-count` | Get unread badge count |
| `POST` | `/api/notifications/{id}/read` | Mark one notification read |
| `POST` | `/api/notifications/read-all` | Mark all notifications read |
| `DELETE` | `/api/notifications/{id}` | Delete a notification |
| `POST` | `/api/notifications/device-token` | Register FCM device token |
| `DELETE` | `/api/notifications/device-token` | Unregister FCM token (on logout) |

### Query params for `GET /api/notifications`

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page (max 100) |
| `unread_only` | bool | false | Filter to unread only |

### Notification types

| `type` value | Triggered when |
|---|---|
| `LIKE_POST` | Someone liked your post |
| `COMMENT_POST` | Someone commented on your post |
| `LIKE_COMMENT` | Someone liked your comment |
| `REPLY_COMMENT` | Someone replied to your comment |
| `JOIN_REQUEST` | Someone requested to join your community |
| `JOIN_ACCEPTED` | Your join request was accepted |
| `NEW_POST` | New post in a community you follow |

### Sample response object

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "type": "LIKE_POST",
  "title": "New like",
  "body": "Rahul liked your post",
  "data": {
    "post_id": "abc123",
    "actor_id": "xyz789"
  },
  "read": false,
  "created_at": "2026-03-07T10:30:00Z"
}
```

---

## Gradle Dependencies

```kotlin
// build.gradle.kts (app)
dependencies {
    // Networking
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")

    // Firebase
    implementation(platform("com.google.firebase:firebase-bom:32.7.4"))
    implementation("com.google.firebase:firebase-messaging-ktx")

    // Coroutines + ViewModel
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.7.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.7.0")
}
```

---

## Project Structure

```
app/
├── data/
│   ├── model/
│   │   └── NotificationModels.kt       ← data classes
│   ├── remote/
│   │   ├── NotificationApi.kt          ← Retrofit interface
│   │   └── RetrofitClient.kt           ← singleton Retrofit instance
│   └── repository/
│       └── NotificationRepository.kt  ← single source of truth
├── service/
│   ├── WebSocketManager.kt             ← OkHttp WebSocket + reconnect
│   └── MyFirebaseService.kt            ← FCM token refresh + message handling
└── ui/
    └── notifications/
        ├── NotificationViewModel.kt    ← StateFlow, marks read, load more
        └── NotificationFragment.kt     ← RecyclerView + badge
```

---

## Step 1 — Data Models

```kotlin
// data/model/NotificationModels.kt
data class NotificationResponse(
    val id: String,
    @SerializedName("user_id")    val userId: String,
    val type: String,
    val title: String,
    val body: String,
    val data: Map<String, Any>?,
    val read: Boolean,
    @SerializedName("created_at") val createdAt: String
)

data class NotificationListResponse(
    val items: List<NotificationResponse>,
    val total: Int,
    @SerializedName("unread_count") val unreadCount: Int
)

data class UnreadCountResponse(val count: Int)
data class DeviceTokenRequest(
    val token: String,
    val platform: String = "android"
)
data class MessageResponse(val message: String)
```

---

## Step 2 — Retrofit Interface

```kotlin
// data/remote/NotificationApi.kt
interface NotificationApi {

    @GET("api/notifications")
    suspend fun list(
        @Query("page")        page: Int            = 1,
        @Query("page_size")   pageSize: Int         = 20,
        @Query("unread_only") unreadOnly: Boolean   = false
    ): NotificationListResponse

    @GET("api/notifications/unread-count")
    suspend fun unreadCount(): UnreadCountResponse

    @POST("api/notifications/{id}/read")
    suspend fun markRead(@Path("id") id: String): NotificationResponse

    @POST("api/notifications/read-all")
    suspend fun markAllRead(): MessageResponse

    @DELETE("api/notifications/{id}")
    suspend fun delete(@Path("id") id: String): MessageResponse

    @POST("api/notifications/device-token")
    suspend fun registerDeviceToken(@Body body: DeviceTokenRequest): MessageResponse

    @DELETE("api/notifications/device-token")
    suspend fun unregisterDeviceToken(): MessageResponse
}
```

---

## Step 3 — Retrofit Client

```kotlin
// data/remote/RetrofitClient.kt
object RetrofitClient {
    private const val BASE_URL = "http://172.21.11.121:8080/"

    fun build(tokenProvider: () -> String?): NotificationApi {
        val client = OkHttpClient.Builder()
            .addInterceptor { chain ->
                val token = tokenProvider()
                val req = if (token != null)
                    chain.request().newBuilder()
                        .addHeader("Authorization", "Bearer $token")
                        .build()
                else chain.request()
                chain.proceed(req)
            }
            .addInterceptor(HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            })
            .build()

        return Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(NotificationApi::class.java)
    }
}
```

---

## Step 4 — WebSocket Manager

```kotlin
// service/WebSocketManager.kt
class WebSocketManager(
    private val baseUrl: String = "ws://172.21.11.121:8080",
    private val tokenProvider: () -> String?
) {
    private val client = OkHttpClient.Builder()
        .pingInterval(30, TimeUnit.SECONDS)
        .build()

    private var ws: WebSocket? = null
    private var reconnectDelay = 1_000L

    var onNotification: ((NotificationResponse) -> Unit)? = null
    var onConnected:    (() -> Unit)?                     = null
    var onDisconnected: (() -> Unit)?                     = null

    fun connect() {
        val token = tokenProvider() ?: return
        val request = Request.Builder()
            .url("$baseUrl/api/notifications/ws?token=$token")
            .build()

        ws = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(ws: WebSocket, response: Response) {
                reconnectDelay = 1_000L
                onConnected?.invoke()
            }

            override fun onMessage(ws: WebSocket, text: String) {
                runCatching {
                    Gson().fromJson(text, NotificationResponse::class.java)
                }.onSuccess { onNotification?.invoke(it) }
            }

            override fun onClosing(ws: WebSocket, code: Int, reason: String) {
                ws.close(1000, null)
                onDisconnected?.invoke()
            }

            override fun onFailure(ws: WebSocket, t: Throwable, res: Response?) {
                onDisconnected?.invoke()
                scheduleReconnect()
            }
        })
    }

    fun disconnect() {
        ws?.close(1000, "logout")
        ws = null
    }

    private fun scheduleReconnect() {
        Handler(Looper.getMainLooper()).postDelayed({
            reconnectDelay = minOf(reconnectDelay * 2, 30_000L)
            connect()
        }, reconnectDelay)
    }
}
```

---

## Step 5 — FCM Service

```kotlin
// service/MyFirebaseService.kt
class MyFirebaseService : FirebaseMessagingService() {

    override fun onNewToken(token: String) {
        CoroutineScope(Dispatchers.IO).launch {
            runCatching {
                val jwt = getSharedPreferences("auth", MODE_PRIVATE)
                    .getString("jwt", null) ?: return@launch
                RetrofitClient.build { jwt }
                    .registerDeviceToken(DeviceTokenRequest(token))
            }
        }
    }

    override fun onMessageReceived(message: RemoteMessage) {
        val title = message.data["title"] ?: message.notification?.title ?: return
        val body  = message.data["body"]  ?: message.notification?.body  ?: return
        showNotification(title, body, message.data)
    }

    private fun showNotification(
        title: String,
        body: String,
        data: Map<String, String>
    ) {
        val channelId = "campus_assist"
        val manager = getSystemService(NOTIFICATION_SERVICE) as NotificationManager

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            manager.createNotificationChannel(
                NotificationChannel(channelId, "Campus Assist",
                    NotificationManager.IMPORTANCE_DEFAULT)
            )
        }

        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_CLEAR_TOP
            data.forEach { (k, v) -> putExtra(k, v) }
        }
        val pending = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_ONE_SHOT or PendingIntent.FLAG_IMMUTABLE
        )

        manager.notify(
            System.currentTimeMillis().toInt(),
            NotificationCompat.Builder(this, channelId)
                .setSmallIcon(R.drawable.ic_notification)
                .setContentTitle(title)
                .setContentText(body)
                .setAutoCancel(true)
                .setContentIntent(pending)
                .build()
        )
    }
}
```

---

## Step 6 — ViewModel

```kotlin
// ui/notifications/NotificationViewModel.kt
class NotificationViewModel(
    private val api: NotificationApi,
    private val ws: WebSocketManager
) : ViewModel() {

    private val _items = MutableStateFlow<List<NotificationResponse>>(emptyList())
    val items: StateFlow<List<NotificationResponse>> = _items.asStateFlow()

    private val _unreadCount = MutableStateFlow(0)
    val unreadCount: StateFlow<Int> = _unreadCount.asStateFlow()

    private val _loading = MutableStateFlow(false)
    val loading: StateFlow<Boolean> = _loading.asStateFlow()

    init {
        connectWebSocket()
        viewModelScope.launch { load() }
    }

    private fun connectWebSocket() {
        ws.onNotification = { notification ->
            _items.value       = listOf(notification) + _items.value
            _unreadCount.value += 1
        }
        ws.connect()
    }

    suspend fun load(page: Int = 1) {
        _loading.value = true
        runCatching { api.list(page = page) }.onSuccess { res ->
            _items.value       = if (page == 1) res.items
                                 else _items.value + res.items
            _unreadCount.value = res.unreadCount
        }
        _loading.value = false
    }

    fun markRead(id: String) = viewModelScope.launch {
        runCatching { api.markRead(id) }.onSuccess {
            _items.value = _items.value.map { n ->
                if (n.id == id) n.copy(read = true) else n
            }
            _unreadCount.value = maxOf(0, _unreadCount.value - 1)
        }
    }

    fun markAllRead() = viewModelScope.launch {
        runCatching { api.markAllRead() }.onSuccess {
            _items.value       = _items.value.map { it.copy(read = true) }
            _unreadCount.value = 0
        }
    }

    fun delete(id: String) = viewModelScope.launch {
        runCatching { api.delete(id) }.onSuccess {
            _items.value = _items.value.filter { it.id != id }
        }
    }

    override fun onCleared() {
        ws.disconnect()
        super.onCleared()
    }
}
```

---

## Step 7 — AndroidManifest.xml

```xml
<!-- inside <application> -->
<service
    android:name=".service.MyFirebaseService"
    android:exported="false">
    <intent-filter>
        <action android:name="com.google.firebase.MESSAGING_EVENT" />
    </intent-filter>
</service>

<!-- permissions -->
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
```

---

## Step 8 — Login / Logout flow

```kotlin
// On login — register FCM token
suspend fun onLoginSuccess(jwt: String) {
    saveJwt(jwt)
    wsManager.connect()
    val fcmToken = FirebaseMessaging.getInstance().token.await()
    api.registerDeviceToken(DeviceTokenRequest(fcmToken))
}

// On logout — clean up both channels
suspend fun onLogout() {
    wsManager.disconnect()
    runCatching { api.unregisterDeviceToken() }
    clearJwt()
}
```

---

## Notification deep-link routing

Use the `data` map in each notification to route the user to the right screen:

```kotlin
when (notification.type) {
    "LIKE_POST", "COMMENT_POST" -> {
        val postId = notification.data?.get("post_id") as? String
        navController.navigate("post/$postId")
    }
    "REPLY_COMMENT", "LIKE_COMMENT" -> {
        val commentId = notification.data?.get("comment_id") as? String
        navController.navigate("comment/$commentId")
    }
    "JOIN_REQUEST" -> {
        val communityId = notification.data?.get("community_id") as? String
        navController.navigate("community/$communityId/requests")
    }
    "JOIN_ACCEPTED" -> {
        val communityId = notification.data?.get("community_id") as? String
        navController.navigate("community/$communityId")
    }
    "NEW_POST" -> {
        val communityId = notification.data?.get("community_id") as? String
        navController.navigate("community/$communityId/feed")
    }
}
```