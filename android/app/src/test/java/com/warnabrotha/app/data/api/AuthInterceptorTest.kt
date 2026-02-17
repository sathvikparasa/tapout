package com.warnabrotha.app.data.api

import com.warnabrotha.app.data.repository.TokenRepository
import io.mockk.every
import io.mockk.mockk
import io.mockk.slot
import io.mockk.verify
import okhttp3.Interceptor
import okhttp3.Protocol
import okhttp3.Request
import okhttp3.Response
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

class AuthInterceptorTest {

    private lateinit var tokenRepository: TokenRepository
    private lateinit var authInterceptor: AuthInterceptor
    private lateinit var chain: Interceptor.Chain

    private val dummyResponse = Response.Builder()
        .code(200)
        .message("OK")
        .protocol(Protocol.HTTP_1_1)
        .request(Request.Builder().url("https://example.com").build())
        .build()

    @Before
    fun setUp() {
        tokenRepository = mockk()
        authInterceptor = AuthInterceptor(tokenRepository)
        chain = mockk()
    }

    @Test
    fun addsBearerToken() {
        every { tokenRepository.getToken() } returns "mytoken123"
        val request = Request.Builder().url("https://api.example.com/data").build()
        every { chain.request() } returns request

        val requestSlot = slot<Request>()
        every { chain.proceed(capture(requestSlot)) } returns dummyResponse

        authInterceptor.intercept(chain)

        assertEquals("Bearer mytoken123", requestSlot.captured.header("Authorization"))
    }

    @Test
    fun noTokenNoHeader() {
        every { tokenRepository.getToken() } returns null
        val request = Request.Builder().url("https://api.example.com/data").build()
        every { chain.request() } returns request

        val requestSlot = slot<Request>()
        every { chain.proceed(capture(requestSlot)) } returns dummyResponse

        authInterceptor.intercept(chain)

        assertNull(requestSlot.captured.header("Authorization"))
    }

    @Test
    fun replacesExistingAuthHeader() {
        every { tokenRepository.getToken() } returns "newtoken"
        val request = Request.Builder()
            .url("https://api.example.com/data")
            .header("Authorization", "Basic oldcreds")
            .build()
        every { chain.request() } returns request

        val requestSlot = slot<Request>()
        every { chain.proceed(capture(requestSlot)) } returns dummyResponse

        authInterceptor.intercept(chain)

        assertEquals("Bearer newtoken", requestSlot.captured.header("Authorization"))
    }

    @Test
    fun passesRequestToChain() {
        every { tokenRepository.getToken() } returns "token"
        val request = Request.Builder().url("https://api.example.com/data").build()
        every { chain.request() } returns request
        every { chain.proceed(any()) } returns dummyResponse

        val result = authInterceptor.intercept(chain)

        verify(exactly = 1) { chain.proceed(any()) }
        assertEquals(dummyResponse, result)
    }
}
