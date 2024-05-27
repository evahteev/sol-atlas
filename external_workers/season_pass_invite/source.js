const {StandardMerkleTree} = await import('npm:@openzeppelin/merkle-tree');

async function getExistingAddresses() {
    // return [address1, address2, ...]
    const response = await Functions.makeHttpRequest(
        {
            url: secrets.URL,
            method: 'get',
            headers: {
                'Content-Type': 'application/json',
                'X-SYS-KEY': secrets.SYS_KEY
            }
        }
    )
    if (response.error) {
        console.error(response.message);
        throw Error("request existing wallets failed")
    }
    return response.data;
}

function generateMerkletree(walletAddresses) {
    const walletsSet = new Set(walletAddresses.map(x => (x.toLowerCase())))
    const walletArrayOfArray = [...walletsSet].map(x => ([x]))
    return StandardMerkleTree.of(walletArrayOfArray, ['address']);
}

const existingWallets = await getExistingAddresses();
const walletsToAdd = JSON.parse(args[0]); // list [address1, address2, ...]


const tree = generateMerkletree(existingWallets.concat(walletsToAdd))
return tree.tree[0];