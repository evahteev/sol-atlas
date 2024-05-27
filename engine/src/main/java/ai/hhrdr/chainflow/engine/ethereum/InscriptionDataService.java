package ai.hhrdr.chainflow.engine.ethereum;

import ai.hhrdr.chainflow.engine.plugins.InscriptionHistoricalEventsHandler;
import org.camunda.bpm.engine.impl.history.event.HistoryEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.web3j.crypto.Credentials;
import org.web3j.protocol.Web3j;
import org.web3j.protocol.core.DefaultBlockParameterName;
import org.web3j.protocol.core.methods.request.Transaction;
import org.web3j.protocol.http.HttpService;
import org.web3j.tx.RawTransactionManager;
import org.web3j.tx.gas.DefaultGasProvider;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;


@Service
public class InscriptionDataService {

    private final Web3j web3j;
    private final Credentials credentials;

    //TODO: Set a realistic gas limit based on prior knowledge or dynamic calculations
    private final BigInteger gasLimit = BigInteger.valueOf(60000);
    private final Integer chainId;

    private static final Logger LOG = LoggerFactory.getLogger(InscriptionDataService.class);


    public InscriptionDataService(@Value("${inscription.privateKey}") String privateKey,
                                  @Value("${inscription.rpcUrl}") String rpcUrl,
                                  @Value("${inscription.chainId}") Integer chainId) {
        this.web3j = Web3j.build(new HttpService(rpcUrl));
        this.credentials = Credentials.create(privateKey);
        this.chainId = chainId;
    }

    public void sendInscriptionData(String jsonData) {
        try {

            String prefixedData = "data:application/json," + jsonData;
            String hexData = "0x" + bytesToHex(prefixedData.getBytes(StandardCharsets.UTF_8));
            sendRawTransaction(hexData);
        } catch (Exception e) {
            LOG.error("Error while sending inscription data: " + e.getMessage());
            e.printStackTrace();
        }
    }

    private void sendRawTransaction(String hexData) throws Exception {

        BigInteger gasPrice = web3j.ethGasPrice().send().getGasPrice();
        // Increase by 20% for higher priority transactions
        gasPrice = gasPrice.add(gasPrice.divide(BigInteger.valueOf(5)));

        RawTransactionManager transactionManager = new RawTransactionManager(web3j, credentials, chainId);

        // Send transaction to self address
        String transactionAddress = credentials.getAddress();
        transactionManager.sendTransaction(gasPrice, gasLimit, transactionAddress, hexData, BigInteger.ZERO);
    }

    private String bytesToHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }
}
