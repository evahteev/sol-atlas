const {StandardMerkleTree} = await import('npm:@openzeppelin/merkle-tree');
// import {StandardMerkleTree} from '@openzeppelin/merkle-tree';

function getExistingAddresses() {
    // return [address1, address2, ...]
    return Functions.makeHttpRequest(
        {
            url: 'https://flow.gurunetwork.ai/api/invited_wallets',
            method: 'get',
            headers: {
                'Content-Type': 'application/json',
                'X-SYS-KEY': secrets.SYS_KEY
            }
        }
    )
}


function generateMerkletree(walletAddresses) {
    let walletAddressesP = [];
    for (const address of walletAddresses) {
        walletAddressesP.push([address]);
    }
    return StandardMerkleTree.of(walletAddressesP, ['address']);
}

const existingWallets = getExistingAddresses();
const walletsToAdd = JSON.parse(args[0]); // list [address1, address2, ...]
// const existingWallets = ["0xab8483f64d9c6d1ecf9b849ae677dd3315835cb2", "0x4b20993bc481177ec7e8f571cecae8a9e22c02db"]
// const walletsToAdd = JSON.parse('["0x3da87b1c3743BD2dA60DF2ef1BC6F26Ef9Da6086"]');


const tree = generateMerkletree(existingWallets.concat(walletsToAdd))
console.log('Root:', tree.root.toString('hex'));

for (const [i, v] of tree.entries()) {
    if (v[0] === '0x3da87b1c3743BD2dA60DF2ef1BC6F26Ef9Da6086') {
        const proof = tree.getProof(i);
        console.log('Value:', v);
        console.log('Proof:', proof);
    }
}
