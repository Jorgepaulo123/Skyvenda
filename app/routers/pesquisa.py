from controlers.pesquisa import *
from schemas import *
from auth import *
from fastapi import APIRouter

router=APIRouter(prefix="/pesquisa",tags=["rotas de pesquisa"])


@router.get("/categorias/peso/")
def calcular_peso_categorias_route(db: Session = Depends(get_db), top_n: int = 5):
    """
    Rota para calcular o peso (frequência de pesquisa) das categorias mais pesquisadas.
    
    Args:
        db (Session): Sessão do banco de dados.
        top_n (int): Número de categorias mais pesquisadas a serem consideradas (padrão: 5).
    
    Returns:
        Lista de categorias e seus pesos (número de pesquisas).
    """
    return calcular_peso_categorias_mais_pesquisadas(db=db, top_n=top_n)



#ROTAS DE DELITE
@router.delete("/{pesquisa_id}/")
def eliminar_pesquisa_route(pesquisa_id: int, db: Session = Depends(get_db)):
    """
    Rota para eliminar uma pesquisa específica pelo seu ID.
    
    Args:
        pesquisa_id (int): ID da pesquisa a ser eliminada.
    
    Returns:
        Mensagem de sucesso.
    """
    return eliminar_pesquisa(db=db, pesquisa_id=pesquisa_id)


@router.get("/lista")
def listar_pesquisas_route(page: int = 1, limit: int = 10, usuario_id: int = None, db: Session = Depends(get_db)):
    """
    Rota para listar todas as pesquisas realizadas, com opção de filtrar por usuário.
    
    Args:
        page (int): Página de resultados.
        limit (int): Limite de resultados por página.
        usuario_id (int, opcional): ID do usuário para filtrar as pesquisas.
    
    Returns:
        Lista de pesquisas.
    """
    return listar_pesquisas(db=db, usuario_id=usuario_id, page=page, limit=limit)


