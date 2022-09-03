import uvicorn
from fastapi import FastAPI, Request
from fastapi import HTTPException, Header
from starlette.responses import JSONResponse

from api.exchange.upbit_exchange import Upbit
from api.exchange.binance_future_excahnge import Binance
from api.model import ExecuteRequest, ExecuteResponse


app = FastAPI(openapi_url=None, redoc_url=None)


@app.get("/")
def root():
    return "OK"


@app.post("/execute", response_model=ExecuteRequest)
def execute_order(data: ExecuteRequest, response_model=ExecuteResponse):
    try:
        upbit = Upbit(account_name=data.account_name)
        binance = Binance(account_name=data.account_name)


    except Exception as e:
        return JSONResponse(status_code=500, content=dict(msg=str(e)))




if __name__ == '__main__':
    # uvicorn main:app --reload --host 0.0.0.0 --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8002)
