"""
main.py
-------
O programa em si: menu, leitura do que o usuário digita e tratamento de erros.

Este é o único arquivo que conversa com o usuário. Os outros três não têm
nenhum input() nem print() - é o que permitiu testar cada um isoladamente.

Aqui também moram as regras que envolvem MAIS DE UM módulo, como a exclusão
em cascata: nem equipamentos.py nem falhas.py enxergam os dados um do outro,
então quem coordena os dois é este arquivo.

Atende ao requisito 1 e junta todos os demais.
"""

import arquivo
import equipamentos
import falhas
from classificacoes import (
    CategoriaEquipamento,
    OrigemFalha,
    NivelGravidade,
    SituacaoTratamento,
)


# Nota sobre os nomes:
# o MÓDULO se chama 'equipamentos' e o DICIONÁRIO com os dados se chama
# 'base_equipamentos'. Se os dois tivessem o mesmo nome, um sobrescreveria o
# outro e nada funcionaria. Essa distinção deixa cada chamada explícita:
# equipamentos.cadastrar(base_equipamentos, ...) lê-se como "o módulo
# equipamentos, operação cadastrar, sobre a base de equipamentos".


# ===========================================================================
# LEITURA COM TRATAMENTO DE ERROS - o coração do REQUISITO 1
#
# O enunciado manda evitar falhas por "comandos inválidos, campos vazios ou
# tipos de dados incorretos". Cada uma dessas três coisas tem uma função
# abaixo. Centralizar aqui significa que eu trato o erro UMA vez e todas as
# telas do programa ganham isso de graça.
# ===========================================================================
def ler_texto(mensagem, obrigatorio=True):
    """Campos vazios: repete a pergunta até vir algo escrito."""
    while True:
        valor = input(mensagem).strip()
        if valor or not obrigatorio:
            return valor
        print("  ! Este campo nao pode ficar vazio.")


def ler_inteiro(mensagem, opcional=False):
    """
    Tipos incorretos: repete até o usuário digitar um número de verdade.

    opcional=True aceita Enter vazio e devolve None. Uso isso na atualização,
    onde Enter significa "não quero mudar este campo".
    """
    while True:
        bruto = input(mensagem).strip()
        if not bruto and opcional:
            return None
        try:
            return int(bruto)
        except ValueError:
            # int() levanta ValueError quando o texto não é número.
            # Capturo aqui em vez de deixar o programa quebrar na cara do
            # usuário.
            print("  ! Digite apenas numeros.")


def ler_enum(mensagem, classe_enum, opcional=False):
    """
    Comandos inválidos: mostra as opções e só aceita um código da lista.
    Quem valida é o próprio Enum - código inexistente levanta ValueError.
    """
    print(f"\n{mensagem}")
    for item in classe_enum:
        print(f"    {item.value} - {item.rotulo}")

    while True:
        codigo = ler_inteiro("  Codigo: ", opcional=opcional)
        if codigo is None:
            return None
        try:
            return classe_enum(codigo)
        except ValueError:
            print("  ! Codigo invalido. Escolha um da lista acima.")


def confirmar(mensagem):
    """Só devolve True se o usuário digitar 's'. Qualquer outra coisa é não."""
    return input(f"{mensagem} (s/N): ").strip().lower() == "s"


# ===========================================================================
# EXIBIÇÃO
# ===========================================================================
def mostrar_equipamento(id_equipamento, registro):
    print(f"\n  ID ............ {id_equipamento}")
    print(f"  Hostname ...... {registro['hostname']}")
    print(f"  Custodiante ... {registro['custodiante']}")
    print(f"  Lotacao ....... {registro['lotacao']}")
    print(f"  Categoria ..... {registro['categoria'].rotulo}")
    print(f"  Descricao ..... {registro['descricao']}")


def mostrar_falhas(base_falhas, id_equipamento):
    """
    REQUISITO 8.
    A mensagem de "sem vulnerabilidades registradas" que o enunciado exige
    sai exatamente aqui - este é o único módulo que fala com o usuário.
    """
    encontradas = falhas.listar_por_equipamento(base_falhas, id_equipamento)

    if not encontradas:
        print("\n  Este equipamento esta sem vulnerabilidades registradas.")
        return

    print(f"\n  Vulnerabilidades ({len(encontradas)}), da mais grave:")
    for id_falha, registro in encontradas:
        print(f"    [{id_falha}] {registro['gravidade'].rotulo:8} | "
              f"{registro['situacao'].rotulo:18} | {registro['origem'].rotulo}")
        print(f"         {registro['descricao']}")


# ===========================================================================
# AÇÕES DO MENU
# ===========================================================================
def cadastrar_falha_para(base_falhas, id_equipamento):
    """
    Pergunta os quatro campos de uma vulnerabilidade e registra.

    Esta função é usada em DOIS lugares: no cadastro do equipamento
    (requisito 3, "lista inicial de vulnerabilidades") e na opção de menu
    própria (requisito 7, "a qualquer momento após o cadastro"). Escrevê-la
    uma vez só evita que as duas telas se comportem de forma diferente.
    """
    descricao = ler_texto("  Descricao da vulnerabilidade: ")
    origem = ler_enum("  Categoria da vulnerabilidade:", OrigemFalha)
    gravidade = ler_enum("  Severidade:", NivelGravidade)
    situacao = ler_enum("  Status do tratamento:", SituacaoTratamento)

    id_falha = falhas.cadastrar(base_falhas, id_equipamento, descricao,
                                origem, gravidade, situacao)
    print(f"\n  Vulnerabilidade {id_falha} registrada.")


def acao_cadastrar_equipamento(base_equipamentos, base_falhas):
    """REQUISITO 3."""
    print("\n--- CADASTRAR EQUIPAMENTO ---\n")
    hostname    = ler_texto("  Hostname: ")
    custodiante = ler_texto("  Custodiante (responsavel): ")
    lotacao     = ler_texto("  Lotacao (setor): ")
    descricao   = ler_texto("  Descricao: ")
    categoria   = ler_enum("  Tipo de equipamento:", CategoriaEquipamento)

    try:
        id_novo = equipamentos.cadastrar(base_equipamentos, hostname,
                                         custodiante, lotacao, descricao,
                                         categoria)
    except ValueError as erro:
        # Hostname duplicado. O módulo recusa, o menu explica.
        print(f"\n  ! {erro}")
        return

    print(f"\n  Equipamento cadastrado com o ID {id_novo}.")

    # Fim do requisito 3: "...e lista inicial de vulnerabilidades associadas,
    # quando houver". O laço abaixo é essa parte - logo após criar o
    # equipamento, ofereço cadastrar vulnerabilidades, quantas quiser.
    while confirmar("\n  Cadastrar uma vulnerabilidade para este equipamento?"):
        cadastrar_falha_para(base_falhas, id_novo)

    arquivo.salvar(base_equipamentos, base_falhas)


def acao_listar_todos(base_equipamentos, base_falhas):
    """Visão geral. Não é exigida pelo enunciado, mas sem ela o usuário
    teria que decorar os IDs para usar qualquer outra opção."""
    print("\n--- EQUIPAMENTOS CADASTRADOS ---")

    if not base_equipamentos:
        print("\n  Nenhum equipamento cadastrado ainda.")
        return

    print(f"\n  {'ID':<4} {'HOSTNAME':<20} {'CATEGORIA':<22} {'LOTACAO':<16} VULNS")
    print("  " + "-" * 74)
    for id_equipamento, registro in sorted(base_equipamentos.items()):
        quantas = len(falhas.listar_por_equipamento(base_falhas, id_equipamento))
        print(f"  {id_equipamento:<4} {registro['hostname']:<20} "
              f"{registro['categoria'].rotulo:<22} "
              f"{registro['lotacao']:<16} {quantas}")


def acao_buscar(base_equipamentos, base_falhas):
    """REQUISITO 4: por identificador OU por hostname."""
    print("\n--- BUSCAR EQUIPAMENTO ---\n")
    print("    1 - Por ID")
    print("    2 - Por hostname")
    opcao = ler_inteiro("  Opcao: ")

    if opcao == 1:
        id_equipamento = ler_inteiro("  ID: ")
        registro = equipamentos.buscar_por_id(base_equipamentos, id_equipamento)
        if registro is None:
            print(f"\n  ! Nenhum equipamento com o ID {id_equipamento}.")
            return
        mostrar_equipamento(id_equipamento, registro)
        mostrar_falhas(base_falhas, id_equipamento)

    elif opcao == 2:
        termo = ler_texto("  Hostname (ou parte dele): ")
        encontrados = equipamentos.buscar_por_hostname(base_equipamentos, termo)
        if not encontrados:
            print(f"\n  ! Nenhum equipamento com '{termo}' no hostname.")
            return
        print(f"\n  {len(encontrados)} equipamento(s) encontrado(s):")
        for id_equipamento, registro in encontrados:
            mostrar_equipamento(id_equipamento, registro)
            mostrar_falhas(base_falhas, id_equipamento)

    else:
        print("\n  ! Opcao invalida.")


def acao_atualizar(base_equipamentos, base_falhas):
    """REQUISITO 5."""
    print("\n--- ATUALIZAR EQUIPAMENTO ---\n")
    id_equipamento = ler_inteiro("  ID do equipamento: ")
    registro = equipamentos.buscar_por_id(base_equipamentos, id_equipamento)
    if registro is None:
        print(f"\n  ! Nenhum equipamento com o ID {id_equipamento}.")
        return

    mostrar_equipamento(id_equipamento, registro)
    print("\n  Deixe em branco para manter o valor atual.\n")

    # Monto um dicionário só com o que o usuário realmente quis mudar, e
    # entrego tudo de uma vez ao módulo. Assim uma alteração recusada (por
    # exemplo hostname duplicado) não deixa metade das mudanças aplicadas.
    alteracoes = {}

    novo = ler_texto(f"  Hostname [{registro['hostname']}]: ", obrigatorio=False)
    if novo:
        alteracoes["hostname"] = novo

    novo = ler_texto(f"  Custodiante [{registro['custodiante']}]: ", obrigatorio=False)
    if novo:
        alteracoes["custodiante"] = novo

    novo = ler_texto(f"  Lotacao [{registro['lotacao']}]: ", obrigatorio=False)
    if novo:
        alteracoes["lotacao"] = novo

    novo = ler_texto(f"  Descricao [{registro['descricao']}]: ", obrigatorio=False)
    if novo:
        alteracoes["descricao"] = novo

    nova_categoria = ler_enum(
        f"  Tipo (atual: {registro['categoria'].rotulo}) - Enter para manter:",
        CategoriaEquipamento, opcional=True)
    if nova_categoria is not None:
        alteracoes["categoria"] = nova_categoria

    if not alteracoes:
        print("\n  Nada foi alterado.")
        return

    try:
        equipamentos.atualizar(base_equipamentos, id_equipamento, alteracoes)
    except ValueError as erro:
        print(f"\n  ! {erro}")
        return

    arquivo.salvar(base_equipamentos, base_falhas)
    print(f"\n  Equipamento atualizado ({len(alteracoes)} campo(s)).")


def acao_excluir(base_equipamentos, base_falhas):
    """REQUISITO 6, com a cascata coordenada aqui."""
    print("\n--- EXCLUIR EQUIPAMENTO ---\n")
    id_equipamento = ler_inteiro("  ID do equipamento: ")
    registro = equipamentos.buscar_por_id(base_equipamentos, id_equipamento)
    if registro is None:
        print(f"\n  ! Nenhum equipamento com o ID {id_equipamento}.")
        return

    mostrar_equipamento(id_equipamento, registro)
    mostrar_falhas(base_falhas, id_equipamento)

    if not confirmar("\n  Confirma a exclusao do equipamento e das falhas dele?"):
        print("\n  Exclusao cancelada.")
        return

    # A CASCATA. Nesta ordem de propósito: primeiro as falhas, depois o
    # equipamento. Se o equipamento saísse primeiro e algo falhasse em
    # seguida, as falhas ficariam órfãs - apontando para um ID que já não
    # existe, e sem nenhuma tela do programa capaz de mostrá-las.
    removidas = falhas.excluir_por_equipamento(base_falhas, id_equipamento)
    equipamentos.excluir(base_equipamentos, id_equipamento)

    arquivo.salvar(base_equipamentos, base_falhas)
    print(f"\n  Equipamento excluido, junto com {removidas} vulnerabilidade(s).")


def acao_cadastrar_falha(base_equipamentos, base_falhas):
    """REQUISITO 7: cadastrar vulnerabilidade a qualquer momento."""
    print("\n--- CADASTRAR VULNERABILIDADE ---\n")
    id_equipamento = ler_inteiro("  ID do equipamento: ")

    # Esta é a checagem que o falhas.py não faz, porque ele não enxerga os
    # equipamentos. É aqui que ela cabe: o main é o único que vê os dois.
    if equipamentos.buscar_por_id(base_equipamentos, id_equipamento) is None:
        print(f"\n  ! Nenhum equipamento com o ID {id_equipamento}.")
        return

    cadastrar_falha_para(base_falhas, id_equipamento)
    arquivo.salvar(base_equipamentos, base_falhas)


def acao_ver_falhas(base_equipamentos, base_falhas):
    """REQUISITO 8."""
    print("\n--- VULNERABILIDADES DE UM EQUIPAMENTO ---\n")
    id_equipamento = ler_inteiro("  ID do equipamento: ")
    registro = equipamentos.buscar_por_id(base_equipamentos, id_equipamento)
    if registro is None:
        print(f"\n  ! Nenhum equipamento com o ID {id_equipamento}.")
        return

    mostrar_equipamento(id_equipamento, registro)
    mostrar_falhas(base_falhas, id_equipamento)


def acao_atualizar_situacao(base_equipamentos, base_falhas):
    """Acompanhamento do tratamento: aberta -> em tratamento -> corrigida."""
    print("\n--- ATUALIZAR SITUACAO DE UMA VULNERABILIDADE ---\n")
    id_falha = ler_inteiro("  ID da vulnerabilidade: ")

    if id_falha not in base_falhas:
        print(f"\n  ! Nenhuma vulnerabilidade com o ID {id_falha}.")
        return

    registro = base_falhas[id_falha]
    print(f"\n  {registro['descricao']}")
    print(f"  Situacao atual: {registro['situacao'].rotulo}")

    nova = ler_enum("  Nova situacao:", SituacaoTratamento)
    falhas.atualizar_situacao(base_falhas, id_falha, nova)

    arquivo.salvar(base_equipamentos, base_falhas)
    print(f"\n  Situacao alterada para: {nova.rotulo}")


# ===========================================================================
# O MENU
#
# Uso um DICIONÁRIO para ligar o número digitado à função correspondente,
# em vez de uma sequência de if/elif. Vantagens: acrescentar uma opção nova
# é uma linha só, e não existe risco de esquecer um elif no meio da cadeia.
#
# É, de quebra, um segundo uso de dicionário no projeto (requisito 9) - aqui
# não para guardar dados, mas para escolher comportamento.
# ===========================================================================
ACOES = {
    1: acao_cadastrar_equipamento,
    2: acao_listar_todos,
    3: acao_buscar,
    4: acao_atualizar,
    5: acao_excluir,
    6: acao_cadastrar_falha,
    7: acao_ver_falhas,
    8: acao_atualizar_situacao,
}


def exibir_menu():
    print("\n" + "=" * 62)
    print("  1 - Cadastrar equipamento")
    print("  2 - Listar todos os equipamentos")
    print("  3 - Buscar equipamento (por ID ou hostname)")
    print("  4 - Atualizar equipamento")
    print("  5 - Excluir equipamento (e suas vulnerabilidades)")
    print("  6 - Cadastrar vulnerabilidade")
    print("  7 - Ver vulnerabilidades de um equipamento")
    print("  8 - Atualizar situacao de uma vulnerabilidade")
    print("  0 - Sair")
    print("=" * 62)


def main():
    print("\n" + "=" * 62)
    print("  INVENTARIO DE SEGURANCA DE TI")
    print("=" * 62)

    # Carrego a base UMA vez, no início. Durante a execução tudo acontece na
    # memória (rápido), e cada alteração é gravada logo em seguida - assim
    # um fechamento inesperado não leva o trabalho junto.
    base_equipamentos, base_falhas = arquivo.carregar()
    print(f"\n  Base carregada: {len(base_equipamentos)} equipamento(s), "
          f"{len(base_falhas)} vulnerabilidade(s).")

    while True:
        exibir_menu()
        opcao = ler_inteiro("  Opcao: ")

        if opcao == 0:
            print("\n  Ate logo.\n")
            break

        acao = ACOES.get(opcao)
        if acao is None:
            print("\n  ! Opcao inexistente. Escolha um numero do menu.")
            continue

        try:
            acao(base_equipamentos, base_falhas)
        except Exception as erro:
            # Rede de segurança. Se algo inesperado escapar de uma ação, o
            # programa avisa e volta ao menu, em vez de fechar e perder a
            # sessão do usuário (requisito 1: "evitar falhas").
            #
            # Capturar Exception assim é abrangente demais para uma
            # biblioteca, porque esconderia bugs. Num programa de menu é o
            # oposto: fechar na cara do usuário é pior do que continuar.
            print(f"\n  ! Erro inesperado: {erro}")


if __name__ == "__main__":
    try:
        main()
    except arquivo.BaseInvalida as erro:
        # A base existe mas não pode ser lida. Recuso abrir de propósito: se
        # eu abrisse com base vazia, a primeira gravação sobrescreveria o
        # arquivo e o estrago viraria permanente.
        print(f"\n  ! A base de dados está corrompida: {erro}")
        print(f"  ! Arquivo: {arquivo.ARQUIVO_DADOS}")
        print("  ! O programa não vai abrir, para não sobrescrever dados bons.")
        print("  ! Corrija o arquivo, ou mova-o para fora da pasta")
        print("    e o programa começa uma base nova.\n")
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C ou fim de entrada: encerra limpo em vez de despejar um
        # traceback vermelho de dez linhas.
        print("\n\n  Encerrado pelo usuario.\n")
