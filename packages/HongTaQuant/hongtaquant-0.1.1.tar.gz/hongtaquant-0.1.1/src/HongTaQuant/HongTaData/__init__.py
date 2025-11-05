"""HongTaData模块"""

from HongTaQuant.HongTaData.config import Settings, settings
from HongTaQuant.HongTaData.http.client import HistoricalClient

__all__ = ["HistoricalClient", "Settings", "settings"]
