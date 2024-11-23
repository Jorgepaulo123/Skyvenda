from controlers.admin import *
from controlers.usuario import listar_usuarios_nao_verificados
from schemas import *
from controlers.info_usuario import *
from models import InfoUsuario
from auth import *
from controlers.usuario import ativar_usuario,delete_usuario_db,desativar_usuario
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter

router=APIRouter(prefix="/admin", tags=["rotas de admin"] )






@router.post("/token")
def login_admin(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    admin = authenticate_admin(db, form_data.username, form_data.password)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(admin.id)}, role="admin")  # Usando o ID do admin no token
    return {"access_token": access_token, "token_type": "bearer"}


@router.put("/usuario/{usuario_id}/revisao")
def revisar_usuario(usuario_id: int, nova_revisao: str, motivo: str = None, db: Session = Depends(get_db)):
    # Recupera o InfoUsuario baseado no ID do usuário
    db_info_usuario = db.query(InfoUsuario).filter(InfoUsuario.usuario_id == usuario_id).first()
    if not db_info_usuario:
        raise HTTPException(status_code=404, detail="InfoUsuario não encontrado.")

    # Chama a função para atualizar a revisão e enviar a notificação
    return update_revisao_info_usuario(db_info_usuario, nova_revisao, db, motivo)

# Admin routes
@router.post("/resgistro")
def create_admin(admin: AdminCreate, db: Session = Depends(get_db)):
    return register_admin(db=db, admin=admin)


@router.get("/{admin_id}")
def read_admins(admin_id: int, db: Session = Depends(get_db)):
    db_admin = get_admin(db=db, admin_id=admin_id)
    if db_admin is None:
        raise HTTPException(status_code=404, detail="Admin not found")
    return db_admin


@router.delete("/delete/user/{usuario_id}")
def delete_usuario(usuario_id: int, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    db_usuario = delete_usuario_db(db=db, usuario_id=usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {"msg": "Usuário excluído com sucesso"}


@router.delete("/delete/{admin_id}")
def delete_admins(admin_id: int, db: Session = Depends(get_db)):
    db_admin = delete_admin(db=db, admin_id=admin_id)
    if db_admin is None:
        raise HTTPException(status_code=404, detail="Admin not found")
    return db_admin


@router.get("/usuarios/nao_verificados/")
def obter_usuarios_nao_verificados(db: Session = Depends(get_db)):
    """
    Rota para obter todos os usuários não verificados.
    
    Returns:
        List[Usuario]: Lista de usuários não verificados.
    """
    usuarios_nao_verificados = listar_usuarios_nao_verificados(db=db)
    return usuarios_nao_verificados

@router.put("/admins/{admin_id}")
def update_admins(admin_id: int, admin: AdminUpdate, db: Session = Depends(get_db)):
    db_admin = update_admin(db=db, admin_id=admin_id, admin=admin)
    if db_admin is None:
        raise HTTPException(status_code=404, detail="Admin not found")
    return db_admin

# Rota para desativar o usuário
@router.put("/usuario/{usuario_id}/desativar")
def desativar_usuario_route(usuario_id: int, db: Session = Depends(get_db)):
    return desativar_usuario(db, usuario_id)

# Rota para ativar o usuário
@router.put("/usuario/{usuario_id}/ativar")
def ativar_usuario_route(usuario_id: int, db: Session = Depends(get_db)):
    return ativar_usuario(db, usuario_id)


@router.delete("/categorias/{categoria_id}")
def delete_categoria(categoria_id: int, db: Session = Depends(get_db)):
    db_categoria =delete_categoria(db=db, categoria_id=categoria_id)
    if db_categoria is None:
        raise HTTPException(status_code=404, detail="Categoria not found")
    return db_categoria