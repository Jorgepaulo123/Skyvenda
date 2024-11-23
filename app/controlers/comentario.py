from sqlalchemy.orm import Session
from models import Comentario
from schemas import ComentarioCreate, ComentarioUpdate

def create_comentario_db(db: Session, comentario: ComentarioCreate):
    db_comentario = Comentario(**comentario.dict())
    db.add(db_comentario)
    db.commit()
    db.refresh(db_comentario)
    return db_comentario

def get_comentarios(db: Session):
    return db.query(Comentario).all()
   


def get_comentario(db: Session, comentario_id: int):
    return db.query(Comentario).filter(Comentario.id == comentario_id).first()

def update_comentario_db(db: Session, comentario_id: int, comentario: ComentarioUpdate):
    db_comentario = db.query(Comentario).filter(Comentario.id == comentario_id).first()
    if db_comentario:
        for key, value in comentario.dict().items():
            setattr(db_comentario, key, value)
        db.commit()
        db.refresh(db_comentario)
    return db_comentario

def delete_comentario(db: Session, comentario_id: int):
    db_comentario = db.query(Comentario).filter(Comentario.id == comentario_id).first()
    if db_comentario:
        db.delete(db_comentario)
        db.commit()
    return db_comentario
