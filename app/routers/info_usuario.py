from controlers.info_usuario import *
from schemas import *
from auth import *
from fastapi import APIRouter,Form
router=APIRouter(prefix="/info_usuario",tags=["rotas de infousuari"])


@router.post("/")
async def create_info_usuario(
    fotos: List[UploadFile] = File(...),  # Lista de 3 fotos (frente, verso do BI, e foto do usuário com BI)
    provincia: str = Form(...),
    distrito: str = Form(...),
    data_nascimento: str = Form(...),
    localizacao: str = Form(...),
    estado: str = Form(...),  
    avenida: Optional[str] = Form(None),
    nacionalidade:Optional[str]=Form(None),
    bairro: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Validação para garantir que 3 fotos sejam enviadas
    if len(fotos) != 3:
        raise HTTPException(status_code=400, detail="Você deve enviar exatamente 3 fotos: frente, verso do BI, e uma foto sua com o BI.")

    # Salvando as imagens
    perfil_filename = save_image(fotos[2], PROFILE_UPLOAD_DIR)  # Foto do usuário segurando o BI (3ª foto)
    bi_frente_filename = save_image(fotos[0], DOCUMENT_UPLOAD_DIR)  # Foto da frente do BI (1ª foto)
    bi_tras_filename = save_image(fotos[1], DOCUMENT_UPLOAD_DIR)  # Foto do verso do BI (2ª foto)

    # Criando o objeto InfoUsuarioCreate para facilitar a passagem de dados
    info_usuario_data = InfoUsuarioCreate(
        perfil=perfil_filename,
        provincia=provincia,
        foto_bi=f"{bi_frente_filename},{bi_tras_filename},{perfil_filename}",  # Fotos concatenadas
        distrito=distrito,
        data_nascimento=data_nascimento,
        localizacao=localizacao,
        estado=estado,
        usuario_id=current_user.id,
        avenida=avenida,
        nacionalidade=nacionalidade,
        bairro=bairro
    )

    # Criando a entrada no banco de dados
    #db_info_usuario = create_info_usuario_db(db=db, info_usuario=info_usuario_data, current_user_id=current_user.id)
    db_info_usuario = create_info_usuario_db(db=db, info_usuario=info_usuario_data, current_user=current_user.id)

    return {"message": "Informações do usuário criadas com sucesso", "info_usuario": db_info_usuario}


@router.post("/{info_usuario_id}/perfil/")
async def upload_profile_picture(
    perfil: Usuario = Depends(get_current_user),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Verifique o tipo de arquivo
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="O arquivo deve ser uma imagem")

    # Salva a imagem no servidor
    new_filename = save_image(file, PROFILE_UPLOAD_DIR)

    # Atualiza a foto de perfil no banco de dados
    update_info_usuario_profile_picture(db, perfil, new_filename)

    return {"filename": new_filename}


@router.get("/{info_usuario_id}")
def read_info_usuario(info_usuario_id: int, db: Session = Depends(get_db)):
    db_info_usuario = get_info_usuario(db=db, info_usuario_id=info_usuario_id)
    if db_info_usuario is None:
        raise HTTPException(status_code=404, detail="InfoUsuario not found")
    return db_info_usuario


@router.delete("/{info_usuario_id}")
def delete_info_usuario(info_usuario_id: int, db: Session = Depends(get_db)):
    db_info_usuario = delete_info_usuario(db=db, info_usuario_id=info_usuario_id)
    if db_info_usuario is None:
        raise HTTPException(status_code=404, detail="InfoUsuario not found")
    return db_info_usuario

@router.put("/{info_usuario_id}")
def update_info_usuario(info_usuario: InfoUsuarioUpdate, db: Session = Depends(get_db),info_usuario_id:Usuario = Depends(get_current_user),):
    db_info_usuario = update_info_usuario_db(db=db, info_usuario_id=info_usuario_id, info_usuario=info_usuario)
    if db_info_usuario is None:
        raise HTTPException(status_code=404, detail="InfoUsuario not found")
    return db_info_usuario