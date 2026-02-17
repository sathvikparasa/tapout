package com.warnabrotha.app.data.api

import com.warnabrotha.app.data.model.*
import com.warnabrotha.app.data.repository.TokenRepository
import io.mockk.every
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import okhttp3.OkHttpClient
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class ApiServiceTest {

    private lateinit var mockWebServer: MockWebServer
    private lateinit var apiService: ApiService

    @Before
    fun setUp() {
        mockWebServer = MockWebServer()
        mockWebServer.start()

        apiService = Retrofit.Builder()
            .baseUrl(mockWebServer.url("/"))
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ApiService::class.java)
    }

    @After
    fun tearDown() {
        mockWebServer.shutdown()
    }

    @Test
    fun registerSendsCorrectRequest() = runTest {
        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setBody("""{"access_token":"tok","token_type":"bearer","expires_in":3600}""")
        )

        apiService.register(DeviceRegistration("device-123", "push-tok"))

        val request = mockWebServer.takeRequest()
        assertEquals("POST", request.method)
        assertEquals("/auth/register", request.path)
        val body = request.body.readUtf8()
        assertTrue(body.contains("\"device_id\":\"device-123\""))
        assertTrue(body.contains("\"push_token\":\"push-tok\""))
    }

    @Test
    fun registerParsesResponse() = runTest {
        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setBody("""{"access_token":"my-jwt-token","token_type":"bearer","expires_in":7200}""")
        )

        val response = apiService.register(DeviceRegistration("dev-1"))

        assertTrue(response.isSuccessful)
        val body = response.body()!!
        assertEquals("my-jwt-token", body.accessToken)
        assertEquals("bearer", body.tokenType)
        assertEquals(7200, body.expiresIn)
    }

    @Test
    fun sendOTPSendsCorrectRequest() = runTest {
        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setBody("""{"success":true,"message":"OTP sent"}""")
        )

        apiService.sendOTP(SendOTPRequest("user@ucdavis.edu", "dev-1"))

        val request = mockWebServer.takeRequest()
        assertEquals("POST", request.method)
        assertEquals("/auth/send-otp", request.path)
        val body = request.body.readUtf8()
        assertTrue(body.contains("\"email\":\"user@ucdavis.edu\""))
        assertTrue(body.contains("\"device_id\":\"dev-1\""))
    }

    @Test
    fun verifyOTPSendsCorrectRequest() = runTest {
        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setBody("""{"success":true,"message":"Verified","email_verified":true,"access_token":"tok","token_type":"bearer","expires_in":3600}""")
        )

        apiService.verifyOTP(VerifyOTPRequest("user@ucdavis.edu", "dev-1", "123456"))

        val request = mockWebServer.takeRequest()
        assertEquals("POST", request.method)
        assertEquals("/auth/verify-otp", request.path)
        val body = request.body.readUtf8()
        assertTrue(body.contains("\"email\":\"user@ucdavis.edu\""))
        assertTrue(body.contains("\"device_id\":\"dev-1\""))
        assertTrue(body.contains("\"otp_code\":\"123456\""))
    }

    @Test
    fun getParkingLotsParsesList() = runTest {
        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setBody("""[
                    {"id":1,"name":"Lot A","code":"LOT_A","latitude":38.54,"longitude":-121.74,"is_active":true},
                    {"id":2,"name":"Lot B","code":"LOT_B","latitude":38.55,"longitude":-121.75,"is_active":true}
                ]""")
        )

        val response = apiService.getParkingLots()

        assertTrue(response.isSuccessful)
        val lots = response.body()!!
        assertEquals(2, lots.size)
        assertEquals("Lot A", lots[0].name)
        assertEquals("LOT_B", lots[1].code)
    }

    @Test
    fun checkInSendsLotId() = runTest {
        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(201)
                .setBody("""{"id":1,"parking_lot_id":5,"parking_lot_name":"Lot A","parking_lot_code":"LOT_A","checked_in_at":"2025-01-15T10:00:00Z","checked_out_at":null,"is_active":true,"reminder_sent":false}""")
        )

        apiService.checkIn(ParkingSessionCreate(5))

        val request = mockWebServer.takeRequest()
        assertEquals("POST", request.method)
        assertEquals("/sessions/checkin", request.path)
        val body = request.body.readUtf8()
        assertTrue(body.contains("\"parking_lot_id\":5"))
    }

    @Test
    fun reportSightingSendsNotes() = runTest {
        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(201)
                .setBody("""{"id":1,"parking_lot_id":1,"parking_lot_name":"Lot A","parking_lot_code":"LOT_A","reported_at":"2025-01-15T11:00:00Z","notes":"Near entrance","users_notified":2}""")
        )

        apiService.reportSighting(SightingCreate(1, "Near entrance"))

        val request = mockWebServer.takeRequest()
        assertEquals("POST", request.method)
        assertEquals("/sightings", request.path)
        val body = request.body.readUtf8()
        assertTrue(body.contains("\"parking_lot_id\":1"))
        assertTrue(body.contains("\"notes\":\"Near entrance\""))
    }

    @Test
    fun voteSendsCorrectType() = runTest {
        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setBody("""{"success":true,"action":"created","vote_type":"upvote"}""")
        )

        apiService.vote(42, VoteCreate("upvote"))

        val request = mockWebServer.takeRequest()
        assertEquals("POST", request.method)
        assertEquals("/feed/sightings/42/vote", request.path)
        val body = request.body.readUtf8()
        assertTrue(body.contains("\"vote_type\":\"upvote\""))
    }

    @Test
    fun errorResponseHandling() = runTest {
        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(400)
                .setBody("""{"detail":"Bad request"}""")
        )

        val response = apiService.register(DeviceRegistration("dev-1"))

        assertFalse(response.isSuccessful)
        assertEquals(400, response.code())
    }

    @Test
    fun authHeaderSent() = runTest {
        val tokenRepository = mockk<TokenRepository>()
        every { tokenRepository.getToken() } returns "my-secret-token"

        val client = OkHttpClient.Builder()
            .addInterceptor(AuthInterceptor(tokenRepository))
            .build()

        val serviceWithAuth = Retrofit.Builder()
            .baseUrl(mockWebServer.url("/"))
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ApiService::class.java)

        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setBody("""[]""")
        )

        serviceWithAuth.getParkingLots()

        val request = mockWebServer.takeRequest()
        assertEquals("Bearer my-secret-token", request.getHeader("Authorization"))
    }
}
