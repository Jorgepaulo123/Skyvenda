from controlers.comentario import *
from schemas import *
from auth import *
from fastapi import APIRouter

router=APIRouter(prefix="/comentarios",tags=["rotas de comentario"])
# Comentario routes

@router.post("/comentarios/")
def create_comentario(comentario: ComentarioCreate, db: Session = Depends(get_db)):
    return create_comentario_db(db=db, comentario=comentario)

@router.get("/{comentario_id}")
def read_comentario(comentario_id: int, db: Session = Depends(get_db)):
    db_comentario = get_comentario(db=db, comentario_id=comentario_id)
    if db_comentario is None:
        raise HTTPException(status_code=404, detail="Comentario not found")
    return db_comentario

@router.delete("/{comentario_id}")
def delete_comentario(comentario_id: int, db: Session = Depends(get_db)):
    db_comentario = delete_comentario(db=db, comentario_id=comentario_id)
    if db_comentario is None:
        raise HTTPException(status_code=404, detail="Comentario not found")
    return db_comentario


@router.put("/{comentario_id}")
def update_comentario(comentario_id: int, comentario: ComentarioUpdate, db: Session = Depends(get_db)):
    db_comentario = update_comentario_db(db=db, comentario_id=comentario_id, comentario=comentario)
    if db_comentario is None:
        raise HTTPException(status_code=404, detail="Comentario not found")
    return db_comentario