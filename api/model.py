from typing import Optional, List
from pydantic import BaseModel


class ExecuteRequest(BaseModel):
    account_name: str
    portfolio: str
    ticker: str
    open_close: str
    position: int
    price: float


class ExecuteResponse:
    pass
