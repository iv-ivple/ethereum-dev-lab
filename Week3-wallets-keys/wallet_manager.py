#!/usr/bin/env python3
"""
Secure Wallet Manager - Week 3 Deliverable
A comprehensive tool demonstrating all Week 3 concepts with security best practices.
"""

from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
from mnemonic import Mnemonic
from dotenv import load_dotenv
import os
import json
import getpass

Account.enable_unaudited_hdwallet_features()
load_dotenv()

class WalletManager:
    def __init__(self):
        rpc_url = os.getenv('RPC_URL', 'https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY')
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.current_account = None
    
    def generate_new_wallet(self):
        """Generate a new random wallet."""
        account = Account.create()
        return {
            'address': account.address,
            'private_key': account.key.hex()
        }
    
    def generate_hd_wallet(self, num_accounts=1):
        """Generate HD wallet from new mnemonic."""
        mnemo = Mnemonic("english")
        mnemonic = mnemo.generate(strength=128)
        
        accounts = []
        for i in range(num_accounts):
            path = f"m/44'/60'/0'/0/{i}"
            account = Account.from_mnemonic(mnemonic, account_path=path)
            accounts.append({
                'index': i,
                'path': path,
                'address': account.address,
                'private_key': account.key.hex()
            })
        
        return {
            'mnemonic': mnemonic,
            'accounts': accounts
        }
    
    def import_from_private_key(self, private_key):
        """Import wallet from private key."""
        try:
            account = Account.from_key(private_key)
            return {
                'address': account.address,
                'private_key': account.key.hex()
            }
        except Exception as e:
            return None
    
    def import_from_mnemonic(self, mnemonic, index=0):
        """Import wallet from mnemonic phrase."""
        try:
            path = f"m/44'/60'/0'/0/{index}"
            account = Account.from_mnemonic(mnemonic, account_path=path)
            return {
                'address': account.address,
                'private_key': account.key.hex(),
                'path': path
            }
        except Exception as e:
            return None
    
    def sign_message(self, private_key, message):
        """Sign a message with private key."""
        account = Account.from_key(private_key)
        message_encoded = encode_defunct(text=message)
        signed_message = account.sign_message(message_encoded)
        
        return {
            'message': message,
            'signature': signed_message.signature.hex(),
            'signer': account.address
        }
    
    def verify_signature(self, message, signature):
        """Verify a signature and recover signer."""
        message_encoded = encode_defunct(text=message)
        recovered_address = Account.recover_message(message_encoded, signature=signature)
        return recovered_address
    
    def get_balance(self, address):
        """Get ETH balance for address."""
        if not self.w3.is_connected():
            return None
        balance_wei = self.w3.eth.get_balance(address)
        return self.w3.from_wei(balance_wei, 'ether')
    
    def get_nonce(self, address):
        """Get transaction nonce for address."""
        if not self.w3.is_connected():
            return None
        return self.w3.eth.get_transaction_count(address)

def print_menu():
    print("\n" + "=" * 70)
    print("SECURE WALLET MANAGER - Week 3 Deliverable")
    print("=" * 70)
    print("\n📋 Main Menu:")
    print("  1. Generate new random wallet")
    print("  2. Generate HD wallet (with mnemonic)")
    print("  3. Import wallet from private key")
    print("  4. Import wallet from mnemonic")
    print("  5. Sign message")
    print("  6. Verify signature")
    print("  7. Check wallet balance")
    print("  8. Get nonce (transaction count)")
    print("  9. Exit")
    print("\n⚠️  Security Reminder: Never share private keys or mnemonics!")
    print("=" * 70)

def main():
    manager = WalletManager()
    
    while True:
        print_menu()
        choice = input("\nSelect option (1-9): ").strip()
        
        if choice == '1':
            print("\n🔐 Generating new random wallet...")
            wallet = manager.generate_new_wallet()
            print(f"\n✅ Wallet Generated!")
            print(f"   Address:     {wallet['address']}")
            print(f"   Private Key: {wallet['private_key']}")
            print("\n⚠️  Save these securely! They won't be shown again.")
        
        elif choice == '2':
            num = input("\nHow many accounts to derive? (default 3): ").strip()
            num_accounts = int(num) if num else 3
            
            print(f"\n🌱 Generating HD wallet with {num_accounts} accounts...")
            hd_wallet = manager.generate_hd_wallet(num_accounts)
            
            print(f"\n✅ HD Wallet Generated!")
            print(f"\n🔑 Mnemonic (BACKUP THIS!):")
            print(f"   {hd_wallet['mnemonic']}")
            print(f"\n📊 Derived Accounts:")
            
            for acc in hd_wallet['accounts']:
                print(f"\n   Account {acc['index']}:")
                print(f"     Path:    {acc['path']}")
                print(f"     Address: {acc['address']}")
                print(f"     PrivKey: {acc['private_key']}")
        
        elif choice == '3':
            print("\n⚠️  Import wallet from private key")
            private_key = getpass.getpass("   Enter private key (input hidden): ").strip()
            
            if not private_key.startswith('0x'):
                private_key = '0x' + private_key
            
            wallet = manager.import_from_private_key(private_key)
            
            if wallet:
                print(f"\n✅ Wallet Imported!")
                print(f"   Address: {wallet['address']}")
            else:
                print("\n❌ Invalid private key!")
        
        elif choice == '4':
            print("\n⚠️  Import wallet from mnemonic")
            mnemonic = getpass.getpass("   Enter mnemonic phrase (input hidden): ").strip()
            index = input("   Account index (default 0): ").strip()
            index = int(index) if index else 0
            
            wallet = manager.import_from_mnemonic(mnemonic, index)
            
            if wallet:
                print(f"\n✅ Wallet Imported!")
                print(f"   Path:    {wallet['path']}")
                print(f"   Address: {wallet['address']}")
            else:
                print("\n❌ Invalid mnemonic phrase!")
        
        elif choice == '5':
            print("\n✍️  Sign a message")
            private_key = getpass.getpass("   Enter private key (input hidden): ").strip()
            
            if not private_key.startswith('0x'):
                private_key = '0x' + private_key
            
            message = input("   Enter message to sign: ").strip()
            
            try:
                result = manager.sign_message(private_key, message)
                print(f"\n✅ Message Signed!")
                print(f"   Message:   {result['message']}")
                print(f"   Signer:    {result['signer']}")
                print(f"   Signature: {result['signature']}")
            except Exception as e:
                print(f"\n❌ Error: {e}")
        
        elif choice == '6':
            print("\n🔍 Verify signature")
            message = input("   Enter original message: ").strip()
            signature = input("   Enter signature: ").strip()
            
            try:
                signer = manager.verify_signature(message, signature)
                print(f"\n✅ Signature Valid!")
                print(f"   Recovered signer: {signer}")
            except Exception as e:
                print(f"\n❌ Invalid signature: {e}")
        
        elif choice == '7':
            print("\n💰 Check wallet balance")
            address = input("   Enter address: ").strip()
            
            if not manager.w3.is_connected():
                print("\n❌ Not connected to Ethereum network")
                print("   Check your INFURA_URL in .env file")
            else:
                balance = manager.get_balance(address)
                if balance is not None:
                    print(f"\n✅ Balance: {balance} ETH")
                else:
                    print("\n❌ Could not fetch balance")
        
        elif choice == '8':
            print("\n🔢 Get transaction nonce")
            address = input("   Enter address: ").strip()
            
            if not manager.w3.is_connected():
                print("\n❌ Not connected to Ethereum network")
                print("   Check your INFURA_URL in .env file")
            else:
                nonce = manager.get_nonce(address)
                if nonce is not None:
                    print(f"\n✅ Nonce (transaction count): {nonce}")
                    print(f"   Next transaction from this address should use nonce: {nonce}")
                else:
                    print("\n❌ Could not fetch nonce")
        
        elif choice == '9':
            print("\n👋 Exiting Wallet Manager...")
            print("   Stay safe! Never share your private keys.\n")
            break
        
        else:
            print("\n❌ Invalid option. Please select 1-9.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("INITIALIZING SECURE WALLET MANAGER")
    print("=" * 70)
    print("\n⚠️  SECURITY WARNINGS:")
    print("  • This tool is for EDUCATIONAL purposes only")
    print("  • NEVER use these wallets with real funds")
    print("  • NEVER commit private keys or mnemonics to git")
    print("  • Use testnets only (Goerli, Sepolia)")
    print("  • Private key input is hidden for security")
    print("=" * 70)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Exiting safely...")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
