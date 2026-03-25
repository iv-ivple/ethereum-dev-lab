#!/usr/bin/env python3
"""
Database helper functions for common operations
"""

from models import DatabaseConnection, Wallet, Token, Transfer, Block
from sqlalchemy.exc import IntegrityError
from datetime import datetime

class BlockchainDB:
    def __init__(self, db_path='sqlite:///databases/blockchain.db'):
        self.db = DatabaseConnection(db_path)
        self.db.create_tables()
    
    # === WALLET OPERATIONS ===
    
    def add_wallet(self, address, label=None):
        """Add a wallet to track"""
        session = self.db.get_session()
        try:
            wallet = Wallet(address=address.lower(), label=label)
            session.add(wallet)
            session.commit()
            print(f"✅ Added wallet: {address}")
            return wallet
        except IntegrityError:
            session.rollback()
            print(f"⚠️  Wallet already exists: {address}")
            return session.query(Wallet).filter_by(address=address.lower()).first()
        finally:
            session.close()
    
    def get_wallet(self, address):
        """Get wallet by address"""
        session = self.db.get_session()
        wallet = session.query(Wallet).filter_by(address=address.lower()).first()
        session.close()
        return wallet
    
    def list_wallets(self):
        """List all tracked wallets"""
        session = self.db.get_session()
        wallets = session.query(Wallet).all()
        session.close()
        return wallets
    
    # === TOKEN OPERATIONS ===
    
    def add_token(self, address, symbol, name, decimals, total_supply=None):
        """Add or update token information"""
        session = self.db.get_session()
        try:
            token = session.query(Token).filter_by(address=address.lower()).first()
            
            if token:
                # Update existing token
                token.symbol = symbol
                token.name = name
                token.decimals = decimals
                token.total_supply = str(total_supply) if total_supply else None
                token.last_updated = datetime.utcnow()
                print(f"📝 Updated token: {symbol}")
            else:
                # Create new token
                token = Token(
                    address=address.lower(),
                    symbol=symbol,
                    name=name,
                    decimals=decimals,
                    total_supply=str(total_supply) if total_supply else None
                )
                session.add(token)
                print(f"✅ Added token: {symbol}")
            
            session.commit()
            return token
        except Exception as e:
            session.rollback()
            print(f"❌ Error adding token: {e}")
            return None
        finally:
            session.close()
    
    def get_token_by_address(self, address):
        """Get token by contract address"""
        session = self.db.get_session()
        token = session.query(Token).filter_by(address=address.lower()).first()
        session.close()
        return token
    
    def get_token_by_symbol(self, symbol):
        """Get token by symbol"""
        session = self.db.get_session()
        token = session.query(Token).filter_by(symbol=symbol.upper()).first()
        session.close()
        return token
    
    # === TRANSFER OPERATIONS ===
    
    def add_transfer(self, token_address, from_addr, to_addr, amount_raw, 
                     block_number, tx_hash, log_index, timestamp=None, gas_used=None):
        """Add a transfer event"""
        session = self.db.get_session()
        try:
            # Get token
            token = session.query(Token).filter_by(address=token_address.lower()).first()
            if not token:
                print(f"⚠️  Token not found: {token_address}")
                return None
            
            # Calculate decimal amount
            amount_decimal = int(amount_raw) / (10 ** token.decimals) if token.decimals else None
            
            # Create transfer
            transfer = Transfer(
                token_id=token.id,
                from_address=from_addr.lower(),
                to_address=to_addr.lower(),
                amount_raw=str(amount_raw),
                amount_decimal=str(amount_decimal),
                block_number=block_number,
                transaction_hash=tx_hash.lower(),
                log_index=log_index,
                timestamp=timestamp,
                gas_used=gas_used
            )
            
            session.add(transfer)
            session.commit()
            return transfer
            
        except IntegrityError:
            session.rollback()
            # Transfer already exists (duplicate)
            return None
        except Exception as e:
            session.rollback()
            print(f"❌ Error adding transfer: {e}")
            return None
        finally:
            session.close()
    
    def get_transfers_for_address(self, address, limit=100):
        """Get transfers involving an address"""
        session = self.db.get_session()
        address = address.lower()
        
        transfers = session.query(Transfer).filter(
            (Transfer.from_address == address) | (Transfer.to_address == address)
        ).order_by(Transfer.block_number.desc()).limit(limit).all()
        
        session.close()
        return transfers
    
    def get_transfers_for_token(self, token_address, limit=100):
        """Get recent transfers for a token"""
        session = self.db.get_session()
        
        token = session.query(Token).filter_by(address=token_address.lower()).first()
        if not token:
            session.close()
            return []
        
        transfers = session.query(Transfer).filter_by(
            token_id=token.id
        ).order_by(Transfer.block_number.desc()).limit(limit).all()
        
        session.close()
        return transfers
    
    # === STATISTICS ===
    
    def get_stats(self):
        """Get database statistics"""
        session = self.db.get_session()
        
        stats = {
            'wallets': session.query(Wallet).count(),
            'tokens': session.query(Token).count(),
            'transfers': session.query(Transfer).count(),
            'blocks': session.query(Block).count()
        }
        
        session.close()
        return stats

# Example usage
if __name__ == '__main__':
    db = BlockchainDB()
    
    # Add a wallet
    db.add_wallet('0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb', 'Uniswap Router')
    
    # Add a token (USDC)
    db.add_token(
        '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
        'USDC',
        'USD Coin',
        6,
        '1000000000000000'
    )
    
    # Get stats
    stats = db.get_stats()
    print(f"\n📊 Database Stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
