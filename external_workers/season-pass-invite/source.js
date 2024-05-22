// const {StandardMerkleTree} = await import('npm:@openzeppelin/merkle-tree');
import {StandardMerkleTree} from '@openzeppelin/merkle-tree';

function getExistingAddresses() {
    // return dict {tokenId: [address1, address2, ...]}
    return Functions.makeHttpRequest(
        {
            url: 'https://gurunetwork.ai/api/invited_wallets',
            method: 'get',
            headers: {
                'Content-Type': 'application/json',
                'X-SYS-KEY': secrets.SYS_KEY
            }
        }
    )
}


function generateMerkletree(tokenIdsToAddressesString) {
    const tokenIdsToAddressesDict = JSON.parse(tokenIdsToAddressesString);
    const tokenIdToAddress = []
    for (const tokenId in tokenIdsToAddressesDict) {
        for (const address of tokenIdsToAddressesDict[tokenId]) {
            tokenIdToAddress.push([tokenId, address]);
        }
    }
    console.log(tokenIdToAddress)
    return StandardMerkleTree.of(tokenIdToAddress, ['uint', 'address']);
}

const existingWallets = getExistingAddresses();

// const tree = generateMerkletree(`{
//     "1": ["0xAb8483F64d9C6d1EcF9b849Ae677dD3315835cb2", "0x4B20993Bc481177ec7E8f571ceCaE8A9e22C02db"],
//     "2": ["0x3da87b1c3743BD2dA60DF2ef1BC6F26Ef9Da6086"]
// }`);
const tree = generateMerkletree(existingWallets);

for (const [i, v] of tree.entries()) {
    if (v[1] === '0x3da87b1c3743BD2dA60DF2ef1BC6F26Ef9Da6086') {
        const proof = tree.getProof(i);
        console.log('Value:', v);
        console.log('Proof:', proof);
    }
}
