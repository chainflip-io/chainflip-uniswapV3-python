from .Shared import *
import secrets

# This module is created to mimick blockchain accounts and their balances. For simplification purposess will only
# support the tokens that are initialized in the constructor function. Transfering or receiving other tokens will
# fail (token not in balances dict).

# A random hex address will be assigned to every account when created. This is done to mimic the blockchain address
# and to not store the addressess as just pointers to the account instance. Otherwise issues arise when using
# the account reference values or when we make copies of the Pool in testing.
class Account:
    def __init__(self, name, tokens, balances):
        checkInputTypes(string=(name, *tokens), uint256=(*balances,))
        assert len(tokens) == len(balances)
        # Check uniquness of tokens list
        assert len(set(tokens)) == len(tokens)

        self.name = name

        self.address = secrets.token_hex(40)

        self.tokens = tokens
        self.balances = {}

        # Assign initial balances
        for i in range(len(tokens)):
            self.balances[tokens[i]] = balances[i]

    def updateBalance(self, token, amount):
        checkInputTypes(string=(token), int256=(amount))
        self.balances[token] += amount

        # Check potential overflow/underflow that would happen in solidity
        checkUInt256(self.balances[token])


# The ledger class is used to keep track of all accounts and their balances and to process the transfer of tokens
# between them.
class Ledger:
    def __init__(self, initialAccounts):
        self.accounts = dict()
        for accountParams in initialAccounts:
            self.createAccount(accountParams[0], accountParams[1], accountParams[2])

    def createAccount(self, name, tokens, balances):
        checkInputTypes(string=(name, *tokens), uint256=(balances))
        account = Account(name, tokens, balances)
        assert not self.accounts.__contains__(account.address)
        self.accounts[account.address] = account

    # Add transfer and receive tokens functions.
    def transferToken(self, sender, recipient, token, amount):
        checkInputTypes(account=(recipient), string=(token), uint256=(amount))
        # Get the references to the Account recipient and sender
        if type(recipient) == str:
            recipient = self.getAccountWithAddress(recipient)
        if type(sender) == str:
            sender = self.getAccountWithAddress(sender)

        balanceSenderBefore = sender.balances[token]
        balanceReceiverBefore = recipient.balances[token]

        assert sender.balances[token] >= amount, "Insufficient balance"

        sender.updateBalance(token, -amount)

        self.receiveToken(recipient, token, amount)

        # Transfer health check
        assert sender.balances[token] == balanceSenderBefore - amount
        assert recipient.balances[token] == balanceReceiverBefore + amount

    def receiveToken(self, recipient, token, amount):
        if type(recipient) == str:
            recipient = self.getAccountWithAddress(recipient)

        checkInputTypes(string=(token), uint256=(amount))
        recipient.updateBalance(token, amount)

    def getAccountWithAddress(self, address):
        return self.accounts[address]

    def balanceOf(self, address, token):
        checkInputTypes(string=(address, token))
        return self.accounts[address].balances[token]

    # Force the balance of an account to ease the testing
    def setBalance(self, address, token, amount):
        checkInputTypes(string=(address, token), uint256=amount)
        self.accounts[address].balances[token] = amount
