"""Operações sobre os ativos: cadastrar, buscar, atualizar e excluir.

O módulo não lê do teclado nem grava em disco: recebe os dados do
main.py e devolve o resultado, o que permite testá-lo sozinho.
Atende aos requisitos 3, 4, 5 e 6.
"""

import string

import formatacao
from arquivo import proximo_id_ativo

# O id fica de fora: mudá-lo deixaria órfãs as falhas do ativo.
CAMPOS_EDITAVEIS = ("hostname", "custodiante", "lotacao", "descricao",
                    "categoria")

# Regras de nome de máquina (RFC 952 e RFC 1123): letras sem acento,
# dígitos e hífen, sem hífen nas pontas, até 63 caracteres e não só
# dígitos. Ponto fica de fora porque o campo é o nome da máquina, não
# o nome completo no domínio.
_CARACTERES_HOSTNAME = set(string.ascii_letters + string.digits + "-")


def problema_no_hostname(hostname, ativos=None, ignorar_id=None):
    """Devolve None se o hostname é válido, ou o motivo da recusa.

    Com ativos, também recusa hostname já usado por outro ativo;
    ignorar_id tira o próprio ativo da checagem numa atualização.
    Devolve a frase em vez de levantar erro para o menu perguntar de
    novo na hora; cadastrar() e atualizar() usam a mesma regra.
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
    # Depois do teste de caracteres: isdigit() aceita dígitos como "²".
    if h.isdigit():
        return "não pode ser composto só de números"
    if ativos is not None and _hostname_existe(ativos, h, ignorar_id):
        return "já é usado por outro ativo"
    return None


def _hostname_existe(ativos, hostname, ignorar_id=None):
    """Diz se outro ativo já usa o hostname, sem diferenciar a caixa."""
    alvo = hostname.strip().lower()
    for id_ativo, registro in ativos.items():
        if id_ativo == ignorar_id:
            continue
        if registro["hostname"].strip().lower() == alvo:
            return True
    return False


def _normalizar(campo, valor):
    """Formata o valor do campo, igual no cadastro e na edição."""
    if campo == "hostname":
        return valor.strip().upper()
    if campo in ("custodiante", "lotacao"):
        return formatacao.titulo(valor)
    if campo == "descricao":
        return formatacao.frase(valor)
    return valor


def cadastrar(ativos, hostname, custodiante, lotacao, descricao, categoria):
    """Cadastra um ativo e devolve o id gerado (requisito 3).

    Levanta ValueError se o hostname for inválido ou já estiver em uso:
    duas máquinas com o mesmo nome são um conflito real na rede.
    """
    problema = problema_no_hostname(hostname, ativos)
    if problema:
        raise ValueError(f"Hostname inválido: {problema}")

    id_novo = proximo_id_ativo(ativos)
    ativos[id_novo] = {
        "hostname": _normalizar("hostname", hostname),
        "custodiante": _normalizar("custodiante", custodiante),
        "lotacao": _normalizar("lotacao", lotacao),
        "descricao": _normalizar("descricao", descricao),
        "categoria": categoria,
    }
    return id_novo


def buscar_por_id(ativos, id_ativo):
    """Devolve o registro do ativo, ou None se o id não existir.

    Busca direta pela chave do dicionário (requisitos 4 e 9).
    """
    return ativos.get(id_ativo)


# Categoria fica de fora: é escolhida numa lista (buscar_por_categoria).
CAMPOS_DE_BUSCA = ("hostname", "custodiante", "lotacao")


def buscar_por_texto(ativos, campo, termo):
    """Devolve os pares (id, registro) cujo campo contém o termo.

    A busca é parcial e ignora acento e caixa: "cart" encontra
    "PC-CARTORIO-01". Percorre todos os ativos, ao contrário da busca
    por id. Levanta ValueError se o campo não aceitar busca por texto.
    """
    if campo not in CAMPOS_DE_BUSCA:
        raise ValueError(f"Campo sem busca por texto: '{campo}'")
    alvo = formatacao.para_busca(termo)
    encontrados = []
    for id_ativo, registro in sorted(ativos.items()):
        if alvo in formatacao.para_busca(registro[campo]):
            encontrados.append((id_ativo, registro))
    return encontrados


def buscar_por_categoria(ativos, categoria):
    """Devolve os pares (id, registro) da categoria, em ordem de id."""
    return [(id_ativo, registro)
            for id_ativo, registro in sorted(ativos.items())
            if registro["categoria"] == categoria]


def atualizar(ativos, id_ativo, alteracoes):
    """Aplica as alterações {campo: valor} ao ativo (requisito 5).

    Devolve True se atualizou e False se o id não existe. Levanta
    ValueError em campo protegido ou hostname inválido ou repetido;
    nesse caso nada muda.
    """
    registro = ativos.get(id_ativo)
    if registro is None:
        return False

    # Confere tudo antes de aplicar, para não alterar pela metade.
    for campo, valor in alteracoes.items():
        if campo not in CAMPOS_EDITAVEIS:
            raise ValueError(f"Campo não editável: '{campo}'")
        if campo == "hostname":
            problema = problema_no_hostname(valor, ativos, id_ativo)
            if problema:
                raise ValueError(f"Hostname inválido: {problema}")

    for campo, valor in alteracoes.items():
        registro[campo] = _normalizar(campo, valor)

    return True


def excluir(ativos, id_ativo):
    """Exclui o ativo e devolve False se o id não existia.

    As falhas do ativo são excluídas antes, pelo main.py, que coordena
    os dois módulos (requisito 6).
    """
    if id_ativo not in ativos:
        return False
    del ativos[id_ativo]
    return True


# Teste: exercita os requisitos 3 a 6 sem ninguém digitar nada.
if __name__ == "__main__":
    from classificacoes import CategoriaAtivo

    ativos = {}

    # --- Requisito 3 ---
    id1 = cadastrar(ativos, "PC-CARTORIO-01", "Escrivão de plantão",
                    "Cartório", "Estação de atendimento ao público",
                    CategoriaAtivo.ESTACAO_TRABALHO)
    id2 = cadastrar(ativos, "SRV-ARQUIVO", "Chefe de equipe",
                    "Sala técnica", "Servidor de arquivos",
                    CategoriaAtivo.SERVIDOR)
    print(f"Cadastrados os ids: {id1} e {id2}")

    try:
        cadastrar(ativos, "srv-arquivo", "X", "Y", "Z",
                  CategoriaAtivo.SERVIDOR)
    except ValueError as erro:
        print(f"Duplicado recusado: {erro}")

    # --- Formato do hostname ---
    print()
    for ruim in ("pc cartorio", "pc/cartorio", "-pc", "pc-", "12345", "pcção"):
        try:
            cadastrar(ativos, ruim, "X", "Y", "Z",
                      CategoriaAtivo.SERVIDOR)
            raise AssertionError(f"aceitou hostname inválido: {ruim!r}")
        except ValueError as erro:
            print(f"Recusado {ruim!r:15} {erro}")
    assert problema_no_hostname("10-ANDAR") is None, "recusou hostname válido"
    print("Aceito   '10-ANDAR'      começa com número, mas não é só número")

    # --- Requisito 4 ---
    print(f"\nBusca por id 2: {buscar_por_id(ativos, 2)['hostname']}")
    print(f"Busca por id 99: {buscar_por_id(ativos, 99)}  "
          f"(None = não existe)")

    print("\nBusca parcial por 'cart' no hostname:")
    for id_ativo, registro in buscar_por_texto(ativos, "hostname", "cart"):
        print(f"  {id_ativo} - {registro['hostname']}")

    # Sem acento e em minúscula, encontra "Escrivão de plantão".
    achados = [i for i, _ in buscar_por_texto(ativos, "custodiante",
                                              "escrivao")]
    print(f"Busca 'escrivao' no responsável: ids {achados}")
    assert achados == [1], "a busca sem acento falhou"

    servidores = buscar_por_categoria(ativos, CategoriaAtivo.SERVIDOR)
    print(f"Busca pela categoria Servidor: ids {[i for i, _ in servidores]}")

    # --- Requisito 5 ---
    atualizar(ativos, 1, {"custodiante": "Investigador de plantão"})
    print(f"\nApós atualizar: {ativos[1]['custodiante']}")

    try:
        atualizar(ativos, 1, {"id": 50})
    except ValueError as erro:
        print(f"Campo protegido: {erro}")

    # Tudo ou nada: o hostname repetido derruba a alteração inteira.
    try:
        atualizar(ativos, 1, {"custodiante": "Outro",
                              "hostname": "srv-arquivo"})
    except ValueError as erro:
        print(f"Recusada inteira: {erro}")
    custodiante = ativos[1]["custodiante"]
    assert custodiante == "Investigador de plantão", "mudou pela metade"

    # --- Requisito 6 ---
    print(f"\nExcluindo id 2: {excluir(ativos, 2)}")
    print(f"Excluindo id 2 de novo: {excluir(ativos, 2)}  "
          f"(False = já não existia)")
    print(f"Restaram os ids: {list(ativos.keys())}")

    print("\nOK - requisitos 3, 4, 5 e 6 exercitados.")
