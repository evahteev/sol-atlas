import {Client, logger} from "camunda-external-task-client-js";

import fs from "fs";
import {
    decodeResult,
    FulfillmentCode,
    ResponseListener,
    ReturnType,
    SecretsManager,
    simulateScript,
    SubscriptionManager,
} from "@chainlink/functions-toolkit";
import ethers from "ethers";

import functionsConsumerAbi from "./functionsClientAbi.mjs";
import 'dotenv/config';


const consumerAddress = process.env.CONSUMER_ADDRESS;
const subscriptionId = process.env.SUBSCRIPTION_ID;

const engineConfig = {
    baseUrl: process.env.ENGINE_URL,
    use: logger,
    workerId: "update_merkle_tree",
    maxTasks: 1,
    lockDuration: 5000000,
    retries: 0,
    autoPoll: true,
};
const client = new Client(engineConfig);


const makeRequest = async (task, taskService) => {
    const routerAddress = process.env.ROUTER_ADDRESS;
    const linkTokenAddress = process.env.LINK_TOKEN_ADDRESS;
    const donId = process.env.DON_ID;
    const explorerUrl = process.env.EXPLORER_URL;
    const availableInvites = task.variables.get("available_invites")
    const inviterWallet = task.variables.get("wallet_address")
    const slotID = 0;
    const privateKey = process.env.PRIVATE_KEY; // fetch PRIVATE_KEY
    const rpcUrl = process.env.RPC_URL;
    const gatewayUrls = process.env.GATEWAY_URLS.split(",")

    let walletsToInvite = []

    for (let i = 1; i <= availableInvites; i++) {
        const wallet = task.variables.get(`wallet_${i}`)
        if (wallet && wallet !== inviterWallet) {
            walletsToInvite.push(wallet)
        }
    }

    // Initialize functions settings
    const source = fs.readFileSync("source.js").toString();

    let args = [JSON.stringify(walletsToInvite)];
    const secrets = {SYS_KEY: process.env.SYS_KEY}; // Only used for simulation in this example
    const gasLimit = 300000;

    // Initialize ethers signer and provider to interact with the contracts onchain
    if (!privateKey)
        throw new Error(
            "private key not provided - check your environment variables"
        );


    if (!rpcUrl)
        throw new Error(`rpcUrl not provided  - check your environment variables`);

    const provider = new ethers.providers.JsonRpcProvider(rpcUrl);

    const wallet = new ethers.Wallet(privateKey);
    const signer = wallet.connect(provider); // create ethers signer for signing transactions

    ///////// START SIMULATION ////////////

    console.log("Start simulation...");

    const response = await simulateScript({
        source: source,
        args: args,
        bytesArgs: [], // bytesArgs - arguments can be encoded off-chain to bytes.
        secrets: secrets,
    });

    console.log("Simulation result", response);
    const errorString = response.errorString;
    if (errorString) {
        console.log(`❌ Error during simulation: `, errorString);
        throw new Error(`Error during simulation: ${errorString}`);
    } else {
        const returnType = ReturnType.uint256;
        const responseBytesHexstring = response.responseBytesHexstring;
        if (ethers.utils.arrayify(responseBytesHexstring).length > 0) {
            const decodedResponse = decodeResult(
                response.responseBytesHexstring,
                returnType
            );
            console.log(`✅ Decoded response to ${returnType}: `, decodedResponse);
        }
    }
    //////// ESTIMATE REQUEST COSTS ////////
    console.log("\nEstimate request costs...");
    // Initialize and return SubscriptionManager
    const subscriptionManager = new SubscriptionManager({
        signer: signer,
        linkTokenAddress: linkTokenAddress,
        functionsRouterAddress: routerAddress,
    });
    await subscriptionManager.initialize();

    // estimate costs in Juels

    const gasPriceWei = await signer.getGasPrice(); // get gasPrice in wei

    const estimatedCostInJuels =
        await subscriptionManager.estimateFunctionsRequestCost({
            donId: donId, // ID of the DON to which the Functions request will be sent
            subscriptionId: subscriptionId, // Subscription ID
            callbackGasLimit: gasLimit, // Total gas used by the consumer contract's callback
            gasPriceWei: BigInt(gasPriceWei), // Gas price in gWei
        });

    console.log(
        `Fulfillment cost estimated to ${ethers.utils.formatEther(
            estimatedCostInJuels
        )} LINK`
    );

    //////// MAKE REQUEST ////////

    console.log("\nMake request...");

    // Initialize SecretsManager instance
    const secretsManager = new SecretsManager({
        signer: signer,
        functionsRouterAddress: routerAddress,
        donId: donId,
    });
    await secretsManager.initialize();

    // Encrypt secrets Urls

    console.log(`\nEncrypt the URLs..`);
    const encryptedSecrets = await secretsManager.encryptSecrets(secrets);

    // Upload secrets
    const uploadResult = await secretsManager.uploadEncryptedSecretsToDON({
        encryptedSecretsHexstring: encryptedSecrets.encryptedSecrets,
        gatewayUrls: gatewayUrls,
        slotId: slotID,
        minutesUntilExpiration: 10,
    });

    if (!uploadResult.success)
        throw new Error(`Encrypted secrets not uploaded to ${gatewayUrls}`);

    console.log(
        `\n✅ Secrets uploaded properly to gateways ${gatewayUrls}! Gateways response: `,
        uploadResult
    );

    const donHostedSecretsVersion = parseInt(uploadResult.version); // fetch the reference of the encrypted secrets

    const functionsConsumer = new ethers.Contract(
        consumerAddress,
        functionsConsumerAbi,
        signer
    );

    // Actual transaction call
    const transaction = await functionsConsumer.sendRequest(
        source, // source
        "0x", // Encrypted Urls where the DON can fetch the encrypted secrets
        slotID, // don hosted secrets - slot ID
        donHostedSecretsVersion, // don hosted secrets - version
        args,
        [], // bytesArgs - arguments can be encoded off-chain to bytes.
        subscriptionId,
        gasLimit,
        ethers.utils.formatBytes32String(donId) // jobId is bytes32 representation of donId
    );

    // Log transaction details
    console.log(
        `\n✅ Functions request sent! Transaction hash ${transaction.hash}. Waiting for a response...`
    );

    console.log(
        `See your request in the explorer ${explorerUrl}/tx/${transaction.hash}`
    );
    return transaction.hash;

};

async function waitForResponse(tx_hash) {
    const rpcUrl = process.env.RPC_URL;
    const provider = new ethers.providers.JsonRpcProvider(rpcUrl);
    const routerAddress = process.env.ROUTER_ADDRESS;
    const responseListener = new ResponseListener({
        provider: provider,
        functionsRouterAddress: routerAddress,
    }); // Instantiate a ResponseListener object to wait for fulfillment.
    const response = await new Promise((resolve, reject) => {
        responseListener
            .listenForResponseFromTransaction(tx_hash)
            .then((response) => {
                resolve(response); // Resolves once the request has been fulfilled.
            })
            .catch((error) => {
                reject(error); // Indicate that an error occurred while waiting for fulfillment.
            });
    });

    const fulfillmentCode = response.fulfillmentCode;

    if (fulfillmentCode === FulfillmentCode.FULFILLED) {
        console.log(
            `\n✅ Request ${
                response.requestId
            } successfully fulfilled. Cost is ${ethers.utils.formatEther(
                response.totalCostInJuels
            )} LINK.Complete reponse: `,
            response
        );
    } else if (fulfillmentCode === FulfillmentCode.USER_CALLBACK_ERROR) {
        console.log(
            `\n⚠️ Request ${
                response.requestId
            } fulfilled. However, the consumer contract callback failed. Cost is ${ethers.utils.formatEther(
                response.totalCostInJuels
            )} LINK.Complete reponse: `,
            response
        );
        throw new Error(`Request fulfilled. However, the consumer contract callback failed.`);
    } else {
        console.log(
            `\n❌ Request ${
                response.requestId
            } not fulfilled. Code: ${fulfillmentCode}. Cost is ${ethers.utils.formatEther(
                response.totalCostInJuels
            )} LINK.Complete reponse: `,
            response
        );
        throw new Error(`Request not fulfilled. Code: ${fulfillmentCode}`);
    }
    const errorString = response.errorString;
    if (errorString) {
        console.log(`\n❌ Error during the execution: `, errorString);
        throw new Error(`Error during the execution: ${errorString}`);
    } else {
        const responseBytesHexstring = response.responseBytesHexstring;
        if (ethers.utils.arrayify(responseBytesHexstring).length > 0) {
            const decodedResponse = decodeResult(
                response.responseBytesHexstring,
                ReturnType.uint256
            );
            console.log(
                `\n✅ Decoded response to ${ReturnType.uint256}: `,
                decodedResponse
            );
        }
    }
}

async function handleTask({task, taskService}) {
    try {
        const tx_hash = await makeRequest(task, taskService);
        await waitForResponse(tx_hash);
        return await taskService.complete(task);
    } catch (error) {
        console.log("Error processing task", error);
        logger.error(error);
        return await taskService.handleBpmnError(task, "CHAINLINK_CCIP_ERROR", error.message);
    }
}


client.subscribe(
    "updateMerkleTree",
    handleTask
);
