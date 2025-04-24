package ai.hhrdr.chainflow.engine.delegate;

import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.JavaDelegate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import org.web3j.protocol.Web3j;
import org.web3j.protocol.http.HttpService;
import org.web3j.protocol.core.DefaultBlockParameterName;
import org.web3j.utils.Convert;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.RoundingMode;
import java.util.logging.Logger;

@Component("evmCheckBalanceDelegate")
public class EvmCheckBalanceDelegate implements JavaDelegate {

    private static final Logger LOGGER = Logger.getLogger(EvmCheckBalanceDelegate.class.getName());

    @Value("${inscription.rpcUrl}")
    private String rpcUrl;

    @Override
    public void execute(DelegateExecution execution) throws Exception {
        LOGGER.info("Starting EvmCheckBalanceDelegate...");

        // 1) Retrieve variables from BPMN execution
        String walletAddress = (String) execution.getVariable("wallet_address");

        // Handle both Number and String types for chain_id
        Object chainIdObj = execution.getVariable("chain_id");
        Long chainId;
        if (chainIdObj instanceof Number) {
            chainId = ((Number) chainIdObj).longValue();
        } else if (chainIdObj instanceof String) {
            chainId = Long.parseLong((String) chainIdObj);
        } else {
            throw new IllegalArgumentException("chain_id variable is neither Number nor String");
        }

        // Use wallet_address_internal in case chain_id equals 261
        if (chainId == 261) {
            String walletAddressInternal = (String) execution.getVariable("wallet_address_internal");
            if (walletAddressInternal != null && !walletAddressInternal.isEmpty()) {
                walletAddress = walletAddressInternal;
            }
        }

        LOGGER.info("Checking balance for address: " + walletAddress + " on chain_id: " + chainId);

        // 2) Connect to the EVM-compatible RPC node
        Web3j web3j = Web3j.build(new HttpService(rpcUrl));
        LOGGER.info("Connected to EVM node via: " + rpcUrl);

        // 3) Fetch the wallet balance in Wei
        BigInteger weiBalance = web3j
                .ethGetBalance(walletAddress, DefaultBlockParameterName.LATEST)
                .send()
                .getBalance();
        LOGGER.info("Wei balance from chain: " + weiBalance);

        // 4) Convert from Wei to Ether (18 decimals)
        BigDecimal balanceInEther = Convert.fromWei(new BigDecimal(weiBalance), Convert.Unit.ETHER);
        LOGGER.info("Balance in 18-decimal format: " + balanceInEther);

        // 5) Round the wallet balance to 2 decimal places
        BigDecimal walletBalanceRounded = balanceInEther.setScale(2, RoundingMode.HALF_UP);
        execution.setVariable("wallet_balance", walletBalanceRounded.toPlainString());
        execution.setVariable("checked_chain_id", chainId);

        // 6) Retrieve the required balance from process variables
        BigDecimal threshold = new BigDecimal(execution.getVariable("required_balance").toString());
        LOGGER.info("Using threshold (required_balance): " + threshold);

        // 7) Check if the balance is below the required threshold
        if (walletBalanceRounded.compareTo(threshold) < 0) {
            // insufficient_balance = true
            execution.setVariable("insufficient_balance", true);

            // Calculate sponsored_amount = threshold - user_balance
            BigDecimal sponsoredAmount = threshold.subtract(walletBalanceRounded);

            // Round UP to the next integer
            BigInteger ceilInt = sponsoredAmount
                    .setScale(0, RoundingMode.UP)
                    .toBigIntegerExact();

            // Store as string in Camunda variable
            execution.setVariable("sponsored_amount", ceilInt.toString());
            LOGGER.info("Balance is below threshold; sponsored_amount set to: " + ceilInt);
        } else {
            // If balance >= threshold
            execution.setVariable("insufficient_balance", false);
            execution.setVariable("sponsored_amount", "0");
            LOGGER.info("Balance meets or exceeds threshold; no sponsorship required.");
        }

        LOGGER.info("EvmCheckBalanceDelegate completed successfully. " +
                "Set 'wallet_balance', 'insufficient_balance', and 'sponsored_amount' in process variables.");
    }
}
