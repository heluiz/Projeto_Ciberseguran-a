"""
equipamentos.py
---------------
Operações sobre os equipamentos de TI: cadastrar, buscar, atualizar, excluir.

Este módulo NÃO conversa com o usuário (nenhum input ou print) e NÃO grava em
disco. Ele recebe dados prontos, mexe no dicionário e devolve resultado.
Quem pergunta as coisas é o main.py; quem grava é o arquivo.py.

Por que essa divisão?
Porque assim eu consigo testar estas funções sem ninguém digitando nada -
é o que faço no bloco de teste no fim do arquivo. Se houvesse input() aqui
dentro, todo teste exigiria uma pessoa na frente do teclado.

Atende aos requisitos 3, 4, 5 e 6.
"""

from arquivo import proximo_id


# Campos que o usuário pode alterar depois do cadastro.
# O identificador NÃO está aqui de propósito: se o id pudesse mudar, as
# vulnerabilidades que apontam para ele ficariam órfãs, apontando para um
# equipamento que não existe mais. Identificador é imutável por natureza.
CAMPOS_EDITAVEIS = ("hostname", "custodiante", "lotacao", "descricao", "categoria")


def _hostname_existe(equipamentos, hostname, ignorar_id=None):
    """
    Função auxiliar. O underscore na frente é convenção em Python: significa
    "de uso interno deste módulo", não é para ser chamada de fora.

    ignorar_id serve para a atualização: ao renomear o equipamento 3, eu
    preciso ignorar o próprio 3 na checagem, senão ele acusaria conflito
    consigo mesmo.
    """
    alvo = hostname.strip().lower()
    for id_equipamento, registro in equipamentos.items():
        if id_equipamento == ignorar_id:
            continue
        if registro["hostname"].strip().lower() == alvo:
            return True
    return False


# ===========================================================================
# REQUISITO 3 - cadastro
# ===========================================================================
def cadastrar(equipamentos, hostname, custodiante, lotacao, descricao, categoria):
    """
    Cria um equipamento e devolve o id gerado.
    Levanta ValueError se o hostname já estiver em uso.

    Por que recusar hostname repetido? Porque hostname é nome de máquina na
    rede, e duas máquinas com o mesmo nome é um problema real de rede. O
    enunciado não exige essa checagem, mas ela faz o sistema representar o
    mundo corretamente - e é uma decisão que eu sei defender.
    """
    if _hostname_existe(equipamentos, hostname):
        raise ValueError(f"Ja existe equipamento com o hostname '{hostname}'")

    id_novo = proximo_id(equipamentos)
    equipamentos[id_novo] = {
        "hostname":    hostname.strip(),
        "custodiante": custodiante.strip(),
        "lotacao":     lotacao.strip(),
        "descricao":   descricao.strip(),
        "categoria":   categoria,
    }
    return id_novo


# ===========================================================================
# REQUISITO 4 - busca por identificador OU por hostname
# ===========================================================================
def buscar_por_id(equipamentos, id_equipamento):
    """
    Devolve o registro, ou None se não existir.

    Aqui está o motivo de usar dicionário (requisito 9): esta busca é direta,
    dá o mesmo trabalho com 10 ou com 10.000 equipamentos. Numa lista eu teria
    que percorrer item por item até achar.

    Uso .get() em vez de [ ] porque o colchete levantaria KeyError num id
    inexistente. Buscar algo que não existe não é um erro do programa - é uma
    resposta legítima, e quem decide o que fazer com ela é o menu.
    """
    return equipamentos.get(id_equipamento)


def buscar_por_hostname(equipamentos, termo):
    """
    Devolve uma LISTA de pares (id, registro).

    Por que lista, e não um resultado só? Porque a busca é parcial e ignora
    maiúsculas: digitar "cart" encontra "PC-CARTORIO-01". Isso pode casar com
    vários equipamentos, e na prática ninguém lembra o hostname inteiro.

    Esta busca percorre o dicionário inteiro, ao contrário da busca por id.
    É o preço de procurar por um campo que não é a chave.
    """
    termo = termo.strip().lower()
    encontrados = []
    for id_equipamento, registro in equipamentos.items():
        if termo in registro["hostname"].lower():
            encontrados.append((id_equipamento, registro))
    return encontrados


# ===========================================================================
# REQUISITO 5 - atualização
# ===========================================================================
def atualizar(equipamentos, id_equipamento, alteracoes):
    """
    'alteracoes' é um dicionário {campo: novo_valor}. Só os campos presentes
    mudam; o resto fica como estava.

    Devolve True se atualizou, False se o id não existe.
    Levanta ValueError se tentarem mexer num campo protegido.
    """
    registro = equipamentos.get(id_equipamento)
    if registro is None:
        return False

    for campo, valor in alteracoes.items():
        if campo not in CAMPOS_EDITAVEIS:
            raise ValueError(f"Campo nao editavel: '{campo}'")
        if campo == "hostname":
            if _hostname_existe(equipamentos, valor, ignorar_id=id_equipamento):
                raise ValueError(f"Ja existe equipamento com o hostname '{valor}'")
            valor = valor.strip()
        registro[campo] = valor

    return True


# ===========================================================================
# REQUISITO 6 - exclusão (a parte do equipamento)
# ===========================================================================
def excluir(equipamentos, id_equipamento):
    """
    Devolve True se excluiu, False se o id não existia.

    Este módulo NÃO apaga as vulnerabilidades associadas. Quem coordena a
    exclusão em cascata é o main.py, que chama falhas.excluir_por_equipamento()
    e só depois esta função.

    Por que assim? Porque cada módulo cuida só dos próprios dados. Se
    equipamentos.py mexesse nas falhas, os dois ficariam amarrados um ao outro
    e eu não conseguiria testar nenhum dos dois isoladamente - que é
    exatamente o que faço no bloco abaixo.
    """
    if id_equipamento not in equipamentos:
        return False
    del equipamentos[id_equipamento]
    return True


# ===========================================================================
# Teste: exercita os quatro requisitos sem ninguém digitar nada.
# ===========================================================================
if __name__ == "__main__":
    from classificacoes import CategoriaEquipamento

    equipamentos = {}

    # --- Requisito 3 ---
    id1 = cadastrar(equipamentos, "PC-CARTORIO-01", "Escrivao de plantao",
                    "Cartorio", "Estacao de atendimento ao publico",
                    CategoriaEquipamento.ESTACAO_TRABALHO)
    id2 = cadastrar(equipamentos, "SRV-ARQUIVO", "Chefe de equipe",
                    "Sala tecnica", "Servidor de arquivos",
                    CategoriaEquipamento.SERVIDOR)
    print(f"Cadastrados os ids: {id1} e {id2}")

    try:
        cadastrar(equipamentos, "srv-arquivo", "X", "Y", "Z",
                  CategoriaEquipamento.SERVIDOR)
    except ValueError as erro:
        print(f"Duplicado recusado: {erro}")

    # --- Requisito 4 ---
    print(f"\nBusca por id 2: {buscar_por_id(equipamentos, 2)['hostname']}")
    print(f"Busca por id 99: {buscar_por_id(equipamentos, 99)}  (None = nao existe)")

    print("\nBusca parcial por 'cart':")
    for id_equipamento, registro in buscar_por_hostname(equipamentos, "cart"):
        print(f"  {id_equipamento} - {registro['hostname']}")

    # --- Requisito 5 ---
    atualizar(equipamentos, 1, {"custodiante": "Investigador de plantao"})
    print(f"\nApos atualizar: {equipamentos[1]['custodiante']}")

    try:
        atualizar(equipamentos, 1, {"id": 50})
    except ValueError as erro:
        print(f"Campo protegido: {erro}")

    # --- Requisito 6 ---
    print(f"\nExcluindo id 2: {excluir(equipamentos, 2)}")
    print(f"Excluindo id 2 de novo: {excluir(equipamentos, 2)}  (False = ja nao existia)")
    print(f"Restaram os ids: {list(equipamentos.keys())}")

    print("\nOK - requisitos 3, 4, 5 e 6 exercitados.")