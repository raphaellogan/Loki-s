from flask import Flask, request, jsonify, send_from_directory, make_response, redirect
import os
import re
from dotenv import load_dotenv
import mysql.connector
from twilio.rest import Client
import secrets


load_dotenv()
      

app = Flask(__name__, static_folder="../frontend") 

db_config = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_DATABASE'),
    'user': os.getenv('DB_USER'), 
    'password': os.getenv('DB_PASSWORD') 
}


def get_db_connection(): 
    return mysql.connector.connect(**db_config)

# ---------------------------------------------------------
# FUNÇÃO AUXILIAR: Sanitização e Formatação E.164
# ---------------------------------------------------------
def formatar_para_twilio(telefone_raw):
    if not telefone_raw:
        return ""
    # Remove qualquer caractere que não seja número (parênteses, traços, espaços)
    numeros = re.sub(r'\D', '', str(telefone_raw))
    
    # Regra 1: Se tem 11 dígitos (DDD + 9 dígitos), assume Brasil e insere +55
    if len(numeros) == 10:
        return f"+55{numeros}"
    # Regra 2: Se já tem 13 dígitos (55 + DDD + número), adiciona apenas o +
    elif len(numeros) == 12:
        return f"+{numeros}"
    
    return numeros


class usuario:
    def __init__(
        self, nome, senha, cpf, setor, cargo, data_admissao, 
        telefone, email, perfil, status="ativo", created_at=None, id=None
    ):
        self.id = id
        self.nome = nome
        self.cpf = cpf
        self.telefone = telefone
        self.email = email
        self.senha = senha
        self.perfil = perfil
        self.setor = setor
        self.cargo = cargo
        self.data_admissao = data_admissao
        self.status = status
        self.created_at = created_at
        
    
class epi:
    # Corrigida a ordem dos parâmetros para bater com a criação do objeto
    def __init__(self, nome, codigo, categoria, fabricante, ca_certificado, validade_ca, estoque_id, created_at=None, status="ativo", id=None):
        self.id = id
        self.nome = nome
        self.codigo = codigo
        self.categoria = categoria
        self.fabricante = fabricante
        self.ca_certificado = ca_certificado
        self.validade_ca = validade_ca
        self.estoque_id = estoque_id
        self.status = status
        self.created_at = created_at
        
        
class entrega_epi:
    def __init__(self, usuario_id, epi_id, data_entrega, data_vencimento, assinatura, data_devolucao=None, observacao=None, created_at=None, id=None):
        self.id = id
        self.usuario_id = usuario_id
        self.epi_id = epi_id
        self.data_entrega = data_entrega
        self.data_devolucao = data_devolucao
        self.data_vencimento = data_vencimento
        self.assinatura = assinatura
        self.observacao = observacao
        self.created_at = created_at
      
        
class alerta:
    def __init__(self, usuario_id, epi_id, tipo, mensagem, created_at=None, visualizado="false", id=None):
        self.id = id
        self.usuario_id = usuario_id
        self.epi_id = epi_id
        self.tipo = tipo
        self.mensagem = mensagem
        self.created_at = created_at
        self.visualizado = visualizado

        
class estoque:
    def __init__(self, nome, categoria, descricao, quantidade_em_estoque=0, quantidade_emprestado=0, created_at=None, id=None):
        self.id = id
        self.nome = nome
        self.categoria = categoria
        self.descricao = descricao
        self.quantidade_em_estoque = quantidade_em_estoque
        self.quantidade_emprestado = quantidade_emprestado
        self.created_at = created_at


ROTAS_GUEST = {
    "login"
}

ROTAS_AUTH = {
    "admin/cadastro",
    "dashboard",
    "meus-epis",
    "solicitar-epi",
    "devolver-epi",
    "historico",
    "configuracoes",
    "grafico"
}


def auth():

    sessao = request.cookies.get("sessao")

    # O navegador não enviou o cookie
    if not sessao:
        return None

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        sql = """
            SELECT
                usuarios.id,
                usuarios.nome,
                usuarios.email
            FROM sessoes
            INNER JOIN usuarios
                ON usuarios.id = sessoes.usuario_id
            WHERE sessoes.sessao = %s
            LIMIT 1
        """

        cursor.execute(sql, (sessao,))

        usuario = cursor.fetchone()

        # A sessão não existe no banco
        if not usuario:
            return None

        return usuario

    except Exception as e:

        print(f"Erro na autenticação: {e}")

        return None

    finally:

        cursor.close()
        conn.close()


@app.route("/")
@app.route("/<path:path>")
def frontend(path=""):

    # 1. Acesso à raiz da aplicação (/)
    if path == "":
        return send_from_directory(app.static_folder, "index.html")

    caminho_fisico = os.path.join(app.static_folder, path)

    # 2. SE FOR UM ARQUIVO FÍSICO REAL (ex: CSS, JS, Imagens, ou .html via fetch)
    if os.path.isfile(caminho_fisico):

        # Permite carregar o HTML da página de login via fetch sem autenticação
        if path == "pages/login.html":
            return send_from_directory(app.static_folder, path)

        # Se for qualquer outro template dentro de pages/ requisitado via fetch
        if path.startswith("pages/"):
            usuario = auth()
            if not usuario:
                # NUNCA retorne redirect() para requisições fetch, retorne 401
                return jsonify({"mensagem": "Sessão expirada ou não autorizada"}), 401

        # Demais arquivos estáticos (CSS, JS, Imagens, etc)
        return send_from_directory(app.static_folder, path)

    # 3. SE FOR UMA ROTA VIRTUAL DO NAVEGADOR (ex: /login, /dashboard)
    usuario = auth()

    if not usuario:
        # Se NÃO está logado e tenta acessar algo que não é rota pública, vai pro /login
        if path not in ROTAS_GUEST:
            return redirect("/login")
    else:
        # Se JÁ ESTÁ logado e tenta acessar /login, envia pro /dashboard (evita o loop)
        if path in ROTAS_GUEST:
            return redirect("/dashboard")

        # Se a rota não existe no sistema
        if path not in ROTAS_AUTH:
            return send_from_directory(app.static_folder, "views/404.html"), 404

    # Para qualquer rota válida da SPA, entrega o index.html
    return send_from_directory(app.static_folder, "index.html")

@app.errorhandler(404)
def pagina_nao_encontrada(e):
    return send_from_directory(app.static_folder, "views/404.html"), 404


@app.route('/registrar', methods=['POST'])
def cadastrar_usuario():
    dados = request.get_json()
    user = usuario(
        nome=dados['nome'],
        senha=dados['senha'],
        cpf=dados['cpf'],
        setor=dados['setor'],
        cargo=dados['cargo'],
        data_admissao=dados['data_admissao'],
        telefone=dados['telefone'],
        email=dados['email'],
        perfil=dados['perfil']
    )
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = "INSERT INTO usuarios (nome, email, senha, cpf, telefone, setor, cargo, data_admissao, status, created_at, perfil) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'ativo', NOW(), %s)"
        cursor.execute(sql, (user.nome, user.email, user.senha, user.cpf, user.telefone, user.setor, user.cargo, user.data_admissao, user.perfil))
        conn.commit()
        return jsonify({"mensagem": "Funcionário cadastrado!"}), 201
    
    except Exception as e:
        conn.rollback()
        print(f"Erro: {e}")
        return jsonify({"mensagem": "erro ao tentar cadastrar funcionário"}), 500
    
    finally:
        cursor.close()
        conn.close()


@app.route('/apagar-conta', methods=['DELETE'])
def apagar_usuario():
    dados = request.get_json()
    user = dados['id']
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = "DELETE FROM usuarios WHERE id = %s"
        cursor.execute(sql, (user,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"mensagem": "Parece que essa conta não existe"}), 404
        return jsonify({"mensagem": "Funcionário excluído!"}), 201
    
    except Exception as e:
        conn.rollback()
        print(f"Erro: {e}")
        return jsonify({"mensagem": "erro ao tentar excluir funcionário"}), 500
    
    finally:
        cursor.close()
        conn.close()
    

@app.route('/criar-estoque', methods=['POST'])
def criar_estoque():
    dados = request.get_json()
    novo_estoque = estoque(dados['nome'], dados['categoria'], dados['descricao'])
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = "INSERT INTO estoques (nome, categoria, descricao, quantidade_em_estoque, quantidade_emprestado) VALUES (%s, %s, %s, 0, 0)"
        cursor.execute(sql, (novo_estoque.nome, novo_estoque.categoria, novo_estoque.descricao))
        conn.commit()
        return jsonify({"mensagem": "Estoque criado!"}), 201

    except Exception as e:
        conn.rollback()
        print(f"Erro: {e}")
        return jsonify({"mensagem": "erro ao tentar criar estoque"}), 500
    
    finally:
        cursor.close()
        conn.close()
    


@app.route('/cadastrar-epi', methods=['POST'])
def cadastrar_epi():
    dados = request.get_json()
    # Ordem dos parâmetros corrigida para bater com o __init__ da classe epi
    novo_epi = epi(
        dados['nome'], 
        dados['codigo'], 
        dados['categoria'], 
        dados['fabricante'], 
        dados['ca_certificado'], 
        dados['validade_ca'], 
        dados['estoque_id']
    )
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql_epi = "INSERT INTO epis (nome, codigo, categoria, fabricante, ca_certificado, validade_ca, estoque_id, status, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, 'ativo', NOW());"
        sql_estoque = "UPDATE estoques SET quantidade_em_estoque = quantidade_em_estoque + 1 WHERE id = %s;"
        cursor.execute(sql_epi, (novo_epi.nome, novo_epi.codigo, novo_epi.categoria, novo_epi.fabricante, novo_epi.ca_certificado, novo_epi.validade_ca, novo_epi.estoque_id))
        cursor.execute(sql_estoque, (novo_epi.estoque_id,)) # Adicionada a vírgula necessária para tupla de 1 item
        conn.commit()
        return jsonify({"mensagem": "EPI cadastrado!"}), 201

    except Exception as e:
        conn.rollback()
        print(f"Erro: {e}")
        return jsonify({"mensagem": "erro ao tentar cadastrar o EPI"}), 500
    
    finally:
        cursor.close()
        conn.close()
    

@app.route('/login', methods=['POST'])
def login():
    dados = request.get_json()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        sql = """
            SELECT *
            FROM usuarios
            WHERE email = %s
            AND senha = %s
        """

        cursor.execute(sql, (
            dados['email'],
            dados['senha']
        ))

        user = cursor.fetchone()

        if user:
            # Gera uma sessão aleatória com 16 caracteres
            sessao = secrets.token_hex(8)

            # Exclui uma sessão antiga desse usuário
            cursor.execute(
                """
                DELETE FROM sessoes
                WHERE usuario_id = %s
                """,
                (user['id'],)
            )

            # Salva a nova sessão relacionada ao usuário
            cursor.execute(
                """
                INSERT INTO sessoes (
                    sessao,
                    usuario_id
                )
                VALUES (%s, %s)
                """,
                (
                    sessao,
                    user['id']
                )
            )

            conn.commit()

            # Evite devolver a senha no JSON
            user.pop('senha', None)

            resposta = make_response(
                jsonify({
                    "mensagem": "Login realizado!",
                    "usuario": user
                }),
                200
            )

            # Envia o cookie para o computador que fez o login
            resposta.set_cookie(
                key='sessao',
                value=sessao,
                httponly=True,
                secure=False,
                samesite='Lax',
                max_age=60 * 60 * 24 * 30
            )

            return resposta

        else:
            return jsonify({
                "mensagem": "Credenciais inválidas"
            }), 401

    except Exception as e:
        conn.rollback()
        print(f"Erro: {e}")

        return jsonify({
            "mensagem": "Erro nos dados de login!"
        }), 500

    finally:
        cursor.close()
        conn.close()  


@app.route('/entregar-epi', methods=['POST'])
def entregar_epi():
    dados = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql_epi = """
            INSERT INTO entregas_epis 
            (usuario_id, epi_id, data_entrega, observacao, data_devolucao, data_vencimento, assinatura, created_at)
            VALUES (%s, %s, NOW(), %s, NULL, %s, %s, NOW())
        """
        sql_estoque = """
            UPDATE estoques SET quantidade_emprestado = quantidade_emprestado + 1 WHERE id = %s
        """
        cursor.execute(sql_epi, (
            dados['usuario_id'],
            dados['epi_id'],
            dados.get('observacao', ''),
            dados['data_vencimento'],
            dados['assinatura']
        ))
        cursor.execute(sql_estoque, (dados['estoque_id'],)) # Adicionada a vírgula para corrigir a tupla
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"mensagem": "Nenhum registro encontrado"}), 404
        return jsonify({"mensagem": "EPI entregue com sucesso!"}), 201
    
    except Exception as e:
        conn.rollback()
        print(f"Erro: {e}")
        return jsonify({"mensagem": "erro ao tentar registrar entrega de EPI"}), 500
    
    finally:
        cursor.close()
        conn.close()


@app.route('/devolver-epi', methods=['POST'])
def devolver_epi():
    dados = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql_epi = """
            UPDATE entregas_epis
            SET data_devolucao = NOW()
            WHERE id = %s
        """
        sql_estoque = """
            UPDATE estoques SET quantidade_emprestado = quantidade_emprestado - 1 WHERE id = %s
        """
        cursor.execute(sql_epi, (dados['entrega_id'],))
        cursor.execute(sql_estoque, (dados['estoque_id'],)) # Adicionada a vírgula para corrigir a tupla e removido o ';' interno incorreto
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"mensagem": "Nenhum epi para ser devolvido"}), 404
        return jsonify({"mensagem": "EPI devolvido!"}), 200
    
    except Exception as e:
        conn.rollback()
        print(f"Erro: {e}")
        return jsonify({"mensagem": "erro ao tentar registrar o devolvimento do EPI"}), 500

    finally:
        cursor.close()
        conn.close()


@app.route('/alerta-visualizado', methods=['POST'])
def alerta_visualizado():
    dados = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = """
            UPDATE alertas
            SET visualizado = 'true'
            WHERE id = %s
        """
        cursor.execute(sql, (dados['alerta_id'],))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"mensagem": "Nenhum alerta encontrado"}), 404
        return jsonify({"mensagem": "Alerta visualizado."}), 200

    except Exception as e:
        conn.rollback()
        print(f"Erro: {e}")
        return jsonify({"mensagem": "falha tentar registrar a visualização da mensagem"}), 500
    
    finally:
        cursor.close()
        conn.close()
        


@app.route('/alterar-senha', methods=['POST'])
def alterar_senha():
    dados = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = """
            UPDATE usuarios
            SET senha = %s
            WHERE id = %s
        """
        cursor.execute(sql, (dados['nova_senha'], dados['usuario_id']))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"mensagem": "Nenhum registro encontrado"}), 404
        return jsonify({"mensagem": "Senha alterada com sucesso!"}), 200

    except Exception as e:
        conn.rollback()
        print(f"Erro: {e}")
        return jsonify({"mensagem": "falha ao tentar alterar a senha"}), 500
    
    finally:
        cursor.close()
        conn.close()
    

#   Provavelmente essa rota não será usada

# @app.route('/ajustar-estoque-epi', methods=['POST'])
# def ajustar_estoque_epi():
#     dados = request.get_json()
#     conn = get_db_connection()
#     cursor = conn.cursor()

#     # Corrigido: Atualiza a tabela 'estoques' (onde de fato fica a quantidade) em vez de 'epis'
#     sql = """
#         UPDATE estoques
#         SET quantidade_em_estoque = quantidade_em_estoque + %s
#         WHERE id = %s
#     """
#     cursor.execute(sql, (dados['ajuste'], dados['estoque_id']))

#     conn.commit()
#     cursor.close()
#     conn.close()

#     return jsonify({"mensagem": "Estoque ajustado!"}), 200

@app.route('/epis-pendentes', methods=['GET'])
def listar_epis_pendentes():
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        sql = """
            SELECT *
            FROM entregas_epis
            WHERE data_devolucao IS NULL
        """

        cursor.execute(sql)
        resultados = cursor.fetchall()
        if cursor.rowcount == 0:
            return jsonify({"mensagem": "Nenhum registro encontrado"}), 404

        return jsonify({
            "total": len(resultados),
            "dados": resultados
        }), 200

    except Exception as e:
        print(f"Erro ao listar EPIs pendentes: {str(e)}")
        return jsonify({"erro": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# =========================================================
# ROTA AUTOMATIZADA: NOTIFICAÇÕES (SMS + WHATSAPP)
# =========================================================

@app.route('/api/notificar-vencimentos', methods=['POST'])
def notificar_vencimentos():
    conn = None
    cursor = None

    try:
        # Inicializa Twilio client uma única vez (melhor performance)
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        sms_from = os.getenv('TWILIO_PHONE_NUMBER')
        whatsapp_from = os.getenv('TWILIO_WHATSAPP_NUMBER')

        client = Client(account_sid, auth_token)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        sql = """
            SELECT F.nome, F.telefone, R.data_vencimento 
            FROM entregas_epis R
            JOIN usuarios F ON F.id = R.usuario_id
            WHERE DATE(R.data_vencimento) 
            BETWEEN CURDATE() 
            AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        """
        cursor.execute(sql)
        vencendo = cursor.fetchall()
        if cursor.rowcount == 0:
            return jsonify({"mensagem": "Nenhum registro encontrado"}), 404

        contador_sucesso = 0

        for reg in vencendo:
            try:
                telefone_limpo = formatar_para_twilio(reg['telefone'])

                # validação mais correta (E.164)
                if not telefone_limpo or not telefone_limpo.startswith("+"):
                    print(f"Aviso: {reg['nome']} ignorado (telefone inválido)")
                    continue

                mensagem = (
                    f"Olá {reg['nome']}, seu EPI vence em breve no dia "
                    f"{reg['data_vencimento']}."
                )

                # WhatsApp (sandbox ou número habilitado)
                client.messages.create(
                    body=mensagem,
                    from_=f"whatsapp:{whatsapp_from}",
                    to=f"whatsapp:{telefone_limpo}"
                )

                contador_sucesso += 1

            except Exception as e:
                print(f"Erro ao enviar para {reg['nome']}: {str(e)}")
                continue

        return jsonify({
            "mensagem": f"Processamento concluído. {contador_sucesso} colaboradores notificados!"
        }), 200

    except Exception as e:
        print(f"Erro crítico no processamento das notificações: {str(e)}")
        return jsonify({"erro": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@app.route("/almoxarife/dashboard/dados", methods=["GET"])
def almoxarife_dashboard():

    usuario = auth()

    if not usuario:
        return redirect("/login")

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Primeira consulta: todas as contagens
        cursor.execute("""
            SELECT
                (
                    SELECT COUNT(*)
                    FROM usuarios
                ) AS quantidade_funcionarios,

                (
                    SELECT COUNT(*)
                    FROM epis
                ) AS quantidade_epis,

                (
                    SELECT COUNT(*)
                    FROM entregas_epis
                    WHERE data_devolucao IS NULL
                ) AS quantidade_epis_emprestados,

                (
                    SELECT COUNT(*)
                    FROM estoques
                    WHERE quantidade_em_estoque < 20
                ) AS quantidade_estoques_baixos,

                (
                    SELECT COUNT(*)
                    FROM entregas_epis
                    WHERE data_vencimento BETWEEN
                        CURDATE()
                        AND DATE_ADD(
                            CURDATE(),
                            INTERVAL 6 DAY
                        )
                    AND data_devolucao IS NULL
                ) AS quantidade_vencimentos_proximos,

                (
                    SELECT COUNT(*)
                    FROM entregas_epis
                    WHERE data_entrega IS NULL
                ) AS quantidade_entregas_pendentes
        """)

        quantidades = cursor.fetchone()

        # Segunda consulta: três entregas recentes
        cursor.execute("""
            SELECT *
            FROM entregas_epis
            WHERE data_devolucao IS NULL
            ORDER BY data_entrega DESC
            LIMIT 3
        """)

        entregas_recentes = cursor.fetchall()

        # Junta os registros recentes ao dicionário
        quantidades["entregas_recentes"] = entregas_recentes

        return jsonify(quantidades), 200

    except Exception as e:
        print(f"Erro ao carregar dashboard: {e}")

        return jsonify({
            "mensagem": "Erro ao carregar os dados do dashboard"
        }), 500

    finally:
        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


@app.route("/almoxarife/funcionarios/dados", methods=["GET"])
def dados_funcionarios_almoxarife():

    usuario = auth()

    if not usuario:
        return redirect("/login")

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # =====================================================
        # 1. CONTAGENS GERAIS
        # =====================================================

        cursor.execute("""
            SELECT

                /* Usuários com pelo menos um EPI atrasado */
                (
                    SELECT COUNT(DISTINCT usuario_id)
                    FROM entregas_epis
                    WHERE data_entrega IS NOT NULL
                      AND data_devolucao IS NULL
                      AND data_vencimento < CURDATE()
                ) AS quantidade_usuarios_devendo_epis,

                /* Trocas previstas entre hoje e os próximos 6 dias */
                (
                    SELECT COUNT(*)
                    FROM entregas_epis
                    WHERE data_entrega IS NOT NULL
                      AND data_devolucao IS NULL
                      AND data_vencimento BETWEEN
                          CURDATE()
                          AND DATE_ADD(
                              CURDATE(),
                              INTERVAL 6 DAY
                          )
                ) AS quantidade_trocas_proximas,

                /* Usuários que não possuem EPI ativo */
                (
                    SELECT COUNT(*)
                    FROM usuarios AS u
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM entregas_epis AS entrega
                        WHERE entrega.usuario_id = u.id
                          AND entrega.data_entrega IS NOT NULL
                          AND entrega.data_devolucao IS NULL
                    )
                ) AS quantidade_usuarios_sem_epis,

                /* Entregas ativas e dentro do prazo */
                (
                    SELECT COUNT(*)
                    FROM entregas_epis
                    WHERE data_entrega IS NOT NULL
                      AND data_devolucao IS NULL
                      AND data_vencimento >= CURDATE()
                ) AS quantidade_entregas_regularizadas,

                /* EPIs vencidos que ainda nem foram entregues */
                (
                    SELECT COUNT(*)
                    FROM entregas_epis
                    WHERE data_entrega IS NULL
                      AND data_vencimento < CURDATE()
                ) AS quantidade_epis_vencidos_nao_entregues,

                /* EPIs entregues próximos da troca ou vencimento */
                (
                    SELECT COUNT(*)
                    FROM entregas_epis
                    WHERE data_entrega IS NOT NULL
                      AND data_devolucao IS NULL
                      AND data_vencimento BETWEEN
                          CURDATE()
                          AND DATE_ADD(
                              CURDATE(),
                              INTERVAL 6 DAY
                          )
                ) AS quantidade_epis_proximos_troca_vencimento,

                /* Funcionários cadastrados nos últimos 30 dias */
                (
                    SELECT COUNT(*)
                    FROM usuarios
                    WHERE created_at >= DATE_SUB(
                        NOW(),
                        INTERVAL 30 DAY
                    )
                ) AS quantidade_funcionarios_novos,

                /* Quantidade total de funcionários */
                (
                    SELECT COUNT(*)
                    FROM usuarios
                ) AS quantidade_total_funcionarios,

                /* Quantidade de EPIs ativos */
                (
                    SELECT COUNT(*)
                    FROM epis
                    WHERE status = 'ativo'
                ) AS quantidade_epis_ativos,

                /* Trocas previstas para hoje ou amanhã */
                (
                    SELECT COUNT(*)
                    FROM entregas_epis
                    WHERE data_entrega IS NOT NULL
                      AND data_devolucao IS NULL
                      AND data_vencimento BETWEEN
                          CURDATE()
                          AND DATE_ADD(
                              CURDATE(),
                              INTERVAL 1 DAY
                          )
                ) AS quantidade_trocas_proximo_dia
        """)

        quantidades = cursor.fetchone()

        # =====================================================
        # 2. TRÊS DEVOLUÇÕES MAIS PRÓXIMAS
        # =====================================================

        cursor.execute("""
            SELECT
                entrega.id,
                entrega.usuario_id,
                entrega.epi_id,
                entrega.data_entrega,
                entrega.data_devolucao,
                entrega.data_vencimento,
                entrega.assinatura,
                entrega.observacao,
                entrega.created_at
            FROM entregas_epis AS entrega
            WHERE entrega.data_entrega IS NOT NULL
              AND entrega.data_devolucao IS NULL
              AND entrega.data_vencimento >= CURDATE()
            ORDER BY entrega.data_vencimento ASC
            LIMIT 3
        """)

        devolucoes_proximas = cursor.fetchall()

        # =====================================================
        # 3. DOIS USUÁRIOS DE SETORES QUE PRECISAM DE EPI,
        #    MAS NÃO POSSUEM EPI ATIVO
        # =====================================================

        cursor.execute("""
            SELECT
                u.id,
                u.nome,
                u.email,
                u.cpf,
                u.telefone,
                u.setor,
                u.cargo,
                u.data_admissao,
                u.perfil,
                u.status,
                u.created_at
            FROM usuarios AS u
            WHERE u.setor IN (
                'Produção',
                'Manutenção',
                'Elétrica',
                'Construção',
                'Almoxarifado'
            )
              AND u.status = 'ativo'
              AND NOT EXISTS (
                  SELECT 1
                  FROM entregas_epis AS entrega
                  WHERE entrega.usuario_id = u.id
                    AND entrega.data_entrega IS NOT NULL
                    AND entrega.data_devolucao IS NULL
              )
            ORDER BY u.created_at ASC
            LIMIT 2
        """)

        usuarios_sem_epis = cursor.fetchall()

        # Adiciona as duas listas ao dicionário das contagens
        quantidades["devolucoes_proximas"] = (
            devolucoes_proximas
        )

        quantidades["usuarios_de_setores_sem_epis"] = (
            usuarios_sem_epis
        )

        return jsonify(quantidades), 200

    except Exception as e:
        print(
            f"Erro ao buscar dados dos funcionários: {e}"
        )

        return jsonify({
            "mensagem": "Erro ao buscar dados dos funcionários"
        }), 500

    finally:
        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


@app.route(
    "/almoxarife/funcionarios-completo/dados",
    methods=["GET"]
)
def listar_funcionarios_completo():

    usuario = auth()

    if not usuario:
        return jsonify({
            "mensagem": "Usuário não autenticado"
        }), 401

# Arrumar essa parte depois!!!!!!!!!!!!!!!!!!!!! erro de key perfil !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # if usuario["perfil"] not in ["almoxarife", "admin"]:
    #     return jsonify({
    #         "mensagem": "Acesso negado"
    #     }), 403

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                u.id,
                u.nome,
                u.email,
                u.perfil,
                u.status,
                u.created_at,
                u.cpf,
                u.setor,
                u.cargo,
                u.data_admissao,
                u.telefone,

                /* Quantidade de EPIs atualmente com o usuário */
                COUNT(
                    CASE
                        WHEN entrega.data_entrega IS NOT NULL
                         AND entrega.data_devolucao IS NULL
                        THEN 1
                    END
                ) AS quantidade_epis,

                /* Possui entrega ainda não realizada */
                CASE
                    WHEN COUNT(
                        CASE
                            WHEN entrega.data_entrega IS NULL
                            THEN 1
                        END
                    ) > 0
                    THEN TRUE
                    ELSE FALSE
                END AS tem_entregas_pendentes,

                /* Possui troca entre hoje e os próximos 6 dias */
                CASE
                    WHEN COUNT(
                        CASE
                            WHEN entrega.data_entrega IS NOT NULL
                             AND entrega.data_devolucao IS NULL
                             AND entrega.data_vencimento BETWEEN
                                 CURDATE()
                                 AND DATE_ADD(
                                     CURDATE(),
                                     INTERVAL 6 DAY
                                 )
                            THEN 1
                        END
                    ) > 0
                    THEN TRUE
                    ELSE FALSE
                END AS tem_trocas_proximas,

                /* Quantidade de trocas próximas */
                COUNT(
                    CASE
                        WHEN entrega.data_entrega IS NOT NULL
                         AND entrega.data_devolucao IS NULL
                         AND entrega.data_vencimento BETWEEN
                             CURDATE()
                             AND DATE_ADD(
                                 CURDATE(),
                                 INTERVAL 6 DAY
                             )
                        THEN 1
                    END
                ) AS quantidade_trocas_proximas,

                /* Situação geral das entregas do usuário */
                CASE
                    WHEN COUNT(
                        CASE
                            WHEN entrega.data_devolucao IS NULL
                             AND (
                                 entrega.data_entrega IS NULL
                                 OR entrega.data_vencimento < CURDATE()
                             )
                            THEN 1
                        END
                    ) > 0
                    THEN 'irregular'

                    ELSE 'regular'
                END AS status_entregas

            FROM usuarios AS u

            LEFT JOIN entregas_epis AS entrega
                ON entrega.usuario_id = u.id

            GROUP BY
                u.id,
                u.nome,
                u.email,
                u.perfil,
                u.status,
                u.created_at,
                u.cpf,
                u.setor,
                u.cargo,
                u.data_admissao,
                u.telefone

            ORDER BY u.nome ASC
        """)

        funcionarios = cursor.fetchall()

        # MySQL pode devolver TRUE e FALSE como 1 e 0.
        # Esta conversão garante booleanos no JSON.
        for funcionario in funcionarios:
            funcionario["tem_entregas_pendentes"] = bool(
                funcionario["tem_entregas_pendentes"]
            )

            funcionario["tem_trocas_proximas"] = bool(
                funcionario["tem_trocas_proximas"]
            )

        return jsonify({
            "quantidade": len(funcionarios),
            "funcionarios": funcionarios
        }), 200

    except Exception as e:
        print(f"Erro ao listar funcionários: {e}")

        return jsonify({
            "mensagem": "Erro ao listar funcionários"
        }), 500

    finally:
        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


@app.route(
    "/almoxarife/epis/dados",
    methods=["GET"]
)
def dados_epis_almoxarife():

    usuario = auth()

    if not usuario:
        return redirect("/login")

    # if usuario["perfil"] not in ["almoxarife", "admin"]:
    #     return jsonify({
    #         "mensagem": "Acesso negado"
    #     }), 403

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Todas as quantidades
        cursor.execute("""
            SELECT

                /* Quantidade total de EPIs cadastrados */
                (
                    SELECT COUNT(*)
                    FROM epis
                ) AS quantidade_epis_cadastrados,

                /* EPIs atualmente emprestados */
                (
                    SELECT COUNT(*)
                    FROM entregas_epis
                    WHERE data_entrega IS NOT NULL
                      AND data_devolucao IS NULL
                ) AS quantidade_epis_emprestados,

                /* EPIs inativos, danificados ou indisponíveis */
                (
                    SELECT COUNT(*)
                    FROM epis
                    WHERE status = 'inativo'
                ) AS quantidade_epis_inativos,

                /* EPIs ativos */
                (
                    SELECT COUNT(*)
                    FROM epis
                    WHERE status = 'ativo'
                ) AS quantidade_epis_ativos,

                /* Quantidade disponível somada dos estoques */
                (
                    SELECT COALESCE(
                        SUM(quantidade_em_estoque),
                        0
                    )
                    FROM estoques
                ) AS quantidade_total_em_estoque
        """)

        dados = cursor.fetchone()

        # Dados completos de todos os estoques
        cursor.execute("""
            SELECT
                id,
                nome,
                categoria,
                descricao,
                quantidade_em_estoque,
                quantidade_emprestado
            FROM estoques
            ORDER BY nome ASC
        """)

        estoques = cursor.fetchall()

        dados["quantidade_estoques"] = len(estoques)
        dados["estoques"] = estoques

        return jsonify(dados), 200

    except Exception as e:
        print(f"Erro ao buscar dados dos EPIs: {e}")

        return jsonify({
            "mensagem": "Erro ao buscar dados dos EPIs"
        }), 500

    finally:
        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


@app.route(
    "/almoxarife/cadastrar-epi/dados",
    methods=["GET"]
)
def buscar_proximo_codigo_epi():

    usuario = auth()

    if not usuario:
        return redirect("/login")

    # if usuario["perfil"] not in ["almoxarife", "admin"]:
    #     return jsonify({
    #         "mensagem": "Acesso negado"
    #     }), 403

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                COALESCE(
                    MAX(
                        CAST(
                            SUBSTRING(codigo, 5)
                            AS UNSIGNED
                        )
                    ),
                    0
                ) + 1 AS proximo_codigo
            FROM epis
            WHERE codigo REGEXP '^EPI-[0-9]+$'
        """)

        resultado = cursor.fetchone()

        # Retorna somente o número
        proximo_codigo = int(resultado["proximo_codigo"])
        return jsonify(proximo_codigo), 200

    except Exception as e:
        print(f"Erro ao buscar próximo código: {e}")

        return jsonify({
            "mensagem": "Erro ao buscar o próximo código de EPI"
        }), 500

    finally:
        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
        )