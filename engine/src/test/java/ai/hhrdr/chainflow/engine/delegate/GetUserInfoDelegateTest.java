package ai.hhrdr.chainflow.engine.delegate;

import lombok.extern.slf4j.Slf4j;
import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.*;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@Slf4j
@ExtendWith(MockitoExtension.class)
public class GetUserInfoDelegateTest {

    @Mock
    private DelegateExecution execution;

    private GetUserInfoDelegate delegate;

    @BeforeEach
    public void setUp() {
        log.info("Setting up test environment");
        delegate = new GetUserInfoDelegate();

        ReflectionTestUtils.setField(delegate, "apiURL", "http://test-api.com");
        ReflectionTestUtils.setField(delegate, "apiKey", "test-api-key");
        ReflectionTestUtils.setField(delegate, "applicationUrl", "https://test-app.com");
        log.info("Test environment setup completed");
    }

    @Test
    public void testExecuteWithCompleteUserData() throws Exception {
        log.info("Starting test: testExecuteWithCompleteUserData");

        String camundaUserId = "user123";
        JSONObject mockUserData = createMockUserData(camundaUserId);
        log.info("Created mock user data for user ID: {}", camundaUserId);

        when(execution.getVariable("camunda_user_id")).thenReturn(camundaUserId);
        log.info("Mocked camunda_user_id variable to return: {}", camundaUserId);

        try (MockedStatic<HttpClient> httpClientMockedStatic = Mockito.mockStatic(HttpClient.class)) {
            HttpClient mockHttpClient = mock(HttpClient.class);
            @SuppressWarnings("unchecked")
            HttpResponse<String> mockResponse = mock(HttpResponse.class);

            httpClientMockedStatic.when(HttpClient::newHttpClient).thenReturn(mockHttpClient);
            log.info("Mocked HttpClient.newHttpClient() to return mock client");

            doAnswer(invocation -> {
                log.info("Mock HttpClient.send() was called");
                return mockResponse;
            }).when(mockHttpClient).send(any(HttpRequest.class), any());

            when(mockResponse.body()).thenReturn(mockUserData.toString());
            log.info("Configured mock response body with user data");

            log.info("Executing GetUserInfoDelegate.execute()");
            delegate.execute(execution);
            log.info("Execution completed successfully");

            log.info("Verifying execution variables were set correctly");
            verify(execution).setVariable(eq("telegram_user_id"), eq(123456L));
            verify(execution).setVariable(eq("username"), eq("testuser"));
            verify(execution).setVariable(eq("isBlock"), eq(false));
            verify(execution).setVariable(eq("user_id"), eq("user123"));
            verify(execution).setVariable(eq("webapp_user_id"), eq("user123"));
            verify(execution).setVariable(eq("user_is_admin"), eq(true));
            verify(execution).setVariable(eq("user_is_premium"), eq(true));
            verify(execution).setVariable(eq("wallet_address"), eq("0x1234567890abcdef"));
            verify(execution).setVariable(eq("invite_link"),
                    eq("https://test-app.com?ref=user123"));
            log.info("All variable verifications passed");
        }
        log.info("Test completed: testExecuteWithCompleteUserData");
    }

    @Test
    public void testExecuteWithNoGuruWallet() throws Exception {
        log.info("Starting test: testExecuteWithNoGuruWallet");

        String camundaUserId = "user456";
        JSONObject mockUserData = createMockUserDataWithoutGuruWallet(camundaUserId);
        log.info("Created mock user data without guru wallet for user ID: {}", camundaUserId);

        when(execution.getVariable("camunda_user_id")).thenReturn(camundaUserId);
        log.info("Mocked camunda_user_id variable to return: {}", camundaUserId);

        try (MockedStatic<HttpClient> httpClientMockedStatic = Mockito.mockStatic(HttpClient.class)) {
            HttpClient mockHttpClient = mock(HttpClient.class);
            @SuppressWarnings("unchecked")
            HttpResponse<String> mockResponse = mock(HttpResponse.class);

            httpClientMockedStatic.when(HttpClient::newHttpClient).thenReturn(mockHttpClient);
            log.info("Mocked HttpClient.newHttpClient() to return mock client");

            doAnswer(invocation -> {
                log.info("Mock HttpClient.send() was called");
                return mockResponse;
            }).when(mockHttpClient).send(any(HttpRequest.class), any());

            when(mockResponse.body()).thenReturn(mockUserData.toString());
            log.info("Configured mock response body with user data (no guru wallet)");

            log.info("Executing GetUserInfoDelegate.execute()");
            delegate.execute(execution);
            log.info("Execution completed successfully");

            log.info("Verifying wallet_address was NOT set");
            verify(execution, never()).setVariable(eq("wallet_address"), any());

            log.info("Verifying other variables are set correctly");
            verify(execution).setVariable(eq("telegram_user_id"), eq(123456L));
            verify(execution).setVariable(eq("username"), eq("testuser"));
            verify(execution).setVariable(eq("isBlock"), eq(false));
            verify(execution).setVariable(eq("user_id"), eq("user456"));
            verify(execution).setVariable(eq("webapp_user_id"), eq("user456"));
            verify(execution).setVariable(eq("user_is_admin"), eq(true));
            verify(execution).setVariable(eq("user_is_premium"), eq(true));
            verify(execution).setVariable(eq("invite_link"),
                    eq("https://test-app.com?ref=user456"));
            log.info("All variable verifications passed");
        }
        log.info("Test completed: testExecuteWithNoGuruWallet");
    }

    @Test
    public void testExecuteWithNullTelegramId() throws Exception {
        log.info("Starting test: testExecuteWithNullTelegramId");

        String camundaUserId = "user789";
        JSONObject mockUserData = createMockUserDataWithNullTelegramId(camundaUserId);
        log.info("Created mock user data with null Telegram ID for user ID: {}", camundaUserId);

        when(execution.getVariable("camunda_user_id")).thenReturn(camundaUserId);
        log.info("Mocked camunda_user_id variable to return: {}", camundaUserId);

        try (MockedStatic<HttpClient> httpClientMockedStatic = Mockito.mockStatic(HttpClient.class)) {
            HttpClient mockHttpClient = mock(HttpClient.class);
            @SuppressWarnings("unchecked")
            HttpResponse<String> mockResponse = mock(HttpResponse.class);

            httpClientMockedStatic.when(HttpClient::newHttpClient).thenReturn(mockHttpClient);
            log.info("Mocked HttpClient.newHttpClient() to return mock client");

            doAnswer(invocation -> {
                log.info("Mock HttpClient.send() was called");
                return mockResponse;
            }).when(mockHttpClient).send(any(HttpRequest.class), any());

            when(mockResponse.body()).thenReturn(mockUserData.toString());
            log.info("Configured mock response body with user data (null Telegram ID)");

            log.info("Executing GetUserInfoDelegate.execute()");
            delegate.execute(execution);
            log.info("Execution completed successfully");

            log.info("Verifying telegram_user_id was set to null");
            verify(execution).setVariable(eq("telegram_user_id"), eq(null));
            log.info("Variable verification passed");
        }
        log.info("Test completed: testExecuteWithNullTelegramId");
    }

    @Test
    public void testExecuteWithApiException() throws Exception {
        log.info("Starting test: testExecuteWithApiException");

        String camundaUserId = "user789";
        log.info("Using user ID: {} for exception test", camundaUserId);

        when(execution.getVariable("camunda_user_id")).thenReturn(camundaUserId);
        log.info("Mocked camunda_user_id variable to return: {}", camundaUserId);

        try (MockedStatic<HttpClient> httpClientMockedStatic = Mockito.mockStatic(HttpClient.class)) {
            HttpClient mockHttpClient = mock(HttpClient.class);

            httpClientMockedStatic.when(HttpClient::newHttpClient).thenReturn(mockHttpClient);
            log.info("Mocked HttpClient.newHttpClient() to return mock client");

            RuntimeException apiException = new RuntimeException("API Error");
            doThrow(apiException)
                    .when(mockHttpClient).send(any(HttpRequest.class), any());
            log.info("Configured mock HttpClient.send() to throw exception: {}", apiException.getMessage());

            log.info("Executing GetUserInfoDelegate.execute() and expecting exception");
            Exception thrownException = assertThrows(RuntimeException.class, () -> delegate.execute(execution));
            log.info("Caught expected exception: {}", thrownException.getMessage());
            assertEquals("API Error", thrownException.getMessage());
            log.info("Exception message matched expected value");
        }
        log.info("Test completed: testExecuteWithApiException");
    }

    private JSONObject createMockUserData(String userId) throws JSONException {
        log.info("Creating mock user data with guru wallet for userId: {}", userId);
        JSONObject userData = new JSONObject();
        userData.put("telegram_user_id", 123456L);
        userData.put("username", "testuser");
        userData.put("is_block", false);
        userData.put("id", userId);
        userData.put("webapp_user_id", userId);
        userData.put("is_admin", true);
        userData.put("is_premium", true);

        JSONArray walletsArray = new JSONArray();
        JSONObject wallet = new JSONObject();
        wallet.put("network_type", "thirdweb_ecosystem");
        wallet.put("wallet_address", "0x1234567890abcdef");
        walletsArray.put(wallet);

        userData.put("web3_wallets", walletsArray);
        log.info("Mock user data created successfully");

        return userData;
    }

    private JSONObject createMockUserDataWithoutGuruWallet(String userId) throws JSONException {
        log.info("Creating mock user data without guru wallet for userId: {}", userId);
        JSONObject userData = new JSONObject();
        userData.put("telegram_user_id", 123456L);
        userData.put("username", "testuser");
        userData.put("is_block", false);
        userData.put("id", userId);
        userData.put("webapp_user_id", userId);
        userData.put("is_admin", true);
        userData.put("is_premium", true);

        JSONArray walletsArray = new JSONArray();
        JSONObject wallet = new JSONObject();
        wallet.put("network_type", "ethereum");
        wallet.put("wallet_address", "0x0987654321fedcba");
        walletsArray.put(wallet);

        userData.put("web3_wallets", walletsArray);
        log.info("Mock user data (without guru wallet) created successfully");

        return userData;
    }

    private JSONObject createMockUserDataWithNullTelegramId(String userId) throws JSONException {
        log.info("Creating mock user data with null Telegram ID for userId: {}", userId);
        JSONObject userData = new JSONObject();
        userData.put("telegram_user_id", JSONObject.NULL);
        userData.put("username", "testuser");
        userData.put("is_block", false);
        userData.put("id", userId);
        userData.put("webapp_user_id", userId);
        userData.put("is_admin", true);
        userData.put("is_premium", true);

        JSONArray walletsArray = new JSONArray();
        JSONObject wallet = new JSONObject();
        wallet.put("network_type", "thirdweb_ecosystem");
        wallet.put("wallet_address", "0x1234567890abcdef");
        walletsArray.put(wallet);

        userData.put("web3_wallets", walletsArray);
        log.info("Mock user data with null Telegram ID created successfully");

        return userData;
    }
}