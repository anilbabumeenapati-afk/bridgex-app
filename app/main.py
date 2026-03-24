from fastapi import FastAPI

app = FastAPI()

try:
    from app.api.router import router
    app.include_router(router)
    print("✅ ROUTER LOADED")
except Exception as e:
    print("❌ IMPORT ERROR:", str(e))