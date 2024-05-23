const {StandardMerkleTree} = await import('npm:@openzeppelin/merkle-tree');
// import {StandardMerkleTree} from '@openzeppelin/merkle-tree';

async function getExistingAddresses() {
    // return [address1, address2, ...]
    const response = await Functions.makeHttpRequest(
        {
            url: 'https://flow.gurunetwork.ai/api/invited_wallets',
            method: 'get',
            headers: {
                'Content-Type': 'application/json',
                'X-SYS-KEY': secrets.SYS_KEY
            }
        }
    )
    if (response.error) {
        console.error(response.error);
        throw Error("request existing wallets failed")
    }
    return response.data;
}


function generateMerkletree(walletAddresses) {
    let walletAddressesP = [];
    for (const address of walletAddresses) {
        walletAddressesP.push([address]);
    }
    return StandardMerkleTree.of(walletAddressesP, ['address']);
}

const existingWallets = await getExistingAddresses();
const walletsToAdd = JSON.parse(args[0]); // list [address1, address2, ...]


const tree = generateMerkletree(existingWallets.concat(walletsToAdd))
return tree.tree[0];