from fastapi import APIRouter, Depends, HTTPException, status,Form
from sqlalchemy.orm import Session
from models import Usuario, Transacao, Publicacao, Notificacao
from schemas import *
from database import SessionLocal
from fastapi.security import OAuth2PasswordRequestForm
from models import *
from passlib.context import CryptContext
from controlers.usuario import *
from controlers.produto import seguir_usuario,get_seguidores
from auth import get_current_user, create_access_token, authenticate_user
from passlib.context import CryptContext
from datetime import datetime
from auth import *
from fastapi.responses import RedirectResponse
import requests
import httpx
import json


router = APIRouter(prefix="/usuario", tags=["rotas de usuarios"])



#FUNCOES
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
#mpesa
url = "https://api.sandbox.vm.co.mz:18352/ipg/v1x/c2bPayment/singleStage/"
#google
GOOGLE_CLIENT_ID ="447649377867-1ff1uie6eeds2u3cq5er9virar9vden5.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
GOOGLE_REDIRECT_URI = "http://localhost:5000/auth/callback"
GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URI = "https://www.googleapis.com/oauth2/v3/userinfo"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()





# Modelo para entrada de pagamento
class PagamentoModel(BaseModel):
    msisdn: str  # Número de telefone do cliente
    valor: str   # Valor a ser carregado


# Função para adicionar saldo usando M-Pesa (sem autenticação)
@router.post("/{user_id}/pagamento/")
def adicionar_saldo_via_mpesa(msisdn: str, valor: int, db: Session = Depends(get_db),current_user: Usuario = Depends(get_current_user)):
    # Buscar o usuário no banco de dados
    usuario = db.query(Usuario).filter(Usuario.id == current_user.id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    # Verifica se o usuário passou pela revisão
    info_usuario = db.query(InfoUsuario).filter(InfoUsuario.usuario_id == usuario.id).first()
    if not info_usuario or info_usuario.revisao != "sim":
        raise HTTPException(status_code=403, detail="Usuário não passou pela revisão e não pode adicionar saldo.")
    
    # Cabeçalhos e payload para a requisição M-Pesa
    # Cabeçalhos da solicitação
    token="XfsLebYAsnNPRsMu6JKfRPH9W5fhzSb+W3cdizVQ/Bm5ho2Xi/tn/Oo4bwHmFLqYlHQVnrog3MziMmxZLN5NnPEqCu5F9tLeYwmIo4mqNp544Ai5B8s+IAbxr//WLIS+pk992fp6uZl8IgFkQreqsN+leWSgQdeW7oiGl7Z5k6e10uc4xuD3KOEldtye0Pzjj0DmHNdhDh8SzpdgkjyEmWPhvyMwCVxn80pqaKAH5UUDGxv+dbY4HgsoAprMC+hclhHkVfk5VfqNlOToxpn6LmfeoZZ5BJJysEA/Y/T3zlK9JYq+dWahlWyMv+UoMEh7VG1lw3k/Hb7dqKkSRmrhStsuRrHjAITKRSoWv98ZWntQQua+Fz/BGV7v6f6qsytTBHCWVJD3qWl3phKztYWpr0CeJ3aGYns+gtKP04V2WdPrqVylYJFEQILGCfKmtFqYZ3rhdKhgs4UDAOQMCkED4uS+op0p+I6kW6ftAyw6WDu5dqQ5OFKV3++f/015kptDzRpoieB1EfUltgabnfWCNzivi7ZJY6S+5+ZJPDI9ORjYq+QlF+Qi/RQmJiGWDh+S/UY2sA2d9692lfmWKk3+10YAUoZlQTlq9qCvqVXYVwquiLkUpHhnpNMbidVBwuBM03IxA0SrmervTM7RY2mS1BXTwO2IQekX+9bnJ6+Tpkk="
    headers = {
           "Content-Type": "application/json",
           "Authorization": f"Bearer {token}",
           "Origin": "developer.mpesa.vm.co.mz"
    }

    # Dados da requisição
    data = {
        "input_TransactionReference": "T12344C",  # Gere uma referência única para cada transação
        "input_CustomerMSISDN": msisdn,           # Número de telefone do cliente
        "input_Amount": str(valor),               # Valor a ser carregado
        "input_ThirdPartyReference": "11115",     # Referência única de terceiros
        "input_ServiceProviderCode": "171717"     # Código do provedor de serviço
    }

    url_pyment = 'https://api.sandbox.vm.co.mz:18345/ipg/v1x/b2cPayment/'
# Enviar a requisição para a API da M-Pesa
    response = requests.post(url_pyment, headers=headers,verify=True, data=json.dumps(data))

    if response.status_code ==422:
        transacao = Transacao(usuario_id=usuario.id, msisdn=msisdn, valor=valor, referencia=data["input_TransactionReference"], status="saldo insuficiente")
        db.add(transacao)
        db.commit()
        return {"msg": "Saldo insuficiente."}

    if response.status_code ==400:
        return {"msg": "ocorreu um erro"}
    

    # Verifique se o status da resposta é de sucesso
    if response.status_code == 200 or response.status_code == 201:
        # Buscar ou criar a wallet do usuário
        wallet = db.query(Wallet).filter(Wallet.usuario_id == usuario.id).first()
        
        # Se a wallet não existe, cria uma nova
        if not wallet:
            wallet = Wallet(usuario_id=usuario.id, saldo_principal=0)  # Inicializa com saldo 0
            db.add(wallet)
            db.commit()
            db.refresh(wallet)

        # Adicionar o valor ao saldo da wallet
        wallet.saldo_principal -= valor
        db.commit()
        db.refresh(wallet)

        # Registrar transação com sucesso
        transacao = Transacao(usuario_id=usuario.id, msisdn=msisdn, valor=valor, referencia=data["input_TransactionReference"], status="sucesso",tipo="saida")
        db.add(transacao)
        db.commit()
        
        return {f"msg": "confirmado retirou o valor {valor}", "saldo_atual": wallet.saldo_principal}
    else:
        # Exibir o conteúdo bruto da resposta para depuração
        print(f"Resposta da M-Pesa: {response.text}")
        raise HTTPException(status_code=400, detail=f"Erro ao processar a transação: {response.text}")

@router.get("/auth/callback")
async def google_auth_callback(code: str, db: Session = Depends(get_db)):
    # Troca o código de autorização por um token de acesso
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        token_response = await client.post(GOOGLE_TOKEN_URI, data=data)
        token_json = token_response.json()

        if "access_token" not in token_json:
            raise HTTPException(status_code=400, detail="Erro ao obter token de acesso")

        access_token = token_json["access_token"]

        # Obter as informações do usuário autenticado
        userinfo_response = await client.get(GOOGLE_USERINFO_URI, headers={"Authorization": f"Bearer {access_token}"})
        userinfo = userinfo_response.json()

        google_id = userinfo.get("sub")
        email = userinfo.get("email")
        nome_completo = userinfo.get("name")
        primeiro_nome = userinfo.get("given_name")
        sobrenome = userinfo.get("family_name")
        foto_perfil = userinfo.get("picture")  # Foto do perfil

        # Verifica se o usuário já existe no banco de dados pelo google_id ou email
        user = db.query(Usuario).filter((Usuario.google_id == google_id) | (Usuario.email == email)).first()

        if not user:
            # Se o usuário não existir, cria um novo
            new_user = Usuario(
                email=email,
                nome=nome_completo,
                google_id=google_id,
                username=sobrenome,  # Sobrenome como username
                senha=None,  # Não salvamos senha para usuários do Google
                foto_perfil=foto_perfil  # Armazena a foto do perfil
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user = new_user

        # Cria o token JWT para o usuário existente ou recém-criado
        access_token = create_access_token(data={"sub": str(user.id)})

        # Redireciona para a página de produtos
        redirect_url = f"http://localhost:5000/auth/callback"
        return RedirectResponse(url=redirect_url)

@router.get("/perfil")
def read_perfil(db: Session = Depends(get_db),current_user: Usuario = Depends(get_current_user)):
    print(current_user.id)
    perfil = get_perfil(db=db, usuario_id=current_user.id)
    if perfil is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return perfil

@router.get("/user")
def read_perfil(db: Session = Depends(get_db),current_user: Usuario = Depends(get_current_user)):
    perfil = db.query(Usuario).filter_by(id=current_user.id).first()
    if perfil is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {
        "id":perfil.id,
        'username':perfil.username,
        'email':perfil.email,
        'name':perfil.nome,
        'conta_pro':perfil.conta_pro,
        "tipo":perfil.tipo,
        'perfil':perfil.foto_perfil,
        'revisado':perfil.revisao

    }

# Rotas relacionadas a usuários
@router.put("/{usuario_id}/desativar_pro/")
def desativar_conta_pro(usuario_id: int, db: Session = Depends(get_db)):
    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    if not db_usuario.conta_pro:
        raise HTTPException(status_code=400, detail="Conta PRO já está desativada para este usuário.")

    db_usuario.conta_pro = False
    db_usuario.limite_diario_publicacoes = 1
    db.commit()
    db.refresh(db_usuario)

    return {"message": "Conta PRO desativada com sucesso.", "usuario": db_usuario}


# Rota para listar todas as publicações
@router.get("/publicacoes/")
def listar_publicacoes(db: Session = Depends(get_db)):
    # Buscar todas as publicações no banco de dados
    publicacoes = db.query(Publicacao).all()
    
    # Verificar se há publicações
    if not publicacoes:
        raise HTTPException(status_code=404, detail="Nenhuma publicação encontrada.")
    
    return publicacoes


@router.post("/{usuario_id}/seguir")
def seguir_usuario_route(usuario_id: int, db: Session = Depends(get_db),seguidor: Usuario = Depends(get_current_user)):
    # Chama a função que implementa a lógica de seguir um usuário
    resultado = seguir_usuario(db, usuario_id, seguidor.id)
    
    return resultado


@router.get("/usuarios/{usuario_id}/seguindo")
def get_usuario_seguindo(usuario_id: int, db: Session = Depends(get_db)):
    return get_seguidores(usuario_id, db)

@router.post("/recuperar_senha/")
def recuperar_senha(email_schema: EmailSchema, db: Session = Depends(get_db)):
    email = email_schema.email
    usuario = db.query(Usuario).filter(Usuario.email == email).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    # Verifica se o usuário tem uma senha configurada
    if not usuario.senha or usuario.senha == "":
        raise HTTPException(status_code=400, detail="Usuários cadastrados via Google não podem recuperar senha.")
    
    # Gera uma nova senha temporária
    nova_senha = gerar_senha_temporaria()

    hashed_senha = pwd_context.hash(nova_senha)
    usuario.senha = hashed_senha
    db.commit()


# Função para adicionar saldo usando M-Pesa (sem autenticação)
@router.post("/{user_id}/adicionar_saldo/")
def adicionar_saldo_via_mpesa(msisdn: str, valor: int, db: Session = Depends(get_db),current_user: Usuario = Depends(get_current_user)):
    # Buscar o usuário no banco de dados
    usuario = db.query(Usuario).filter(Usuario.id == current_user.id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    # Verifica se o usuário passou pela revisão
    info_usuario = db.query(InfoUsuario).filter(InfoUsuario.usuario_id == usuario.id).first()
    if not info_usuario or info_usuario.revisao != "sim":
        raise HTTPException(status_code=403, detail="Usuário não passou pela revisão e não pode adicionar saldo.")
    
    # Cabeçalhos e payload para a requisição M-Pesa
    # Cabeçalhos da solicitação
    token="XfsLebYAsnNPRsMu6JKfRPH9W5fhzSb+W3cdizVQ/Bm5ho2Xi/tn/Oo4bwHmFLqYlHQVnrog3MziMmxZLN5NnPEqCu5F9tLeYwmIo4mqNp544Ai5B8s+IAbxr//WLIS+pk992fp6uZl8IgFkQreqsN+leWSgQdeW7oiGl7Z5k6e10uc4xuD3KOEldtye0Pzjj0DmHNdhDh8SzpdgkjyEmWPhvyMwCVxn80pqaKAH5UUDGxv+dbY4HgsoAprMC+hclhHkVfk5VfqNlOToxpn6LmfeoZZ5BJJysEA/Y/T3zlK9JYq+dWahlWyMv+UoMEh7VG1lw3k/Hb7dqKkSRmrhStsuRrHjAITKRSoWv98ZWntQQua+Fz/BGV7v6f6qsytTBHCWVJD3qWl3phKztYWpr0CeJ3aGYns+gtKP04V2WdPrqVylYJFEQILGCfKmtFqYZ3rhdKhgs4UDAOQMCkED4uS+op0p+I6kW6ftAyw6WDu5dqQ5OFKV3++f/015kptDzRpoieB1EfUltgabnfWCNzivi7ZJY6S+5+ZJPDI9ORjYq+QlF+Qi/RQmJiGWDh+S/UY2sA2d9692lfmWKk3+10YAUoZlQTlq9qCvqVXYVwquiLkUpHhnpNMbidVBwuBM03IxA0SrmervTM7RY2mS1BXTwO2IQekX+9bnJ6+Tpkk="
    headers = {
           "Content-Type": "application/json",
           "Authorization": f"Bearer {token}",
           "Origin": "developer.mpesa.vm.co.mz"
    }

    # Dados da requisição
    data = {
        "input_TransactionReference": "T12344C",  # Gere uma referência única para cada transação
        "input_CustomerMSISDN": msisdn,           # Número de telefone do cliente
        "input_Amount": str(valor),               # Valor a ser carregado
        "input_ThirdPartyReference": "11115",     # Referência única de terceiros
        "input_ServiceProviderCode": "171717"     # Código do provedor de serviço
    }

   
# Enviar a requisição para a API da M-Pesa
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code ==422:
        transacao = Transacao(usuario_id=usuario.id, msisdn=msisdn,tipo="entrada", valor=valor, referencia=data["input_TransactionReference"], status="saldo insuficiente")
        db.add(transacao)
        db.commit()
        return {"msg": "Saldo insuficiente."}

    if response.status_code ==400:
        return {"msg": "ocorreu um erro"}
    

    # Verifique se o status da resposta é de sucesso
    if response.status_code == 200 or response.status_code == 201:
        # Buscar ou criar a wallet do usuário
        wallet = db.query(Wallet).filter(Wallet.usuario_id == usuario.id).first()
        
        # Se a wallet não existe, cria uma nova
        if not wallet:
            wallet = Wallet(usuario_id=usuario.id, saldo_principal=0)  # Inicializa com saldo 0
            db.add(wallet)
            db.commit()
            db.refresh(wallet)

        # Adicionar o valor ao saldo da wallet
        wallet.saldo_principal += valor
        db.commit()
        db.refresh(wallet)

        # Registrar transação com sucesso
        transacao = Transacao(usuario_id=usuario.id, msisdn=msisdn, valor=valor, referencia=data["input_TransactionReference"], status="sucesso",tipo="entrada")
        db.add(transacao)
        db.commit()
        
        return {"msg": "Saldo adicionado com sucesso!", "saldo_atual": wallet.saldo_principal}
    else:
        # Exibir o conteúdo bruto da resposta para depuração
        print(f"Resposta da M-Pesa: {response.text}")
        raise HTTPException(status_code=400, detail=f"Erro ao processar a transação: {response.text}")




@router.get("/{user_id}/saldo/")
def obter_saldo(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    # Buscar o usuário no banco de dados
    usuario = db.query(Usuario).filter(Usuario.id == current_user.id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    # Buscar a wallet do usuário
    wallet = db.query(Wallet).filter(Wallet.usuario_id == usuario.id).first()

    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet não encontrada para o usuário.")

    # Pegando o saldo principal da wallet
    saldo_principal = wallet.saldo_principal

    # Pegando o saldo de bônus (por exemplo, se houver uma tabela de Bônus relacionada ao usuário)
    bonus = wallet.bonus if hasattr(wallet, 'bonus') else 0.0  # Atribuindo 0 se não houver bônus

    # Pegando o saldo congelado (por exemplo, relacionado a transações pendentes)
    saldo_congelado = wallet.saldo_congelado if hasattr(wallet, 'saldo_congelado') else 0.0  # Atribuindo 0 se não houver saldo congelado

    return {
        "saldo_principal": saldo_principal,
        "saldo_bonus": bonus,
        "saldo_congelado": saldo_congelado
    }

@router.put("/{usuario_id}/ativar_pro/")
def ativar_conta_pro(usuario_id: int, db: Session = Depends(get_db)):
    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    if db_usuario.conta_pro:
        raise HTTPException(status_code=400, detail="Usuário já possui uma conta PRO ativa.")

    db_usuario.conta_pro = True
    db_usuario.data_ativacao_pro = datetime.utcnow()

    db.commit()
    db.refresh(db_usuario)

    return {"message": "Conta PRO ativada com sucesso.", "usuario": db_usuario}
    

# Rota para o login (gera o token com ID e tipo de usuário)
@router.post("/token")
def login_user(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    # Autenticação do usuário
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Gera o token de acesso com ID e tipo de usuário
    access_token = create_access_token(user_id=user.id, user_role=user.tipo)  # Inclui ID e tipo no token
    return {"access_token": access_token, "token_type": "bearer","id":user.id}



@router.post("/{user_id}/publicar/")
def publicar_texto(user_id: int, publicacao: PublicacaoCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Usuário não autorizado a publicar para este ID.")

    nova_publicacao = Publicacao(usuario_id=current_user.id, conteudo=publicacao.conteudo)
    
    db.add(nova_publicacao)
    db.commit()
    db.refresh(nova_publicacao)

    return {"msg": "Publicação criada com sucesso!", "publicacao": nova_publicacao}


# Endpoint para cadastro de um novo usuário utilizando dados de formulário
@router.post("/cadastro")
def create_usuario_endpoint(
    nome: str = Form(...),
    username: str = Form(...),
    email: EmailStr = Form(...),
    senha: Optional[str] = Form(None),
    tipo: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # Verifica se o usuário já existe com o mesmo email ou username
    existing_user = db.query(Usuario).filter(
        (Usuario.email == email) | (Usuario.username == username)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário com este email ou username já existe."
        )

    # Cadastra o usuário se ele ainda não existir
    print(username)
    print(senha)
    return register_user(db, nome, username, email, senha, tipo)

@router.get("/pro/")
def listar_usuarios_pro(db: Session = Depends(get_db)):
    usuarios_pro = db.query(Usuario).filter(Usuario.conta_pro == True).all()

    if not usuarios_pro:
        raise HTTPException(status_code=404, detail="Nenhum usuário com conta PRO encontrado.")

    return {"usuarios_pro": usuarios_pro}


@router.get("/{usuario_id}/notificacoes/")
def listar_notificacoes(usuario_id: int, db: Session = Depends(get_db)):
    notificacoes = db.query(Notificacao).filter(Notificacao.usuario_id == usuario_id).all()
    return notificacoes


@router.put("/{usuario_id}")
def update_usuario_endpoint(usuario_id: int, usuario: UsuarioUpdate, db: Session = Depends(get_db)):
    db_usuario = update_usuario_db(db=db, usuario_id=usuario_id, usuario=usuario)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario not found")
    return db_usuario


@router.put("/{user_id}/atualizar_senha/")
def atualizar_senha(user_id: int, senha_atual: str, nova_senha: str, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    if not usuario.senha or usuario.senha == "":
        raise HTTPException(status_code=400, detail="Usuários cadastrados via Google não podem alterar a senha.")
    if not verify_password(senha_atual, usuario.senha):
        raise HTTPException(status_code=400, detail="Senha atual incorreta.")

    hashed_nova_senha = hash_password(nova_senha)
    usuario.senha = hashed_nova_senha
    db.commit()

    return {"msg": "Senha atualizada com sucesso."}


@router.get("/saldo")
def get_saldo(db: Session = Depends(get_db), 
              current_user: Usuario = Depends(get_current_user)):  # Usuário autenticado é extraído automaticamente
    
    # Verifica se o usuário existe no banco de dados
    usuario = db.query(Usuario).filter(Usuario.id == current_user.id).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    # Retorna o saldo do usuário autenticado
    return {"saldo": usuario.saldo}




# Rota para obter todas as transações de um usuário específico
@router.get("/{user_id}/transacoes/")
def listar_transacoes(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    # Verificar se o usuário existe
    usuario = db.query(Usuario).filter(Usuario.id ==  current_user.id).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    # Buscar todas as transações do usuário
    transacoes = db.query(Transacao).filter(Transacao.usuario_id == current_user.id).all()

    # Verificar se existem transações
    if not transacoes:
        raise HTTPException(status_code=404, detail="Nenhuma transação encontrada.")
    
    return transacoes

@router.get("/transacoes/")
def listar_todas_transacoes(db: Session = Depends(get_db)):
    # Buscar todas as transações do sistema
    transacoes = db.query(Transacao).all()

    # Verificar se existem transações
    if not transacoes:
        raise HTTPException(status_code=404, detail="Nenhuma transação encontrada.")
    
    return transacoes

# Rota para obter todas as transações de um usuário específico
@router.get("/{user_id}/transacoes/")
def listar_transacoes(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    # Verificar se o usuário existe
    usuario = db.query(Usuario).filter(Usuario.id ==  current_user.id).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    # Buscar todas as transações do usuário
    transacoes = db.query(Transacao).filter(Transacao.usuario_id == current_user.id).all()

    # Verificar se existem transações
    if not transacoes:
        raise HTTPException(status_code=404, detail="Nenhuma transação encontrada.")
    
    return transacoes    