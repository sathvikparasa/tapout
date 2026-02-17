package com.warnabrotha.app.data.repository

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import androidx.test.core.app.ApplicationProvider
import io.mockk.every
import io.mockk.mockkConstructor
import io.mockk.mockkStatic
import io.mockk.mockk
import io.mockk.unmockkAll
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [33])
class TokenRepositoryTest {

    private lateinit var tokenRepository: TokenRepository
    private lateinit var testPrefs: SharedPreferences

    @Before
    fun setUp() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        testPrefs = context.getSharedPreferences("test_prefs", Context.MODE_PRIVATE)
        testPrefs.edit().clear().commit()

        mockkConstructor(MasterKey.Builder::class)
        val mockMasterKey = mockk<MasterKey>()
        every { anyConstructed<MasterKey.Builder>().setKeyScheme(any()) } returns mockk {
            every { build() } returns mockMasterKey
        }

        mockkStatic(EncryptedSharedPreferences::class)
        every {
            EncryptedSharedPreferences.create(
                any<Context>(), any(), any(), any(), any()
            )
        } returns testPrefs

        tokenRepository = TokenRepository(context)
    }

    @After
    fun tearDown() {
        unmockkAll()
    }

    @Test
    fun saveAndGetToken() {
        tokenRepository.saveToken("abc")
        assertEquals("abc", tokenRepository.getToken())
    }

    @Test
    fun getTokenWhenNoneSaved() {
        assertNull(tokenRepository.getToken())
    }

    @Test
    fun clearToken() {
        tokenRepository.saveToken("temp")
        tokenRepository.clearToken()
        assertNull(tokenRepository.getToken())
    }

    @Test
    fun hasTokenTrue() {
        tokenRepository.saveToken("present")
        assertTrue(tokenRepository.hasToken())
    }

    @Test
    fun hasTokenFalse() {
        assertFalse(tokenRepository.hasToken())
    }

    @Test
    fun getOrCreateDeviceIdCreates() {
        val deviceId = tokenRepository.getOrCreateDeviceId()
        assertEquals(36, deviceId.length)
        assertTrue(deviceId.matches(Regex("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")))
    }

    @Test
    fun getOrCreateDeviceIdStable() {
        val first = tokenRepository.getOrCreateDeviceId()
        val second = tokenRepository.getOrCreateDeviceId()
        assertEquals(first, second)
    }

    @Test
    fun saveAndGetPushToken() {
        tokenRepository.savePushToken("push123")
        assertEquals("push123", tokenRepository.getPushToken())
    }

    @Test
    fun getPushTokenWhenNone() {
        assertNull(tokenRepository.getPushToken())
    }
}
