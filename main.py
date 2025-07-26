from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

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

@app.get('/')
def read_root():
    return {'message': 'Welcome to モテメッセ API'}

@app.get('/health')
def health_check():
    return {'status': 'healthy', 'service': 'モテメッセ API'}

@app.get('/api/hello')
def hello_world():
    return {'message': 'Hello World from モテメッセ API'}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)