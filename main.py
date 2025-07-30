from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from service.app.api.auth_routes import router as auth_router
from service.app.api.general_routes import router as general_router
from service.app.api.langchain_routes import router as langchain_router

load_dotenv()

app = FastAPI(title='モテメッセ API', version='0.1.0')

# CORS設定
origins = [
    'http://localhost:3000',
    'http://localhost:3001',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:3001',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# ルーターを追加
app.include_router(auth_router)
app.include_router(general_router)
app.include_router(langchain_router)

@app.get('/')
def read_root():
    return {'message': 'Welcome to モテメッセ API'}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)