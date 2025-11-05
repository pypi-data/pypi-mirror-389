"""
fubon_neo stub for CI/CD environments

This is a minimal stub implementation of the fubon_neo SDK
for use in CI/CD environments where the actual SDK cannot be installed
due to platform restrictions (Windows-only wheel).

This stub provides the necessary classes and methods signatures
to allow imports and basic testing without the actual SDK functionality.
"""

__version__ = "2.2.5.stub"


class SDK:
    """Stub SDK class for fubon_neo"""
    
    def __init__(self, *args, **kwargs):
        """Initialize SDK stub"""
        self.is_stub = True
        
    def login(self, *args, **kwargs):
        """Stub login method"""
        raise NotImplementedError("This is a stub - actual SDK not available")
        
    def logout(self, *args, **kwargs):
        """Stub logout method"""
        pass
        
    def init_realtime(self, *args, **kwargs):
        """Stub init_realtime method"""
        pass
        
    def place_order(self, *args, **kwargs):
        """Stub place_order method"""
        raise NotImplementedError("This is a stub - actual SDK not available")
        
    def update_order(self, *args, **kwargs):
        """Stub update_order method"""
        raise NotImplementedError("This is a stub - actual SDK not available")
        
    def cancel_order(self, *args, **kwargs):
        """Stub cancel_order method"""
        raise NotImplementedError("This is a stub - actual SDK not available")


class Order:
    """Stub Order class"""
    
    def __init__(self, *args, **kwargs):
        """Initialize Order stub"""
        pass


class Constant:
    """Stub Constant class with nested enums"""
    
    class Action:
        Buy = "Buy"
        Sell = "Sell"
        
    class MarketType:
        Common = "Common"
        Emerging = "Emerging"
        Odd = "Odd"
        
    class OrderType:
        Stock = "Stock"
        Futures = "Futures"
        Option = "Option"
        
    class PriceType:
        Limit = "Limit"
        Market = "Market"
        LimitUp = "LimitUp"
        LimitDown = "LimitDown"
        
    class TimeInForce:
        ROD = "ROD"
        IOC = "IOC"
        FOK = "FOK"
        
    class OrderStatus:
        Submitted = "Submitted"
        Failed = "Failed"
        Filled = "Filled"
        PartiallyFilled = "PartiallyFilled"
        Cancelled = "Cancelled"


# Additional stub classes as needed
class Quote:
    """Stub Quote class"""
    pass


class Trade:
    """Stub Trade class"""
    pass


class Snapshot:
    """Stub Snapshot class"""
    pass
