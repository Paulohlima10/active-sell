# webhook.py
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print(f"Dados recebidos: {data}")
    return {"message": "Dados recebidos com sucesso"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("simple_webhook:app", host="0.0.0.0", port=8000)