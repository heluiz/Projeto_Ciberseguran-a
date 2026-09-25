"""Operações sobre as vulnerabilidades (falhas) dos ativos.

Como ativos.py, não lê do teclado nem grava em disco. Atende aos
requisitos 7 e 8, à exclusão em cascata do requisito 6 e ao
relatório de pendentes da opção 10.
"""

from arquivo import proximo_id_falha
from classificacoes import SituacaoTratamento
import formatacao

# O ativo_id fica de fora: mudar a falha de ativo é um novo cadastro.
CAMPOS_EDITAVEIS = ("descricao", "origem", "gravidade", "situacao")


def cadastrar(falhas, ativo_id, descricao, origem, gravidade, situacao):
    """Registra uma falha e devolve o id gerado (requisito 7).

    Não confere se o ativo existe: este módulo não recebe os ativos, de
    propósito, para ser testado sozinho. Quem confere é o main.py.
    """
    id_novo = proximo_id_falha(falhas)
    falhas[id_novo] = {
        "ativo_id": ativo_id,
        "descricao": formatacao.frase(descricao),
        "origem": origem,
        "gravidade": gravidade,
        "situacao": situacao,
    }
    return id_novo


def listar_por_ativo(falhas, ativo_id):
    """Devolve as falhas do ativo, da mais grave para a menos grave.

    Cada item é um par (id, registro); lista vazia significa ativo sem
    vulnerabilidades registradas (requisito 8).
    """
    encontradas = []
    for id_falha, registro in falhas.items():
        if registro["ativo_id"] == ativo_id:
            encontradas.append((id_falha, registro))
    encontradas.sort(key=lambda par: par[1]["gravidade"].value, reverse=True)
    return encontradas


# Corrigida e aceita como risco já foram decididas; o resto pede ação.
SITUACOES_PENDENTES = (SituacaoTratamento.ABERTA,
                       SituacaoTratamento.EM_TRATAMENTO)


def listar_pendentes(falhas):
    """Devolve as falhas pendentes de todos os ativos, da mais grave.

    Base do relatório da opção 10. No empate de gravidade, mantém a
    ordem de cadastro, porque o sort() do Python é estável.
    """
    pendentes = [(id_falha, registro)
                 for id_falha, registro in falhas.items()
                 if registro["situacao"] in SITUACOES_PENDENTES]
    pendentes.sort(key=lambda par: par[1]["gravidade"].value, reverse=True)
    return pendentes


def atualizar(falhas, id_falha, alteracoes):
    """Aplica as alterações {campo: valor} à falha.

    Devolve True se atualizou e False se o id não existe. Levanta
    ValueError em campo protegido; nesse caso nada muda.
    """
    registro = falhas.get(id_falha)
    if registro is None:
        return False

    # Confere tudo antes de aplicar, como na atualização de ativos.
    for campo in alteracoes:
        if campo not in CAMPOS_EDITAVEIS:
            raise ValueError(f"Campo não editável: '{campo}'")

    for campo, valor in alteracoes.items():
        if campo == "descricao":
            valor = formatacao.frase(valor)
        registro[campo] = valor

    return True


def excluir(falhas, id_falha):
    """Exclui uma falha e devolve False se o id não existia.

    Serve para cadastro errado ou duplicado. Falha resolvida não se
    exclui: marca-se como Corrigida, para manter o histórico.
    """
    if id_falha not in falhas:
        return False
    del falhas[id_falha]
    return True


def excluir_por_ativo(falhas, ativo_id):
    """Exclui as falhas do ativo e devolve quantas foram excluídas.

    É a cascata do requisito 6. Os ids são separados antes porque
    apagar chaves de um dicionário enquanto se percorre ele levanta
    RuntimeError.
    """
    ids_para_remover = [
        id_falha
        for id_falha, registro in falhas.items()
        if registro["ativo_id"] == ativo_id
    ]

    for id_falha in ids_para_remover:
        del falhas[id_falha]

    return len(ids_para_remover)


# Teste: requisitos 7, 8 e a cascata do 6, sem ninguém digitar nada.
if __name__ == "__main__":
    from classificacoes import OrigemFalha, NivelGravidade

    falhas = {}

    # --- Requisito 7 ---
    cadastrar(falhas, 1, "Sistema operacional sem atualização há 8 meses",
              OrigemFalha.FALTA_ATUALIZACAO, NivelGravidade.ALTA,
              SituacaoTratamento.ABERTA)
    cadastrar(falhas, 1, "Compartilhamento de rede aberto para todos",
              OrigemFalha.PERMISSAO_INDEVIDA, NivelGravidade.CRITICA,
              SituacaoTratamento.EM_TRATAMENTO)
    cadastrar(falhas, 1, "Senha padrão de fábrica ainda em uso",
              OrigemFalha.SENHA_FRACA, NivelGravidade.MEDIA,
              SituacaoTratamento.ABERTA)
    cadastrar(falhas, 2, "Porta de acesso remoto exposta na rede interna",
              OrigemFalha.SERVICO_EXPOSTO, NivelGravidade.ALTA,
              SituacaoTratamento.ABERTA)
    print(f"Cadastradas {len(falhas)} falhas.")

    # --- Requisito 8 ---
    print("\nFalhas do ativo 1 (mais grave primeiro):")
    for id_falha, registro in listar_por_ativo(falhas, 1):
        print(f"  [{id_falha}] {registro['gravidade'].rotulo:8} | "
              f"{registro['situacao'].rotulo:18} | {registro['descricao']}")

    vazio = listar_por_ativo(falhas, 99)
    print(f"\nFalhas do ativo 99: {vazio}")
    print("  (lista vazia = o menu vai dizer "
          "'sem vulnerabilidades registradas')")

    # --- Correção de um cadastro errado ---
    atualizar(falhas, 3, {
        "gravidade": NivelGravidade.CRITICA,
        "descricao": "Senha padrão de fábrica na interface web",
    })
    print(f"\nFalha 3 corrigida: {falhas[3]['gravidade'].rotulo} | "
          f"{falhas[3]['descricao']}")

    try:
        atualizar(falhas, 3, {"ativo_id": 99})
    except ValueError as erro:
        print(f"Campo protegido: {erro}")

    # --- Acompanhamento do tratamento ---
    atualizar(falhas, 1, {"situacao": SituacaoTratamento.CORRIGIDA})
    print(f"Falha 1 agora está: {falhas[1]['situacao'].rotulo}")

    # --- Relatório de pendentes (opção 10) ---
    pendentes = [id_falha for id_falha, _ in listar_pendentes(falhas)]
    print(f"Pendentes, da mais grave: {pendentes}  (a 1 saiu: foi corrigida)")
    assert pendentes == [2, 3, 4], "o relatório de pendentes errou"

    # --- Exclusão de uma vulnerabilidade só ---
    print(f"\nExcluindo a falha 3: {excluir(falhas, 3)}")
    print(f"Excluindo a falha 3 de novo: {excluir(falhas, 3)}  "
          f"(False = já não existia)")
    print(f"Restaram os ids: {sorted(falhas.keys())}")

    # --- Requisito 6, cascata ---
    removidas = excluir_por_ativo(falhas, 1)
    print(f"\nExcluídas em cascata do ativo 1: {removidas}")
    print(f"Restaram os ids: {list(falhas.keys())}  (a falha do ativo 2)")

    print("\nOK - requisitos 7, 8 e a cascata do 6 exercitados.")
