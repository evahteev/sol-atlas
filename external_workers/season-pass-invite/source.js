const {MerkleTree} = await import('npm:merkletreejs');
const {keccakFromHexString, keccak256} = await import('https://deno.land/x/npm_ethereumjs_util@0.0.3/mod.ts');


function getExistingAddresses() {
    const existingAddresses = Functions.HTTPGet("https://clfunctions.s3.eu-north-1.amazonaws.com/offchain-secrets.json")
}

function generateMerkletree(addresses) {
    const set = Array.from(new Set(addresses));
    const leafNodes = set.map((address) => keccakFromHexString(address));
    return new MerkleTree(leafNodes, keccak256, {sortPairs: true});
}

const tree = generateMerkletree(existingAddresses.concat(args))
return tree.getRoot();
