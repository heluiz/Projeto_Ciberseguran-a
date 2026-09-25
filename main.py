"""Programa principal: menu, leitura do teclado e exibição.

Único módulo que conversa com o usuário. Também coordena as regras que
envolvem mais de um módulo, como a exclusão em cascata. Atende ao
requisito 1 e integra os demais.
"""

import arquivo
import ativos
import falhas
from classificacoes import (
    CategoriaAtivo,
    OrigemFalha,
    NivelGravidade,
    SituacaoTratamento,
)

# Os dicionários de dados se chamam base_ativos e base_falhas para não
# ocultarem os módulos ativos e falhas.


def ler_texto(mensagem, obrigatorio=True):
    """Lê um texto; se obrigatório, repete a pergunta até vir algo.

    Recusa caracteres de controle, como ESC: gravados, eles alterariam
    o terminal toda vez que o texto fosse exibido.
    """
    while True:
        valor = input(mensagem).strip()
        if not valor.isprintable():
            print("  ! Use apenas caracteres visíveis.")
        elif valor or not obrigatorio:
            return valor
        else:
            print("  ! Este campo não pode ficar vazio.")


# Texto mais curto que isto pede confirmação: "TI" pode ser um setor,
# mas "a" costuma ser engano de digitação.
MINIMO_SEM_CONFIRMAR = 3


def ler_campo(mensagem, obrigatorio=True):
    """Lê responsável, lotação ou descrição.

    Recusa texto sem nenhuma letra ("12") e pede confirmação para texto
    curto ("TI"). Com obrigatorio=False, Enter vazio devolve "" (manter
    o valor atual).
    """
    while True:
        valor = ler_texto(mensagem, obrigatorio)
        if not valor:
            return valor
        if not any(c.isalpha() for c in valor):
            print("  ! Use pelo menos uma letra.")
            continue
        pergunta = f'  "{valor}" ficou curto. É isso mesmo?'
        if len(valor) < MINIMO_SEM_CONFIRMAR and not confirmar(pergunta):
            continue
        return valor


def ler_inteiro(mensagem, opcional=False):
    """Lê um número inteiro, repetindo a pergunta até vir um válido.

    Com opcional=True, Enter vazio devolve None (manter o valor atual).
    """
    while True:
        bruto = input(mensagem).strip()
        if not bruto and opcional:
            return None
        try:
            return int(bruto)
        except ValueError:
            print("  ! Digite apenas números.")


def ler_enum(mensagem, classe_enum, opcional=False):
    """Mostra as opções do Enum e só aceita um código da lista.

    Com opcional=True, Enter vazio devolve None.
    """
    print(f"\n{mensagem}")
    for item in classe_enum:
        print(f"    {item.value} - {item.rotulo}")

    while True:
        codigo = ler_inteiro("  Código: ", opcional=opcional)
        if codigo is None:
            return None
        try:
            return classe_enum(codigo)
        except ValueError:
            print("  ! Código inválido. Escolha um da lista acima.")


def confirmar(mensagem):
    """Devolve True se o usuário responder 's' ou 'sim'."""
    return input(f"{mensagem} (s/N): ").strip().lower() in ("s", "sim")


def ler_hostname(mensagem, base_ativos, ignorar_id=None,
                 obrigatorio=True):
    """Lê um hostname e repete a pergunta até vir um nome válido.

    A regra, inclusive a de nome repetido, fica em
    ativos.problema_no_hostname(). Vazio só é aceito com
    obrigatorio=False (na atualização, manter o atual).
    """
    while True:
        valor = ler_texto(mensagem, obrigatorio)
        if not valor:
            return valor
        problema = ativos.problema_no_hostname(valor, base_ativos,
                                               ignorar_id)
        if problema is None:
            return valor
        print(f"  ! Hostname inválido: {problema}.")


def coluna(texto, largura, a_direita=False):
    """Encaixa o texto numa coluna de largura fixa.

    Texto longo é cortado e marcado com "..". Números vão à direita
    (a_direita=True), para as unidades ficarem alinhadas.
    """
    texto = str(texto)
    if len(texto) > largura:
        return texto[:largura - 2] + ".."
    if a_direita:
        return texto.rjust(largura)
    return texto.ljust(largura)


def linha_da_tabela(valores, larguras, a_direita):
    """Monta uma linha da tabela, com dois espaços entre as colunas."""
    celulas = [coluna(valor, largura, direita)
               for valor, largura, direita
               in zip(valores, larguras, a_direita)]
    return "  " + "  ".join(celulas)


def mostrar_tabela(base_falhas, itens):
    """Mostra ativos em tabela, uma linha por ativo.

    Cada coluna tem a largura do maior valor da lista, até um teto. Com
    todos os tetos, a linha mais larga tem 113 caracteres e cabe nas
    120 colunas do Windows Terminal.
    """
    cabecalho = ("ID", "HOSTNAME", "CATEGORIA", "RESPONSÁVEL", "LOTAÇÃO",
                 "VULNS")
    tetos = (6, 24, 22, 24, 20, 5)
    a_direita = (True, False, False, False, False, True)

    linhas = []
    for id_ativo, registro in itens:
        quantas = len(falhas.listar_por_ativo(base_falhas, id_ativo))
        linhas.append((str(id_ativo), registro["hostname"],
                       registro["categoria"].rotulo, registro["custodiante"],
                       registro["lotacao"], str(quantas)))

    # Largura: o maior entre o título e os valores, limitada ao teto.
    larguras = []
    for posicao, titulo in enumerate(cabecalho):
        maior = max([len(titulo)] + [len(linha[posicao]) for linha in linhas])
        larguras.append(min(maior, tetos[posicao]))

    print("\n" + linha_da_tabela(cabecalho, larguras, a_direita))
    print("  " + "-" * (sum(larguras) + 2 * (len(larguras) - 1)))
    for linha in linhas:
        print(linha_da_tabela(linha, larguras, a_direita))


def mostrar_ativo(id_ativo, registro):
    """Mostra a ficha de um ativo."""
    print(f"\n  ID ............ {id_ativo}")
    print(f"  Hostname ...... {registro['hostname']}")
    print(f"  Custodiante ... {registro['custodiante']}")
    print(f"  Lotação ....... {registro['lotacao']}")
    print(f"  Categoria ..... {registro['categoria'].rotulo}")
    print(f"  Descrição ..... {registro['descricao']}")


def mostrar_falha(id_falha, registro, base_ativos):
    """Mostra uma falha, com hostname e responsável do ativo.

    O acesso direto base_ativos[...] é seguro: a carga recusa falha que
    aponte para ativo inexistente.
    """
    ativo = base_ativos[registro["ativo_id"]]
    print(f"\n  ID ............ {id_falha}")
    print(f"  Ativo ......... {registro['ativo_id']} - "
          f"{ativo['hostname']} ({ativo['custodiante']})")
    print(f"  Descrição ..... {registro['descricao']}")
    print(f"  Categoria ..... {registro['origem'].rotulo}")
    print(f"  Severidade .... {registro['gravidade'].rotulo}")
    print(f"  Situação ...... {registro['situacao'].rotulo}")


def imprimir_falhas(encontradas, base_ativos=None):
    """Imprime falhas em duas linhas cada, na ordem recebida.

    Primeira linha: severidade em coluna fixa, id e descrição. Segunda:
    situação e categoria. Com base_ativos (relatório de pendentes), a
    segunda linha começa pelo hostname do ativo.
    """
    # Largura do id tirada da própria lista, para alinhar [3] e [147].
    largura_id = max(len(f"[{id_falha}]") for id_falha, _ in encontradas)

    for id_falha, registro in encontradas:
        marcador = f"[{id_falha}]"
        legenda = (f"{registro['situacao'].rotulo} · "
                   f"{registro['origem'].rotulo}")
        if base_ativos is not None:
            hostname = base_ativos[registro["ativo_id"]]["hostname"]
            legenda = f"{hostname} · {legenda}"
        print(f"    {registro['gravidade'].rotulo.upper():<9} "
              f"{marcador:<{largura_id}} {registro['descricao']}")
        print(f"    {'':<9} {'':<{largura_id}} {legenda}\n")


def mostrar_falhas(base_falhas, id_ativo):
    """Mostra as falhas do ativo (requisito 8)."""
    encontradas = falhas.listar_por_ativo(base_falhas, id_ativo)

    if not encontradas:
        print("\n  Este ativo está sem vulnerabilidades registradas.")
        return

    print(f"\n  Vulnerabilidades ({len(encontradas)}), da mais grave:\n")
    imprimir_falhas(encontradas)


def cadastrar_falha_para(base_ativos, base_falhas, id_ativo):
    """Pergunta os campos de uma vulnerabilidade, registra e grava.

    Usada no cadastro do ativo (requisito 3) e na opção 6 (requisito
    7), para as duas telas se comportarem igual.
    """
    descricao = ler_campo("  Descrição da vulnerabilidade: ")
    origem = ler_enum("  Categoria da vulnerabilidade:", OrigemFalha)
    gravidade = ler_enum("  Severidade:", NivelGravidade)
    situacao = ler_enum("  Status do tratamento:", SituacaoTratamento)

    id_falha = falhas.cadastrar(base_falhas, id_ativo, descricao,
                                origem, gravidade, situacao)
    arquivo.salvar(base_ativos, base_falhas)
    print(f"\n  Vulnerabilidade {id_falha} registrada.")


def acao_cadastrar_ativo(base_ativos, base_falhas):
    """Opção 1: cadastra um ativo e as falhas iniciais (requisito 3)."""
    print("\n--- CADASTRAR ATIVO ---\n")
    hostname = ler_hostname("  Hostname: ", base_ativos)
    custodiante = ler_campo("  Custodiante (responsável): ")
    lotacao = ler_campo("  Lotação (setor): ")
    descricao = ler_campo("  Descrição: ")
    categoria = ler_enum("  Tipo de ativo:", CategoriaAtivo)

    try:
        id_novo = ativos.cadastrar(base_ativos, hostname, custodiante,
                                   lotacao, descricao, categoria)
    except ValueError as erro:
        print(f"\n  ! {erro}")
        return

    arquivo.salvar(base_ativos, base_falhas)
    print(f"\n  Ativo cadastrado com o ID {id_novo}.")

    # A lista inicial de vulnerabilidades do requisito 3.
    while confirmar("\n  Cadastrar uma vulnerabilidade para este ativo?"):
        cadastrar_falha_para(base_ativos, base_falhas, id_novo)


def acao_listar_todos(base_ativos, base_falhas):
    """Opção 2: mostra todos os ativos em tabela."""
    print("\n--- ATIVOS CADASTRADOS ---")

    if not base_ativos:
        print("\n  Nenhum ativo cadastrado ainda.")
        return

    mostrar_tabela(base_falhas, sorted(base_ativos.items()))


# Buscas por texto da opção 3: número da opção -> (campo, pergunta).
BUSCAS_POR_TEXTO = {
    2: ("hostname", "  Hostname (ou parte dele): "),
    3: ("custodiante", "  Responsável (ou parte do nome): "),
    4: ("lotacao", "  Lotação (ou parte dela): "),
}


def acao_buscar(base_ativos, base_falhas):
    """Opção 3: busca ativos por id, hostname ou outros campos.

    O requisito 4 pede id e hostname; responsável, lotação e categoria
    vão além. Um resultado mostra a ficha completa; vários, a tabela.
    """
    print("\n--- BUSCAR ATIVO ---\n")
    print("    1 - Por ID")
    print("    2 - Por hostname")
    print("    3 - Por responsável")
    print("    4 - Por lotação")
    print("    5 - Por categoria")
    opcao = ler_inteiro("  Opção: ")

    if opcao == 1:
        id_ativo = ler_inteiro("  ID: ")
        registro = ativos.buscar_por_id(base_ativos, id_ativo)
        encontrados = []
        if registro is not None:
            encontrados.append((id_ativo, registro))
    elif opcao in BUSCAS_POR_TEXTO:
        campo, pergunta = BUSCAS_POR_TEXTO[opcao]
        termo = ler_texto(pergunta)
        encontrados = ativos.buscar_por_texto(base_ativos, campo, termo)
    elif opcao == 5:
        categoria = ler_enum("  Categoria:", CategoriaAtivo)
        encontrados = ativos.buscar_por_categoria(base_ativos, categoria)
    else:
        print("\n  ! Opção inválida.")
        return

    if not encontrados:
        print("\n  ! Nenhum ativo encontrado.")
    elif len(encontrados) == 1:
        id_ativo, registro = encontrados[0]
        mostrar_ativo(id_ativo, registro)
        mostrar_falhas(base_falhas, id_ativo)
    else:
        print(f"\n  {len(encontrados)} ativos encontrados:")
        mostrar_tabela(base_falhas, encontrados)
        print("\n  Para ver a ficha e as vulnerabilidades de um deles, "
              "use a opção 7.")


def acao_atualizar(base_ativos, base_falhas):
    """Opção 4: altera os campos de um ativo (requisito 5).

    Enter mantém o valor atual. As mudanças vão juntas para o módulo,
    que recusa todas se alguma for inválida.
    """
    print("\n--- ATUALIZAR ATIVO ---\n")
    id_ativo = ler_inteiro("  ID do ativo: ")
    registro = ativos.buscar_por_id(base_ativos, id_ativo)
    if registro is None:
        print(f"\n  ! Nenhum ativo com o ID {id_ativo}.")
        return

    mostrar_ativo(id_ativo, registro)
    print("\n  Deixe em branco para manter o valor atual.\n")

    alteracoes = {}

    novo = ler_hostname(f"  Hostname [{registro['hostname']}]: ",
                        base_ativos, ignorar_id=id_ativo,
                        obrigatorio=False)
    if novo:
        alteracoes["hostname"] = novo

    novo = ler_campo(f"  Custodiante [{registro['custodiante']}]: ",
                     obrigatorio=False)
    if novo:
        alteracoes["custodiante"] = novo

    novo = ler_campo(f"  Lotação [{registro['lotacao']}]: ",
                     obrigatorio=False)
    if novo:
        alteracoes["lotacao"] = novo

    novo = ler_campo(f"  Descrição [{registro['descricao']}]: ",
                     obrigatorio=False)
    if novo:
        alteracoes["descricao"] = novo

    nova_categoria = ler_enum(
        f"  Tipo (atual: {registro['categoria'].rotulo})"
        " - Enter para manter:",
        CategoriaAtivo, opcional=True)
    if nova_categoria is not None:
        alteracoes["categoria"] = nova_categoria

    if not alteracoes:
        print("\n  Nada foi alterado.")
        return

    try:
        ativos.atualizar(base_ativos, id_ativo, alteracoes)
    except ValueError as erro:
        print(f"\n  ! {erro}")
        return

    arquivo.salvar(base_ativos, base_falhas)
    print(f"\n  Ativo atualizado ({len(alteracoes)} campo(s)).")


def acao_excluir(base_ativos, base_falhas):
    """Opção 5: exclui o ativo e, em cascata, as falhas dele.

    Requisito 6. A cascata fica aqui porque é o main.py que coordena
    ativos.py e falhas.py.
    """
    print("\n--- EXCLUIR ATIVO ---\n")
    id_ativo = ler_inteiro("  ID do ativo: ")
    registro = ativos.buscar_por_id(base_ativos, id_ativo)
    if registro is None:
        print(f"\n  ! Nenhum ativo com o ID {id_ativo}.")
        return

    mostrar_ativo(id_ativo, registro)
    mostrar_falhas(base_falhas, id_ativo)

    if not confirmar("\n  Confirma a exclusão do ativo e das falhas dele?"):
        print("\n  Exclusão cancelada.")
        return

    # Falhas primeiro: se algo der errado no meio, não sobra falha
    # apontando para ativo inexistente.
    removidas = falhas.excluir_por_ativo(base_falhas, id_ativo)
    ativos.excluir(base_ativos, id_ativo)

    arquivo.salvar(base_ativos, base_falhas)
    print(f"\n  Ativo excluído, junto com {removidas} vulnerabilidade(s).")


def acao_cadastrar_falha(base_ativos, base_falhas):
    """Opção 6: cadastra uma vulnerabilidade num ativo (requisito 7)."""
    print("\n--- CADASTRAR VULNERABILIDADE ---\n")
    id_ativo = ler_inteiro("  ID do ativo: ")

    # falhas.py não recebe os ativos; a existência é conferida aqui.
    if ativos.buscar_por_id(base_ativos, id_ativo) is None:
        print(f"\n  ! Nenhum ativo com o ID {id_ativo}.")
        return

    cadastrar_falha_para(base_ativos, base_falhas, id_ativo)


def acao_ver_falhas(base_ativos, base_falhas):
    """Opção 7: mostra o ativo e as falhas dele (requisito 8)."""
    print("\n--- VULNERABILIDADES DE UM ATIVO ---\n")
    id_ativo = ler_inteiro("  ID do ativo: ")
    registro = ativos.buscar_por_id(base_ativos, id_ativo)
    if registro is None:
        print(f"\n  ! Nenhum ativo com o ID {id_ativo}.")
        return

    mostrar_ativo(id_ativo, registro)
    mostrar_falhas(base_falhas, id_ativo)


def acao_atualizar_falha(base_ativos, base_falhas):
    """Opção 8: corrige uma vulnerabilidade já cadastrada.

    Mesma mecânica da opção 4: Enter mantém o valor atual. Serve também
    para mudar só a situação do tratamento.
    """
    print("\n--- ATUALIZAR VULNERABILIDADE ---\n")
    id_falha = ler_inteiro("  ID da vulnerabilidade: ")

    if id_falha not in base_falhas:
        print(f"\n  ! Nenhuma vulnerabilidade com o ID {id_falha}.")
        return

    registro = base_falhas[id_falha]
    mostrar_falha(id_falha, registro, base_ativos)
    print("\n  Deixe em branco para manter o valor atual.\n")

    alteracoes = {}

    novo = ler_campo(f"  Descrição [{registro['descricao']}]: ",
                     obrigatorio=False)
    if novo:
        alteracoes["descricao"] = novo

    nova_origem = ler_enum(
        f"  Categoria (atual: {registro['origem'].rotulo})"
        " - Enter para manter:",
        OrigemFalha, opcional=True)
    if nova_origem is not None:
        alteracoes["origem"] = nova_origem

    nova_gravidade = ler_enum(
        f"  Severidade (atual: {registro['gravidade'].rotulo})"
        " - Enter para manter:",
        NivelGravidade, opcional=True)
    if nova_gravidade is not None:
        alteracoes["gravidade"] = nova_gravidade

    nova_situacao = ler_enum(
        f"  Situação (atual: {registro['situacao'].rotulo})"
        " - Enter para manter:",
        SituacaoTratamento, opcional=True)
    if nova_situacao is not None:
        alteracoes["situacao"] = nova_situacao

    if not alteracoes:
        print("\n  Nada foi alterado.")
        return

    try:
        falhas.atualizar(base_falhas, id_falha, alteracoes)
    except ValueError as erro:
        print(f"\n  ! {erro}")
        return

    arquivo.salvar(base_ativos, base_falhas)
    print(f"\n  Vulnerabilidade atualizada ({len(alteracoes)} campo(s)).")


def acao_excluir_falha(base_ativos, base_falhas):
    """Opção 9: exclui uma vulnerabilidade cadastrada por engano.

    Falha resolvida deve ser marcada como Corrigida (opção 8), não
    excluída, para não perder o histórico; a tela avisa isso.
    """
    print("\n--- EXCLUIR VULNERABILIDADE ---\n")
    id_falha = ler_inteiro("  ID da vulnerabilidade: ")

    if id_falha not in base_falhas:
        print(f"\n  ! Nenhuma vulnerabilidade com o ID {id_falha}.")
        return

    mostrar_falha(id_falha, base_falhas[id_falha], base_ativos)

    print("\n  Atenção: exclua apenas cadastro errado ou duplicado.")
    print("  Se a vulnerabilidade foi resolvida, use a opção 8 e marque")
    print("  como Corrigida - apagar destrói o histórico.")

    if not confirmar("\n  Confirma a exclusão?"):
        print("\n  Exclusão cancelada.")
        return

    falhas.excluir(base_falhas, id_falha)
    arquivo.salvar(base_ativos, base_falhas)
    print("\n  Vulnerabilidade excluída.")


def acao_pendentes(base_ativos, base_falhas):
    """Opção 10: lista as falhas pendentes de todos os ativos.

    Vai além do enunciado: mostra o que corrigir primeiro sem abrir a
    ficha de cada ativo.
    """
    print("\n--- VULNERABILIDADES PENDENTES ---")
    pendentes = falhas.listar_pendentes(base_falhas)

    if not pendentes:
        print("\n  Nenhuma vulnerabilidade aberta ou em tratamento.")
        return

    print(f"\n  {len(pendentes)} aberta(s) ou em tratamento, da mais grave:\n")
    imprimir_falhas(pendentes, base_ativos)


# Número da opção -> função que a executa. Substitui uma cadeia de
# if/elif: ligar uma opção nova custa uma linha aqui e um print em
# exibir_menu().
ACOES = {
    1: acao_cadastrar_ativo,
    2: acao_listar_todos,
    3: acao_buscar,
    4: acao_atualizar,
    5: acao_excluir,
    6: acao_cadastrar_falha,
    7: acao_ver_falhas,
    8: acao_atualizar_falha,
    9: acao_excluir_falha,
    10: acao_pendentes,
}


def exibir_menu():
    """Mostra o menu, com os números alinhados à direita."""
    print("\n" + "=" * 62)
    print("   1 - Cadastrar ativo")
    print("   2 - Listar todos os ativos")
    print("   3 - Buscar ativo (por ID, hostname, responsável...)")
    print("   4 - Atualizar ativo")
    print("   5 - Excluir ativo (e suas vulnerabilidades)")
    print("   6 - Cadastrar vulnerabilidade")
    print("   7 - Ver vulnerabilidades de um ativo")
    print("   8 - Atualizar vulnerabilidade")
    print("   9 - Excluir vulnerabilidade")
    print("  10 - Vulnerabilidades pendentes (todas, da mais grave)")
    print("   0 - Sair")
    print("=" * 62)


def main():
    """Carrega a base e repete o menu até o usuário escolher 0."""
    print("\n" + "=" * 62)
    print("  INVENTÁRIO DE ATIVOS E VULNERABILIDADES")
    print("=" * 62)

    # A base é lida uma vez; cada alteração é gravada na hora.
    base_ativos, base_falhas = arquivo.carregar()
    print(f"\n  Base carregada: {len(base_ativos)} ativo(s), "
          f"{len(base_falhas)} vulnerabilidade(s).")

    while True:
        exibir_menu()
        opcao = ler_inteiro("  Opção: ")

        if opcao == 0:
            print("\n  Até logo.\n")
            break

        acao = ACOES.get(opcao)
        if acao is None:
            print("\n  ! Opção inexistente. Escolha um número do menu.")
            continue

        try:
            acao(base_ativos, base_falhas)
        except EOFError:
            raise  # Ctrl+Z ou Ctrl+D: encerramento limpo, no fim do arquivo
        except Exception as erro:
            # Ponto de isolamento (requisito 1): um erro inesperado numa
            # ação não derruba o programa. A base é recarregada porque
            # a ação pode ter parado entre a memória e o disco.
            print(f"\n  ! Erro inesperado: {erro}")
            base_ativos, base_falhas = arquivo.carregar()
            print("  ! Base recarregada do disco: o que não chegou a ser "
                  "gravado foi descartado.")


if __name__ == "__main__":
    try:
        main()
    except arquivo.BaseInvalida as erro:
        # Não abre base ruim: a primeira gravação apagaria o original.
        print(f"\n  ! Não foi possível carregar a base de dados: {erro}")
        print(f"  ! Arquivo: {arquivo.ARQUIVO_DADOS}")
        print("  ! O programa para aqui, para não sobrescrever dados bons.")
        print("  ! Corrija o arquivo, ou mova-o para fora da pasta")
        print("    e o programa começa uma base nova.\n")
    except (KeyboardInterrupt, EOFError):
        print("\n\n  Encerrado pelo usuário.\n")
