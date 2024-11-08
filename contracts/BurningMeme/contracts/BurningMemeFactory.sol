// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./BurningMemeBet.sol";
import "@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";


contract BurningMemeFactory is Initializable, OwnableUpgradeable, UUPSUpgradeable {

    address public WGURU;
    address[] public deployedBurningMemes;

    event BurningMemeCreated(address indexed newBurningMeme);

    constructor() {
        _disableInitializers();
    }

    function initialize(address initialOwner, address wguru) initializer public {
        __Ownable_init(initialOwner);
        __UUPSUpgradeable_init();
        WGURU = wguru;
    }

    function _authorizeUpgrade(address newImplementation)
        internal
        onlyOwner
        override
    {}
    
    function createBurningMeme(
        address initialOwner,
        string memory name,
        string memory symbol,
        string memory art_id,
        uint256 bettingTTL,
        uint256 allocation
    ) external returns (address) {
        IBurningMemeBet newBurningMeme = new BurningMemeBet(
            WGURU,
            initialOwner,
            name,
            symbol,
            bettingTTL,
            allocation,
            art_id
        );
        deployedBurningMemes.push(address(newBurningMeme));
        emit BurningMemeCreated(address(newBurningMeme));
        return address(newBurningMeme);
    }

    function getDeployedBurningMemes() public view returns (address[] memory) {
        return deployedBurningMemes;
    }

    function getDeployedTokensCount() public view returns (uint256) {
        return deployedBurningMemes.length;
    }

}