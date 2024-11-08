// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;

import { IBurningMemeBet } from "./IBurningMemeBet.sol";
import { Ownable } from "@openzeppelin/contracts/access/Ownable.sol";
import { ERC20 } from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import { ERC20Pausable } from "@openzeppelin/contracts/token/ERC20/extensions/ERC20Pausable.sol";


// todo add fees to guru 2% of total supply.
// deploy on other chains common erc20 with fee.
//
//this contract only for guru network
contract BurningMemeBet is ERC20, ERC20Pausable, IBurningMemeBet, Ownable {
    mapping(address account => uint256) private _burnBalances;
    mapping(address account => uint256) private _mintBalances;
    address[] private _minters;
    address[] private _burners;
    uint256 private _burnTotalSupply = 0;
    uint256 private _mintTotalSupply = 0;
    uint256 private _allocation;
    string private ART_ID;
    address public memeOwner;
    address public factory;
    address public WGURU;

    bool private _isWinnersDefined = false;
    uint256 private immutable BETTING_END_TIMESTAMP;

    constructor(
        address wguru,
        address initialOwner,
        string memory _name,
        string memory _symbol,
        uint256 _trading_ttl,
        uint256 __allocation,
        string memory _art_id
    )
        ERC20(_name, _symbol)
        Ownable(tx.origin)
    {
        WGURU = wguru;
        factory = msg.sender;
        BETTING_END_TIMESTAMP = block.timestamp + _trading_ttl;
        _allocation = __allocation;
        ART_ID = _art_id;
        memeOwner = initialOwner;
        pause();
    }

    modifier onlyOwnerOrFactory() {
        if (msg.sender != owner() && msg.sender != factory) revert("Not allowed");
        _;
    }
    
    function allocation() public view returns (uint256) {
        return _allocation;
    }

    function mint(uint256 amount_) external payable override {
        require(block.timestamp < BETTING_END_TIMESTAMP, "Betting is closed");
        uint256 proceeds = voteCost(amount_);
        address sender = msg.sender;

        if (msg.value < proceeds) {
            revert InsufficientValue(proceeds, msg.value);
        }

        _mintVote(sender, amount_);

        if (msg.value > proceeds) {
            (bool sent,) = sender.call{value: msg.value - proceeds}("");
            if (!sent) {
                revert EtherTransferFailed(sender, msg.value - proceeds);
            }
        }
        emit Mint(sender, proceeds, amount_);
        emit Swap(sender, proceeds, 0, 0, amount_, sender);
    }

    function _mintVote(address account, uint256 amount_) private {
        if (_mintBalances[account] == 0) {
            _minters.push(account);
        }
        _mintBalances[account] += amount_;
        _mintTotalSupply += amount_;
        emit Transfer(address(0), account, amount_);
    }

    function burn(uint256 amount_) external payable {
        require(block.timestamp < BETTING_END_TIMESTAMP, "Betting is closed");
        uint256 proceeds = voteCost(amount_);
        address sender = msg.sender;

        if (msg.value < proceeds) {
            revert InsufficientValue(proceeds, msg.value);
        }

        _burnVote(sender, amount_);

        if (msg.value > proceeds) {
            (bool sent,) = sender.call{value: msg.value - proceeds}("");
            if (!sent) {
                revert EtherTransferFailed(sender, msg.value - proceeds);
            }
        }
        emit Burn(sender, proceeds, amount_, sender);
        emit Swap(sender, proceeds, 0, 0, amount_, sender);
    }

    function _burnVote(address account, uint256 amount) private {
        if (_burnBalances[account] == 0) {
            _burners.push(account);
        }
        _burnBalances[account] += amount;
        _burnTotalSupply += amount;
        emit Transfer(address(0), account, amount);
    }

    function voteCost(uint256 amount_) public view override returns (uint256) {
        // The sum of the prices of all the tokens already minted
        uint256 sumBeforeVote = _sumOfPriceToNTokens(totalSupply());
        // The sum of the prices of all the tokens after burning amount_
        uint256 sumAfterVote = _sumOfPriceToNTokens(totalSupply() + amount_);

        return sumAfterVote - sumBeforeVote;
    }

   // The following function is override required by Solidity.
    function _update(address from, address to, uint256 value)
        internal
        override(ERC20, ERC20Pausable)
    {
        super._update(from, to, value);
    }

    function pause() public onlyOwnerOrFactory {
        _pause();
    }

    function unpause() public onlyOwnerOrFactory {
        _unpause();
    }

    function totalSupply() public view override  returns (uint256) {
        return _burnTotalSupply + _mintTotalSupply;
    }

    function getBettingEndTimestamp() public view returns (uint256) {
        return BETTING_END_TIMESTAMP;
    }

    function defineWinners() public onlyOwner {
        require(block.timestamp > BETTING_END_TIMESTAMP, "Betting still in progress");
        require(!_isWinnersDefined, "Winners have been already defined");
        if (mintTotalSupply() > burnTotalSupply()) {
            _mintTotalSupply = mintTotalSupply() + burnTotalSupply();
            _burnTotalSupply = 0;
            for (uint i=0; i< _burners.length; i++) {
                _burnBalances[_burners[i]] = 0;
            }
            delete _burners;
        }
        else {
            _burnTotalSupply = mintTotalSupply() + burnTotalSupply();
            _mintTotalSupply = 0;
            for (uint i=0; i< _minters.length; i++) {
                 _mintBalances[_minters[i]] = 0;
            }
            delete _minters;
        }
        _isWinnersDefined = true;
        unpause();
    }

    function burnBalanceOf(address account) public view returns (uint256) {
        return _burnBalances[account];
    }

    function burnTotalSupply() public view returns (uint256) {
        return _burnTotalSupply;
    }

    function mintTotalSupply() public view returns (uint256) {
        return _mintTotalSupply;
    }

    function mintBalanceOf(address account) public view returns (uint256) {
        return _mintBalances[account];
    }


    function decimals() public pure override returns (uint8) {
        return 0;
    }

    // The price of *all* tokens from number 1 to n.
    function _sumOfPriceToNTokens(uint256 n_) internal pure returns (uint256) {
        return n_ * (n_ + 1) * (2 * n_ + 1) / 6;
    }

    function withdraw() public onlyOwner {
        uint256 amount = address(this).balance;
        (bool sent,) = msg.sender.call{value: amount}("");
        if (!sent) {
            revert EtherTransferFailed(msg.sender, amount);
        }
    }

    // uniswap v2 pool behavior

    function token0() public view returns (address) {
        return WGURU;
    }

    function token1() public view returns (address) {
        return address(this);
    }

    function getReserves() public view returns (uint256, uint256) {
        return (address(this).balance, totalSupply());
    }
}
