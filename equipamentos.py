"""
equipamentos.py
---------------
Operações sobre os equipamentos de TI: cadastrar, buscar, atualizar, excluir.

Este módulo NÃO conversa com o usuário (nenhum input, e print só no bloco de
teste) e NÃO grava em disco. Ele recebe dados prontos, mexe no dicionário e
devolve resultado. Quem pergunta as coisas é o main.py; quem grava é o
arquivo.py.

Por que essa divisão?
Porque assim eu consigo testar estas funções sem ninguém digitando nada -
é o que faço no bloco de teste no fim do arquivo. Se houvesse input() aqui
dentro, todo teste exigiria uma pessoa na frente do teclado.

Atende aos requisitos 3, 4, 5 e 6.
"""

from arquivo import proximo_id_equipamento
import formatacao
import string


# Campos que o usuário pode alterar depois do cadastro.
# O identificador NÃO está aqui de propósito: se o id pudesse mudar, as
# vulnerabilidades que apontam para ele ficariam órfãs, apontando para um
# equipamento que não existe mais. Identificador é imutável por natureza.
CAMPOS_EDITAVEIS = ("hostname", "custodiante", "lotacao", "descricao", "categoria")


# ===========================================================================
# FORMATO DO HOSTNAME
#
# Hostname é o nome da máquina na rede, e a rede tem regras para ele. Estas
# vêm das normas que definem nome de máquina (RFC 952 e RFC 1123) e da
# documentação da Microsoft para redes Windows:
#
#   - só letras sem acento, números e hífen: nada de espaço, ponto, barra,
#     sublinhado ou acento;
#   - não começa nem termina com hífen;
#   - no máximo 63 caracteres, o limite de um nome no DNS;
#   - não pode ser só números: o Active Directory recusa, e um nome só de
#     dígitos se confunde com endereço IP.
#
# Ponto fica de fora porque o campo é o nome da máquina (PC-CARTORIO-01),
# não o endereço completo no domínio (pc-cartorio-01.delegacia.local).
#
# O Windows ainda corta o nome antigo de rede (NetBIOS) em 15 caracteres.
# Não imponho esse limite porque o inventário também tem roteador e
# servidor, que nem sempre são Windows.
# ===========================================================================
_CARACTERES_HOSTNAME = set(string.ascii_letters + string.digits + "-")


def problema_no_hostname(hostname):
    """
    Devolve None se o hostname é válido, ou uma frase dizendo o que está
    errado.

    Por que devolver a frase em vez de levantar erro? Porque o main.py usa
    esta função para perguntar de novo NA HORA em que o operador digita -
    sem obrigá-lo a preencher os outros campos para só então descobrir o
    problema. E cadastrar() e atualizar() usam a mesma função para recusar
    o dado de qualquer forma. A regra mora num lugar só.

    A ordem das checagens importa: os caracteres vêm antes do isdigit(),
    porque isdigit() aceita dígitos de outros alfabetos, como o "²".
    """
    h = hostname.strip()
    if not h:
        return "não pode ficar vazio"
    if len(h) > 63:
        return f"tem {len(h)} caracteres, o máximo é 63"
    invalidos = sorted(set(h) - _CARACTERES_HOSTNAME)
    if invalidos:
        mostrados = " ".join(repr(c) for c in invalidos)
        return (f"caractere(s) não permitido(s): {mostrados} - use apenas "
                f"letras sem acento, números e hífen")
    if h[0] == "-" or h[-1] == "-":
        return "não pode começar nem terminar com hífen"
    if h.isdigit():
        return "não pode ser composto só de números"
    return None


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


def _normalizar(campo, valor):
    """
    Aplica a formatação certa para cada campo.

    Existe para que cadastrar() e atualizar() não possam divergir: a regra
    está escrita num lugar só e as duas chamam esta função. Antes, cada uma
    fazia o seu próprio .strip() - e bastava eu mexer numa para as duas
    passarem a gravar diferente.
    """
    if campo == "hostname":
        # Nome de máquina em rede é convencionalmente em caixa alta, e assim
        # a listagem fica alinhada.
        return valor.strip().upper()
    if campo in ("custodiante", "lotacao"):
        return formatacao.titulo(valor)
    if campo == "descricao":
        return formatacao.frase(valor)
    return valor


# ===========================================================================
# REQUISITO 3 - cadastro
# ===========================================================================
def cadastrar(equipamentos, hostname, custodiante, lotacao, descricao, categoria):
    """
    Cria um equipamento e devolve o id gerado.
    Levanta ValueError se o hostname estiver fora do formato ou já em uso.

    Por que recusar hostname repetido? Porque hostname é nome de máquina na
    rede, e duas máquinas com o mesmo nome é um problema real de rede. O
    enunciado não exige essa checagem, mas ela faz o sistema representar o
    mundo corretamente - e é uma decisão que eu sei defender.
    """
    problema = problema_no_hostname(hostname)
    if problema:
        raise ValueError(f"Hostname inválido: {problema}")
    if _hostname_existe(equipamentos, hostname):
        raise ValueError(f"Já existe equipamento com o hostname '{hostname}'")

    id_novo = proximo_id_equipamento(equipamentos)
    equipamentos[id_novo] = {
        "hostname":    _normalizar("hostname", hostname),
        "custodiante": _normalizar("custodiante", custodiante),
        "lotacao":     _normalizar("lotacao", lotacao),
        "descricao":   _normalizar("descricao", descricao),
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
    Levanta ValueError num campo protegido ou num hostname inválido ou
    repetido - e aí nada muda, nem os outros campos pedidos.
    """
    registro = equipamentos.get(id_equipamento)
    if registro is None:
        return False

    # Dois laços de propósito: primeiro confiro TUDO, depois aplico. Num laço
    # só, um hostname recusado no meio deixaria os campos anteriores já
    # trocados - metade da alteração feita, sem ninguém pedir.
    for campo, valor in alteracoes.items():
        if campo not in CAMPOS_EDITAVEIS:
            raise ValueError(f"Campo não editável: '{campo}'")
        if campo == "hostname":
            problema = problema_no_hostname(valor)
            if problema:
                raise ValueError(f"Hostname inválido: {problema}")
            if _hostname_existe(equipamentos, valor, ignorar_id=id_equipamento):
                raise ValueError(f"Já existe equipamento com o hostname '{valor}'")

    for campo, valor in alteracoes.items():
        # Mesma normalização do cadastro, pela mesma função.
        registro[campo] = _normalizar(campo, valor)

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
    id1 = cadastrar(equipamentos, "PC-CARTORIO-01", "Escrivão de plantão",
                    "Cartório", "Estação de atendimento ao público",
                    CategoriaEquipamento.ESTACAO_TRABALHO)
    id2 = cadastrar(equipamentos, "SRV-ARQUIVO", "Chefe de equipe",
                    "Sala técnica", "Servidor de arquivos",
                    CategoriaEquipamento.SERVIDOR)
    print(f"Cadastrados os ids: {id1} e {id2}")

    try:
        cadastrar(equipamentos, "srv-arquivo", "X", "Y", "Z",
                  CategoriaEquipamento.SERVIDOR)
    except ValueError as erro:
        print(f"Duplicado recusado: {erro}")

    # --- Formato do hostname (RFC 1123) ---
    print()
    for ruim in ("pc cartorio", "pc/cartorio", "-pc", "pc-", "12345", "pcção"):
        try:
            cadastrar(equipamentos, ruim, "X", "Y", "Z",
                      CategoriaEquipamento.SERVIDOR)
            raise AssertionError(f"aceitou hostname inválido: {ruim!r}")
        except ValueError as erro:
            print(f"Recusado {ruim!r:15} {erro}")
    assert problema_no_hostname("10-ANDAR") is None, "recusou hostname válido"
    print("Aceito   '10-ANDAR'      começa com número, mas não é só número")

    # --- Requisito 4 ---
    print(f"\nBusca por id 2: {buscar_por_id(equipamentos, 2)['hostname']}")
    print(f"Busca por id 99: {buscar_por_id(equipamentos, 99)}  (None = não existe)")

    print("\nBusca parcial por 'cart':")
    for id_equipamento, registro in buscar_por_hostname(equipamentos, "cart"):
        print(f"  {id_equipamento} - {registro['hostname']}")

    # --- Requisito 5 ---
    atualizar(equipamentos, 1, {"custodiante": "Investigador de plantão"})
    print(f"\nApós atualizar: {equipamentos[1]['custodiante']}")

    try:
        atualizar(equipamentos, 1, {"id": 50})
    except ValueError as erro:
        print(f"Campo protegido: {erro}")

    # Tudo ou nada: o hostname repetido derruba a alteração inteira, e o
    # custodiante, que vinha antes no dicionário, também não pode mudar.
    try:
        atualizar(equipamentos, 1, {"custodiante": "Outro",
                                    "hostname": "srv-arquivo"})
    except ValueError as erro:
        print(f"Recusada inteira: {erro}")
    custodiante = equipamentos[1]["custodiante"]
    assert custodiante == "Investigador de plantão", "mudou pela metade"

    # --- Requisito 6 ---
    print(f"\nExcluindo id 2: {excluir(equipamentos, 2)}")
    print(f"Excluindo id 2 de novo: {excluir(equipamentos, 2)}  (False = já não existia)")
    print(f"Restaram os ids: {list(equipamentos.keys())}")

    print("\nOK - requisitos 3, 4, 5 e 6 exercitados.")
