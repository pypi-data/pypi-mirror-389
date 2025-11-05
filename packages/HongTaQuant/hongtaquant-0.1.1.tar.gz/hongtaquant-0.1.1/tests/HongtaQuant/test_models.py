"""Test data models."""

import pytest
from datetime import datetime
from decimal import Decimal
from pydantic import ValidationError

from financial_sdk.models import StockData, Quote


def test_stock_data_creation() -> None:
    """测试创建股票数据模型."""
    data = StockData(
        symbol="000001.SZ",
        timestamp=datetime(2024, 1, 1, 9, 30),
        open=Decimal("10.50"),
        high=Decimal("11.00"),
        low=Decimal("10.20"),
        close=Decimal("10.80"),
        volume=1000000,
    )
    
    assert data.symbol == "000001.SZ"
    assert data.open == Decimal("10.50")
    assert data.volume == 1000000


def test_stock_data_validation() -> None:
    """测试股票数据验证."""
    with pytest.raises(ValidationError):
        StockData(symbol="000001.SZ")  # 缺少必需字段


def test_quote_creation() -> None:
    """测试创建行情模型."""
    quote = Quote(
        symbol="000001.SZ",
        timestamp=datetime(2024, 1, 1, 9, 30),
        bid_price=Decimal("10.50"),
        ask_price=Decimal("10.51"),
        last_price=Decimal("10.50"),
    )
    
    assert quote.symbol == "000001.SZ"
    assert quote.bid_price == Decimal("10.50")
