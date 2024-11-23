from controlers.produto import *
from controlers.pesquisa import *
from schemas import *
from auth import *
from models import Message, MessageType
from fastapi import APIRouter,Form,File,Query
from decimal import Decimal


router=APIRouter(prefix="/produtos",tags=["rotas de produtos"])


@router.put("/status/atualizar/{status_id}")
def atualizar_status(
    status_id: int,
    duracao_dias: int = Form(...),  # Corrigido para "duracao_dias"
    conteudo: str = Form(None),
    imagem: UploadFile = Form(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Rota para atualizar um status existente do usuário.
    """
    try:
        resultado = atualizar_status_controller(
            db=db,
            usuario_id=current_user.id,
            status_id=status_id,
            dias_adicionais=duracao_dias,  # Use "duracao_dias" aqui
            conteudo=conteudo,
            imagem=imagem
        )
        return resultado
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{status_id}/visualizar/")
async def visualizar(status_id: int, db: Session = Depends(get_db)):
    resultado = visualizar_status(status_id=status_id, db=db)
    return resultado
# Rota para promover um produto e criar um anúncio
@router.post("/{produto_id}/promover")
def promover_produto_route(
    produto_id: int,
    dias: int, 
    titulo: str, 
    descricao: str, 
    tipo: str, 
    usuario_id: int, 
    db: Session = Depends(get_db)
):
    return promover_produto(produto_id, dias, db, usuario_id, titulo, descricao, tipo)


@router.post("/{produto_id}/reativar/")
def reativar_produto_endpoint(produto_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return reativar_produto(produto_id=produto_id, current_user=current_user, db=db) 


@router.get("/pegar/{produto_id}")
async def get_produto(produto_id: int, db: Session = Depends(get_db)):
    # Busca o produto pelo ID
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    # Calcula o tempo de publicação em formato legível
    tempo_publicacao = calcular_tempo_publicacao(produto.data_publicacao)
    
    # Retorna os dados do produto com o tempo de publicação formatado
    return {
        "id": produto.id,
        "nome": produto.nome,
        "capa": produto.capa,
        "preco": str(produto.preco),
        "quantidade_estoque": produto.quantidade_estoque,
        "estado": produto.estado,
        "provincia": produto.provincia,
        "distrito": produto.distrito,
        "localizacao": produto.localizacao,
        "revisao": produto.revisao,
        "disponiblidade": produto.disponiblidade,
        "descricao": produto.descricao,
        "categoria": produto.categoria,
        "detalhes": produto.detalhes,
        "tipo": produto.tipo,
        "visualizacoes": produto.visualizacoes,
        "likes": produto.likes,
        "data_publicacao": tempo_publicacao
    }




@router.post("/publicar")
async def create_produto(
    nome: str = Form(...),
    preco: Decimal = Form(...),
    quantidade_estoque: Optional[int] = Form(None),
    estado: str = Form(...),
    distrito: str = Form(...),
    provincia: str = Form(...),
    localizacao: str = Form(...),
    revisao:  Optional[str] = Form(None),
    disponiblidade: str = Form(...),
    descricao: str = Form(...),
    categoria: str = Form(...),
    detalhes: str = Form(...),
    tipo: str = Form(...),
    fotos: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)  # Renomeie para evitar confusão
):
    # Verifica se pelo menos uma foto foi enviada
    if not fotos:
        raise HTTPException(status_code=400, detail="Pelo menos uma foto deve ser enviada.")
    
    # A primeira foto será a capa, as demais serão adicionais
    capa = fotos[0]
    outras_fotos = fotos[1:]

    # Criação do objeto ProdutoCreate
    produto_data = ProdutoCreate(
        nome=nome,
        preco=preco,
        quantidade_estoque=quantidade_estoque,
        estado=estado,
        provincia=provincia,
        distrito=distrito,
        localizacao=localizacao,
        revisao=revisao,
        disponiblidade=disponiblidade,
        descricao=descricao,
        categoria=categoria,
        detalhes=detalhes,
        tipo=tipo,
        CustomerID=current_user.id,  # Use o ID do usuário
    )

    # Gera o slug único
    slug = gerar_slug_unico(produto_data.nome, db)
    produto_data.slug = slug  # Atribui o slug gerado ao produto

    # Verifica se o usuário completou o registro antes de salvar o produto
    db_produto = create_produto_db_with_image(
        db=db, 
        produto=produto_data,
        user_id=current_user.id,  # Passe o ID do usuário aqui também
        files=fotos,  # Passa todas as fotos
        extra_files=outras_fotos  # Fotos adicionais
    )
    print("Produto cadastrado com sucesso:", db_produto)

    return {"message": "Produto criado com sucesso", "produto": db_produto}


@router.get("/pesquisa/")
def pesquisa_avancada(
    termo: str, 
    offset: int = Query(0, description="Ponto inicial da paginação"), 
    limit: int = Query(10, description="Limite de itens por página"), 
    db: Session = Depends(get_db), 
    user_id: Optional[int] = Query(None, description="ID opcional do usuário")
):
    """
    Rota para pesquisa avançada de produtos.
    """
    produtos = executar_pesquisa_avancada(
        termo=termo, 
        offset=offset, 
        limit=limit, 
        db=db, 
        user_id=user_id
    )
    return produtos


@router.get("/{slug}")
def read_produto(slug: str, db: Session = Depends(get_db)):
    # Busca o produto pelo slug no banco de dados
    db_produto = db.query(Produto).filter(Produto.slug == slug).first()
    
    # Verifica se o produto foi encontrado
    if db_produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    return db_produto

@router.get("/detalhes/{slug}")
def produto_detalhado(slug: str, db: Session = Depends(get_db)):
    return get_produto_detalhado(db, slug)

@router.get("/produto/{produto_id}/likes")
def produto_likes(produto_id: int, db: Session = Depends(get_db)):
    return get_produto_likes(db, produto_id)

@router.delete("/produtos/{produto_id}")
def delete_produto(produto_id: int, db: Session = Depends(get_db)):
    db_produto = delete_produto(db=db, produto_id=produto_id)
    if db_produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return db_produto

# A rota precisa de `Form` para receber JSON junto com arquivos
@router.put("/{produto_id}")
async def update_produto(
    produto_id: int,
    nome: Optional[str] = Form(None),
    preco: Optional[float] = Form(None),
    quantidade_estoque: Optional[int] = Form(None),
    estado: Optional[str] = Form(None),
    disponiblidade: Optional[str] = Form(None),
    descricao: Optional[str] = Form(None),
    detalhes: Optional[str] = Form(None),
    tipo: Optional[str] = Form(None),
    categoria: Optional[int] = Form(None),
    CustomerID: Optional[int] = Form(None),
    files: List[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    # Transforme os dados recebidos via Form em um dicionário para atualizar o produto
    produto = ProdutoUpdate(
        nome=nome,
        preco=preco,
        quantidade_estoque=quantidade_estoque,
        estado=estado,
        disponiblidade=disponiblidade,
        descricao=descricao,
        detalhes=detalhes,
        tipo=tipo,
        categoria=categoria,
        CustomerID=CustomerID,
      
    )
    
    # Função de atualização do produto
    db_produto = update_produto_db_with_images(db=db, produto_id=produto_id, produto=produto, files=files)
    
    if db_produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    return db_produto

@router.post("/{produto_slug}/like")
def like_produto(
    produto_slug: str, 
    db: Session = Depends(get_db),
    user_id: Usuario = Depends(get_current_user)
):
    return toggle_like_produto(db, produto_slug, user_id.id)


@router.get("/anuncios/")
def listar_anuncios(db: Session = Depends(get_db)):
    """
    Rota para listar todos os anúncios válidos junto com os produtos associados.
    """
    return listar_anuncios_com_produtos(db)

@router.get("/promovidos/")
def listar_produtos_promovidos(db: Session = Depends(get_db)):
    return get_produtos_promovidos(db)


@router.get("/")
def listar_produtos(
    db: Session = Depends(get_db),
    user_id: int = Query(None, description="ID opcional do usuário para verificar likes"),
    limit: int = Query(10, description="Quantidade de produtos por página"),
    offset: int = Query(0, description="Ponto inicial para a paginação")
):
    """
    Lista produtos com informações detalhadas e, se `user_id` for fornecido, indica se o usuário deu like.
    - Prioriza produtos recentes com ordem aleatória.
    - Lista demais produtos organizados por peso.

    Args:
        user_id (int): ID do usuário opcional para verificar os likes.
        limit (int): Quantidade de produtos a exibir por página.
        offset (int): Índice de início da listagem para paginação.

    Returns:
        List[dict]: Lista paginada com detalhes específicos dos produtos e se o usuário deu like, se `user_id` for fornecido.
    """
    produtos = db.query(Produto).all()

    if not produtos:
        raise HTTPException(status_code=404, detail="Nenhum produto encontrado.")
    
    produtos_ordenados = combinar_produtos(produtos, db)
    produtos_paginados = produtos_ordenados[offset: offset + limit]

    # Consulta o usuário apenas se `user_id` for fornecido
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first() if user_id else None

    return [
        {
            "id": produto.id,
            "nome": produto.nome,
            "capa": produto.capa,
            "fotos": produto.fotos,
            "preco": float(produto.preco),
            "quantidade_estoque": produto.quantidade_estoque,
            "estado": produto.estado,
            "provincia": produto.provincia,
            "distrito": produto.distrito,
            "localizacao": produto.localizacao,
            "revisao": produto.revisao,
            "disponibilidade": produto.disponiblidade,
            "descricao": produto.descricao,
            "categoria": produto.categoria,
            "detalhes": produto.detalhes,
            "tipo": produto.tipo,
            "view": produto.visualizacoes,
            "ativo": produto.ativo,
            "CustomerID": produto.CustomerID,
            "likes": produto.likes,

            "slug": produto.slug,
            "tempo": calcular_tempo_publicacao(produto.data_publicacao),
              "usuario": {
                "id": produto.usuario.id,
                "nome": produto.usuario.nome,
            },
            "liked": usuario in produto.usuarios_que_deram_like if usuario else None,
            "comentario": db.query(Comentario).filter(Comentario.produtoID == produto.id).count()
        
        }
        for produto in produtos_paginados
    ]

@router.get("/usuarios/{user_id}/produtos/")
def get_produtos_by_user(user_id: int, db: Session = Depends(get_db)):
    """
    Rota que retorna todos os produtos de um usuário específico.
    """
    produtos = db.query(Produto).filter(Produto.CustomerID == user_id).all()
    if not produtos:
        raise HTTPException(status_code=404, detail="Nenhum produto encontrado para este usuário.")
    return produtos

@router.post("/usuarios/{usuario_id}/status/")
async def criar_status(
    usuario_id: int,
    conteudo: str = Form(None),
    imagem: UploadFile = File(None),
    duracao_dias: int = Form(...),
    db: Session = Depends(get_db)
):
    # Chamar o controlador para criar o status
    resultado = criar_status_controller(
        usuario_id=usuario_id,
        conteudo=conteudo,
        imagem=imagem,
        duracao_dias=duracao_dias,
        db=db
    )

    return resultado



@router.post("/status/{status_id}/responder")
def responder_status(
    status_id: int,
    sender_id: int,
    receiver_id: int,
    conteudo: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # Verificar se o status existe
    status = db.query(Status).filter(Status.id == status_id).first()
    if not status:
        raise HTTPException(status_code=404, detail="Status não encontrado")

    # Verificar se o conteúdo é fornecido
    if not conteudo and not status.imagem_url:
        raise HTTPException(status_code=400, detail="Conteúdo ou imagem do status é necessário para responder")

    # Criar a mensagem de resposta
    nova_mensagem = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=conteudo,
        message_type=MessageType.TEXT if not status.imagem_url else MessageType.IMAGE,
        file_url=status.imagem_url  # Usar a imagem do status
    )

    db.add(nova_mensagem)
    db.commit()

    return {"message": "Resposta enviada com sucesso", "message_id": nova_mensagem.id}
