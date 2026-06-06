"""
=============================================================================
SISTEMA DE GESTÃO DE TREINAMENTOS - SST 4.0
Módulo: Lógica de Negócio e POO (Pré-Banco de Dados)
Objetivo: Revisar manipulação de Dicionários, Arrays (Listas), Laços e Classes.
=============================================================================
"""
#Direferença entre Classe Modelo e Classe Controladora:
# - A CLASSE MODELO é a estrutura que representa os dados (como um molde).
# - A CLASSE CONTROLADORA é a estrutura que gerencia os dados (como um gerente de banco de dados).

#diferença entre objeto, atributo e método:
# - OBJETO: É uma instância de uma classe, ou seja, é um "exemplar" criado a partir do molde da classe. Ele possui suas próprias características e comportamentos.Exemplo: "João Silva" é um objeto da classe "Treinamento".

# - ATRIBUTO: São as características ou propriedades de um objeto. Eles armazenam informações sobre o objeto. Por exemplo, em um objeto "Carro", os atributos podem ser "cor", "modelo" e "ano".Exemplo: "curso" é um atributo do objeto "João Silva" que pode ter o valor "NR-35 (Trabalho em Altura)".

# - MÉTODO: São as ações ou comportamentos que um objeto pode realizar. Eles são definidos dentro da classe e podem manipular os atributos do objeto. Por exemplo, um método "acelerar" em um objeto "Carro" pode aumentar a velocidade do carro.

# ===========================================================================
# 1. A CLASSE MODELO (Representa uma linha na futura tabela do MySQL)
# ===========================================================================

from datetime import datetime, timedelta # Importando as bibliotecas para manipulação de datas. datetime é usada para representar datas e horas, enquanto timedelta é usada para realizar operações de adição ou subtração de tempo.


class Treinamento:
    def __init__(self, matricula, nome, curso, data_realizacao, validade_meses):
        # Atributos do objeto
        self.matricula = matricula
        self.nome = nome
        self.curso = curso
        self.validade_meses = validade_meses
        
        # Converte a data de texto para formato de data real
        self.data_realizacao = datetime.strptime(data_realizacao, "%Y-%m-%d") # Formato: Ano-Mês-Dia (Padrão ISO). A função strptime é usada para converter uma string de data em um objeto datetime. O formato "%Y-%m-%d" indica que a string está no formato "Ano-Mês-Dia".

    # Função interna para calcular a data de vencimento
    def calcular_vencimento(self):
        dias_validade = self.validade_meses * 30 # Aproximação: 1 mês = 30 dias
        return self.data_realizacao + timedelta(days=dias_validade)

    # Função interna para definir o status (Semaforização)
    def verificar_status(self):
        vencimento = self.calcular_vencimento()
        hoje = datetime.now() # Obtém a data e hora atual. A função datetime.now() retorna um objeto datetime representando a data e hora atuais do sistema. Isso é útil para comparar com a data de vencimento e determinar o status do treinamento.
        
        if hoje > vencimento: # Verifica se já está vencido. A comparação hoje > vencimento verifica se a data atual (hoje) é posterior à data de vencimento. Se for, significa que o treinamento já passou da data de validade, e portanto, está vencido.
            return "🔴 VENCIDO"
        elif hoje >= (vencimento - timedelta(days=30)): # Verifica se está vencendo em 30 dias ou menos. A função timedelta(days=30) é usada para criar um objeto timedelta que representa um período de 30 dias. Subtraindo esse período da data de vencimento, podemos verificar se a data atual (hoje) está dentro desse intervalo, indicando que o treinamento está prestes a vencer.
            return "🟡 VENCE EM 30 DIAS" 
        else: # Se não estiver vencido e nem próximo do vencimento, está em dia. Se a data atual (hoje) não for posterior à data de vencimento e também não estiver dentro dos 30 dias anteriores ao vencimento, então o treinamento está considerado "em dia", ou seja, ainda é válido por um período mais longo.
            return "🟢 EM DIA"

    # Função que converte o Objeto de volta para Dicionário (Preparação para o JSON/Flask)
    def converter_para_dicionario(self): # Esta função é responsável por converter os atributos do objeto Treinamento em um formato de dicionário. Isso é útil para preparar os dados para serem enviados como resposta em uma API, onde o formato JSON é comumente utilizado. O método converter_para_dicionario() retorna um dicionário contendo as informações relevantes do treinamento, incluindo a matrícula, nome, curso, data de vencimento formatada e status.
        return {
            "matricula": self.matricula,
            "nome": self.nome,
            "curso": self.curso,
            "vencimento": self.calcular_vencimento().strftime("%d/%m/%Y"),
            "status": self.verificar_status()
        }


# ===========================================================================
# 2. A CLASSE CONTROLADORA (Simula o Banco de Dados e as Rotas)
# ===========================================================================
class GerenciadorSST:
    def __init__(self):
        # Array (Lista) que atua como o nosso banco de dados provisório
        self.banco_de_memoria = []

    # Equivalente ao comando INSERT INTO no banco de dados
    def inserir_registro(self, novo_treinamento):
        self.banco_de_memoria.append(novo_treinamento)
        print(f"[Sucesso] Treinamento de {novo_treinamento.nome} ({novo_treinamento.curso}) registrado!")

    # Equivalente ao comando SELECT no banco de dados
    def listar_todos(self):
        print("\n" + "="*60)
        print("📊 PAINEL DE CONFORMIDADE - TREINAMENTOS SST")
        print("="*60)
        
        # Laço de repetição percorrendo o Array
        for treinamento in self.banco_de_memoria:
            dicionario = treinamento.converter_para_dicionario()
            
            print(f"Matrícula : {dicionario['matricula']} | {dicionario['nome']}")
            print(f"Curso     : {dicionario['curso']}")
            print(f"Vencimento: {dicionario['vencimento']}")
            print(f"Status    : {dicionario['status']}")
            print("-" * 60)


# ===========================================================================
# 3. EXECUÇÃO NA PRÁTICA (A rotina de testes do laboratório)
# ===========================================================================

# Instanciamos o "Banco de Dados"
sistema_sst = GerenciadorSST()

print("Iniciando sistema SST 4.0...\n")

# Criamos os Objetos (Mockando os dados)
treinamento_1 = Treinamento(
    matricula="MAT-001", 
    nome="João Silva", 
    curso="NR-35 (Trabalho em Altura)", 
    data_realizacao="2025-01-15", 
    validade_meses=24
)

treinamento_2 = Treinamento(
    matricula="MAT-002", 
    nome="Maria Oliveira", 
    curso="NR-33 (Espaço Confinado)", 
    data_realizacao="2024-04-10", 
    validade_meses=12 # Vencido de propósito para teste
)

treinamento_3 = Treinamento(
    matricula="MAT-003", 
    nome="Carlos Souza", 
    curso="NR-10 (Elétrica)", 
    data_realizacao="2025-05-20", # Configurado para vencer próximo (Mude o ano se necessário)
    validade_meses=12
)

# Simulamos a inserção no banco (O futuro POST da API)
sistema_sst.inserir_registro(treinamento_1)
sistema_sst.inserir_registro(treinamento_2)
sistema_sst.inserir_registro(treinamento_3)

# Simulamos a consulta e impressão do relatório (O futuro GET da API)
sistema_sst.listar_todos()