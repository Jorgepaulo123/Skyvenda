from sqlalchemy.orm import Session
from database import SessionLocal, engine
from typing import List, Dict
from fastapi.staticfiles import StaticFiles
import os
from models import Base
from fastapi import FastAPI, Request

from fastapi.responses import HTMLResponse
from routers.admin import router as admin_router
from routers.comentario import router as comentario_router
from routers.denuncia_produto import router as denuncia_produto_router
from routers.endereco_envio import router as endereco_envio_router
from routers.info_usuario import router as info_usuario_router
from routers.mensagem import router as mensagem_router
from routers.pedido import router as pedido_router
from routers.produto import router as produto_router
from routers.usuario import router as usuario_router
from routers.pesquisa import router as pesquisa_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

import logging

app = FastAPI(swagger_ui_parameters={"defaultModelsExpandDepth": -1})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos os domínios. Ajuste conforme necessário.
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos os métodos HTTP.
    allow_headers=["*"],  # Permitir todos os cabeçalhos.
)


# Manipulador de exceção para erros de validação
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Mostra detalhes do erro no console
    print("Erro de validação:", exc.errors())
    
    # Retorna o erro como uma resposta JSON, transformando-o em um formato serializável
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )


BASE_UPLOAD_DIR = "uploads/"
#PRODUCT_UPLOAD_DIR = "uploads/produto"
#app.mount("/video", StaticFiles(directory=os.path.join(BASE_UPLOAD_DIR, "")), name="")

# Montar o diretório de produtos
app.mount("/produto", StaticFiles(directory=os.path.join(BASE_UPLOAD_DIR, "produto")), name="produto")

# Montar o diretório de perfil
app.mount("/perfil", StaticFiles(directory=os.path.join(BASE_UPLOAD_DIR, "perfil")), name="perfil")

# Montar o diretório de documentos
app.mount("/documentos", StaticFiles(directory=os.path.join(BASE_UPLOAD_DIR, "documentos")), name="documentos")

# Montar o diretório de estatus
app.mount("/status", StaticFiles(directory=os.path.join(BASE_UPLOAD_DIR, "status")), name="status")

# Registrar os routers
app.include_router(admin_router)
app.include_router(comentario_router)
app.include_router(denuncia_produto_router)
app.include_router(endereco_envio_router)
app.include_router(info_usuario_router)
app.include_router(mensagem_router)
app.include_router(pedido_router)
app.include_router(produto_router)
app.include_router(usuario_router)
app.include_router(pesquisa_router)



"####Teste####"
"""@app.get('/video')

def video():
    import os
    videos=[]
    for video in os.listdir(f"{BASE_UPLOAD_DIR}/"):
        
            videos.append(f'<br><a href="video/{video}">{video}</a><br>')
    return HTMLResponse(str(videos))
"""
######Teste#####

Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,host="192.168.1.62", port=8000) 
