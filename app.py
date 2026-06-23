from flask import Flask, request, jsonify
import os
import re
from dotenv import load_dotenv
import mysql.connector
from twilio.rest import Client


load_dotenv()
      

app = Flask(__name__) 

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
        sql = "SELECT * FROM usuarios WHERE email = %s AND senha = %s"
        cursor.execute(sql, (dados['email'], dados['senha']))
        user = cursor.fetchone()
        if user:
            return jsonify({"mensagem": "Login realizado!", "usuario": user}), 200
        else:
            return jsonify({"mensagem": "Credenciais inválidas"}), 401
        
    except Exception as e:
        conn.rollback()
        print(f"Erro: {e}")
        return jsonify({"mensagem": "erro nos dados de login!"}), 500
    
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
            

if __name__ == '__main__':
    app.run(debug=True)