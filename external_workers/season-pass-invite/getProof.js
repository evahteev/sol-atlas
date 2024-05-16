import keccak256 from 'keccak256'
import {MerkleTree} from 'merkletreejs'

const getHexProof = (claimingAddress, tree) => {
    let hexProof = tree.getHexProof(keccak256(claimingAddress))

    if (!hexProof.length) {
        hexProof = ['0x']
    }

    return hexProof
}

function generateMerkletree(addresses) {
    const set = Array.from(new Set(addresses));
    const leafNodes = set.map((address) => keccak256(address));
    console.log(leafNodes);
    return new MerkleTree(leafNodes, keccak256, {sortPairs: true});
}

const existingAddresses = ["0xAb8483F64d9C6d1EcF9b849Ae677dD3315835cb2", "0x4B20993Bc481177ec7E8f571ceCaE8A9e22C02db"];


const addressToAdd = "0x3da87b1c3743BD2dA60DF2ef1BC6F26Ef9Da6086";

let tree = generateMerkletree(existingAddresses.concat(addressToAdd));
console.log(tree.getRoot().toString('hex'));
console.log(getHexProof("0x3da87b1c3743BD2dA60DF2ef1BC6F26Ef9Da6086", tree));