"""
falhas.py
---------
Operações sobre as vulnerabilidades associadas aos equipamentos.

Mesma regra do equipamentos.py: nenhum input(), nenhum print(), nenhuma
gravação em disco. Recebe dados, mexe no dicionário, devolve resultado.

Atende aos requisitos 7 e 8, e à parte de cascata do requisito 6.
"""

from arquivo import proximo_id


# ===========================================================================
# REQUISITO 7 - cadastro de vulnerabilidade
# ===========================================================================
def cadastrar(falhas, equipamento_id, descricao, origem, gravidade, situacao):
    """
    Registra uma vulnerabilidade e devolve o id gerado.

    Os quatro campos que o enunciado exige estão aqui: descrição, categoria
    (que eu chamei de origem), severidade (gravidade) e status de tratamento
    (situação).

    Repare que esta função NÃO confere se o equipamento_id existe. Ela não
    teria como: este módulo não enxerga o dicionário de equipamentos, de
    propósito. Quem confere antes de chamar é o main.py.

    Por que não receber os equipamentos aqui só para conferir? Porque aí os
    dois módulos ficariam amarrados um ao outro, e eu não conseguiria testar
    as falhas sem montar equipamentos junto - que é exatamente o que faço no
    bloco de teste no fim deste arquivo.
    """
    id_novo = proximo_id(falhas)
    falhas[id_novo] = {
        "equipamento_id": equipamento_id,
        "descricao":      descricao.strip(),
        "origem":         origem,
        "gravidade":      gravidade,
        "situacao":       situacao,
    }
    return id_novo


# ===========================================================================
# REQUISITO 8 - visualizar as vulnerabilidades de um equipamento
# ===========================================================================
def listar_por_equipamento(falhas, equipamento_id):
    """
    Devolve uma LISTA de pares (id, registro), da mais grave para a menos.

    Lista vazia significa "sem vulnerabilidades registradas". A mensagem em
    si sai no main.py - este módulo não fala com o usuário.

    A ordenação usa .gravidade.value, e é aqui que a decisão lá do
    classificacoes.py se paga: numerei BAIXA=1 ate CRITICA=4 justamente para
    que a ordem dos números significasse ordem de gravidade. Se eu tivesse
    numerado em ordem alfabética, esta ordenação não faria sentido nenhum.
    """
    encontradas = []
    for id_falha, registro in falhas.items():
        if registro["equipamento_id"] == equipamento_id:
            encontradas.append((id_falha, registro))

    # key= diz ao sort qual valor usar para comparar. O 'lambda' é uma função
    # curta escrita na própria linha: recebe um par (id, registro) e devolve
    # o número da gravidade. reverse=True põe a mais grave primeiro - quem
    # abre a ficha de um equipamento quer ver o problema crítico no topo.
    encontradas.sort(key=lambda par: par[1]["gravidade"].value, reverse=True)
    return encontradas


def atualizar_situacao(falhas, id_falha, nova_situacao):
    """
    Muda só o status de tratamento: aberta -> em tratamento -> corrigida.
    Devolve True se mudou, False se o id não existe.

    O enunciado não pede esta função. Incluí porque sem ela o "status de
    tratamento" do requisito 7 seria decorativo: eu registraria que a falha
    está aberta e nunca poderia marcá-la como corrigida. Um inventário de
    segurança existe justamente para acompanhar esse ciclo.
    """
    registro = falhas.get(id_falha)
    if registro is None:
        return False
    registro["situacao"] = nova_situacao
    return True


# ===========================================================================
# REQUISITO 6 - a cascata: ao excluir o equipamento, as falhas vão junto
# ===========================================================================
def excluir_por_equipamento(falhas, equipamento_id):
    """
    Apaga todas as falhas de um equipamento e devolve quantas foram apagadas.

    Por que montar a lista de ids ANTES de apagar, em vez de apagar dentro do
    laço? Porque alterar um dicionário enquanto se percorre ele levanta
    RuntimeError em Python. Primeiro decido o que sai, depois saio apagando.

    As três linhas abaixo são uma "list comprehension": um laço escrito de
    forma compacta. Lê-se de trás para frente - "para cada par no dicionário,
    SE o equipamento_id bater, guarde o id_falha".
    """
    ids_para_remover = [
        id_falha
        for id_falha, registro in falhas.items()
        if registro["equipamento_id"] == equipamento_id
    ]

    for id_falha in ids_para_remover:
        del falhas[id_falha]

    return len(ids_para_remover)


# ===========================================================================
# Teste: requisitos 7, 8 e a cascata do 6, sem ninguém digitar nada.
# ===========================================================================
if __name__ == "__main__":
    from classificacoes import OrigemFalha, NivelGravidade, SituacaoTratamento

    falhas = {}

    # --- Requisito 7 ---
    cadastrar(falhas, 1, "Sistema operacional sem atualizacao ha 8 meses",
              OrigemFalha.FALTA_ATUALIZACAO, NivelGravidade.ALTA,
              SituacaoTratamento.ABERTA)
    cadastrar(falhas, 1, "Compartilhamento de rede aberto para todos",
              OrigemFalha.PERMISSAO_INDEVIDA, NivelGravidade.CRITICA,
              SituacaoTratamento.EM_TRATAMENTO)
    cadastrar(falhas, 1, "Senha padrao de fabrica ainda em uso",
              OrigemFalha.SENHA_FRACA, NivelGravidade.MEDIA,
              SituacaoTratamento.ABERTA)
    cadastrar(falhas, 2, "Porta de acesso remoto exposta na rede interna",
              OrigemFalha.SERVICO_EXPOSTO, NivelGravidade.ALTA,
              SituacaoTratamento.ABERTA)
    print(f"Cadastradas {len(falhas)} falhas.")

    # --- Requisito 8 ---
    print("\nFalhas do equipamento 1 (mais grave primeiro):")
    for id_falha, registro in listar_por_equipamento(falhas, 1):
        print(f"  [{id_falha}] {registro['gravidade'].rotulo:8} | "
              f"{registro['situacao'].rotulo:18} | {registro['descricao']}")

    vazio = listar_por_equipamento(falhas, 99)
    print(f"\nFalhas do equipamento 99: {vazio}")
    print("  (lista vazia = o menu vai dizer 'sem vulnerabilidades registradas')")

    # --- acompanhamento do tratamento ---
    atualizar_situacao(falhas, 1, SituacaoTratamento.CORRIGIDA)
    print(f"\nFalha 1 agora esta: {falhas[1]['situacao'].rotulo}")

    # --- Requisito 6, cascata ---
    removidas = excluir_por_equipamento(falhas, 1)
    print(f"\nExcluidas em cascata do equipamento 1: {removidas}")
    print(f"Restaram os ids: {list(falhas.keys())}  (a falha do equipamento 2)")

    print("\nOK - requisitos 7, 8 e a cascata do 6 exercitados.")