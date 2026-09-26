"""Programa principal: menu, leitura do teclado e exibição.

Único módulo que conversa com o usuário. Também coordena as regras que
envolvem mais de um módulo, como a exclusão em cascata. Atende ao
requisito 1 e integra os demais.
"""

import os
import sys

import arquivo
import ativos
import cores
import falhas
from classificacoes import (
    CategoriaAtivo,
    OrigemFalha,
    NivelGravidade,
    SituacaoTratamento,
)

# Os dicionários de dados se chamam base_ativos e base_falhas para não
# ocultarem os módulos ativos e falhas.


# ------------------------------------------------------------------
# Comandos globais: voltar, sair, limpar e ajuda
#
# Funcionam em qualquer pergunta porque toda leitura do teclado passa
# por uma única porta, ler_resposta(). O caminho de uma resposta é:
#
#   1. ler_resposta() lê a linha e procura a palavra em COMANDOS.
#   2. Não é comando: devolve o texto, e a pergunta segue normal.
#   3. É "limpar" ou "ajuda": executa e faz a mesma pergunta de novo.
#   4. É "voltar" ou "sair": levanta uma exceção, que atravessa todas
#      as funções abertas até ser capturada no laço do menu, em main()
#      e em executar(). É o mesmo mecanismo de sys.exit(), que também
#      encerra o programa levantando uma exceção (SystemExit).
#
# Sem exceção, cada ler_*() teria de devolver um valor especial e
# cada ação teria de testá-lo depois de cada pergunta.
# ------------------------------------------------------------------


class VoltarAoMenu(Exception):
    """Pedido de "voltar": abandona a ação e retorna ao menu.

    Deriva de Exception, como a documentação do Python recomenda para
    exceções próprias. Por isso executar() a captura antes do
    "except Exception" genérico, que a confundiria com um erro.
    """


class SairDoPrograma(Exception):
    """Pedido de "sair": encerra o programa de qualquer tela."""


def pedir_voltar():
    """Atende "voltar"."""
    raise VoltarAoMenu


def pedir_saida():
    """Atende "sair"."""
    raise SairDoPrograma


def limpar_tela():
    """Atende "limpar": limpa o terminal com o comando do sistema."""
    os.system("cls" if os.name == "nt" else "clear")


def mostrar_ajuda():
    """Atende "ajuda": lista os comandos a partir de COMANDOS."""
    print("\n  " + cores.titulo("Comandos aceitos em qualquer pergunta:"))
    for palavras, _, efeito in COMANDOS:
        nomes = ", ".join(palavras).ljust(9)
        print(f"    {cores.destaque(nomes)} {efeito}")
    # "lista" fica fora de COMANDOS: só vale nas perguntas de ID.
    print(f"    {cores.destaque('lista'.ljust(9))} nas perguntas de ID, "
          "mostra os registros e pergunta de novo")
    print("  " + cores.discreto(
        "O que ainda não foi gravado é descartado ao voltar ou sair.") + "\n")


# Fonte única dos comandos: a mesma tabela decide o que cada palavra
# faz e monta o texto da ajuda, então comando novo é uma linha aqui.
# Só a resposta inteira vale como comando: "Sair do sistema" continua
# sendo uma descrição normal.
COMANDOS = (
    (("voltar",), pedir_voltar, "abandona a tela atual e volta ao menu"),
    (("sair",), pedir_saida, "fecha o programa"),
    (("limpar",), limpar_tela, "limpa a tela"),
    (("ajuda", "?"), mostrar_ajuda, "mostra esta lista"),
)

# Palavra digitada -> função, montado da tabela acima: "?" e "ajuda"
# apontam para a mesma função.
_FUNCAO_DO_COMANDO = {palavra: funcao
                      for palavras, funcao, _ in COMANDOS
                      for palavra in palavras}


def ler_resposta(mensagem, depois_de_limpar=None):
    """Lê uma linha do teclado e atende os comandos globais.

    Devolve o texto digitado quando ele não é comando. Maiúsculas não
    importam: "SAIR" e "sair" são o mesmo comando. Com
    depois_de_limpar, essa função redesenha a tela depois de "limpar"
    (o menu usa isso para não sumir).
    """
    while True:
        valor = input(mensagem).strip()
        comando = _FUNCAO_DO_COMANDO.get(valor.casefold())
        if comando is None:
            return valor
        comando()  # voltar e sair levantam exceção e não retornam
        if comando is limpar_tela and depois_de_limpar is not None:
            depois_de_limpar()


def ler_texto(mensagem, obrigatorio=True):
    """Lê um texto; se obrigatório, repete a pergunta até vir algo.

    Recusa caracteres de controle, como ESC: gravados, eles alterariam
    o terminal toda vez que o texto fosse exibido.
    """
    while True:
        valor = ler_resposta(mensagem)
        if not valor.isprintable():
            print("  " + cores.erro("! Use apenas caracteres visíveis."))
        elif valor or not obrigatorio:
            return valor
        else:
            print("  " + cores.erro("! Este campo não pode ficar vazio."))


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
            print("  " + cores.erro("! Use pelo menos uma letra."))
            continue
        pergunta = f'  "{valor}" ficou curto. É isso mesmo?'
        if len(valor) < MINIMO_SEM_CONFIRMAR and not confirmar(pergunta):
            continue
        return valor


def ler_inteiro(mensagem, opcional=False, mostrar_lista=None):
    """Lê um número inteiro, repetindo a pergunta até vir um válido.

    Com opcional=True, Enter vazio devolve None (manter o valor atual).
    Com mostrar_lista, a resposta "lista" chama essa função (que mostra
    os registros) e repete a pergunta.
    """
    while True:
        bruto = ler_resposta(mensagem)
        if not bruto and opcional:
            return None
        if mostrar_lista is not None and bruto.casefold() == "lista":
            mostrar_lista()
            continue
        try:
            return int(bruto)
        except ValueError:
            print("  " + cores.erro("! Digite apenas números."))


def ler_enum(mensagem, classe_enum, opcional=False):
    """Mostra as opções do Enum e só aceita um código da lista.

    Com opcional=True, Enter vazio devolve None.
    """
    print(f"\n{mensagem}")
    for item in classe_enum:
        print(f"    {cores.destaque(str(item.value))} - {item.rotulo}")

    while True:
        codigo = ler_inteiro("  Código: ", opcional=opcional)
        if codigo is None:
            return None
        try:
            return classe_enum(codigo)
        except ValueError:
            print("  " + cores.erro(
                "! Código inválido. Escolha um da lista acima."))


def confirmar(mensagem):
    """Devolve True se o usuário responder 's' ou 'sim'."""
    resposta = ler_resposta(f"{mensagem} (s/N): ")
    return resposta.lower() in ("s", "sim")


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
        print("  " + cores.erro(f"! Hostname inválido: {problema}."))


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
    cabecalho = ("ID", "HOSTNAME", "TIPO", "RESPONSÁVEL", "LOTAÇÃO",
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

    # Pinta a linha já montada, para não afetar as larguras.
    titulos = linha_da_tabela(cabecalho, larguras, a_direita)
    print("\n" + cores.pintar(titulos, cores.NEGRITO))
    tracos = "-" * (sum(larguras) + 2 * (len(larguras) - 1))
    print("  " + cores.discreto(tracos))
    for linha in linhas:
        print(linha_da_tabela(linha, larguras, a_direita))


def ler_id_ativo(base_ativos, base_falhas, mensagem="  ID do ativo: "):
    """Lê o ID de um ativo; "lista" mostra a tabela e repete."""
    def listar():
        if not base_ativos:
            print("\n  " + cores.aviso("Nenhum ativo cadastrado ainda.\n"))
            return
        mostrar_tabela(base_falhas, sorted(base_ativos.items()))
        print()

    return ler_inteiro(mensagem, mostrar_lista=listar)


def ler_id_falha(base_ativos, base_falhas):
    """Lê o ID de uma falha; "lista" mostra todas e pergunta de novo."""
    def listar():
        if not base_falhas:
            print("\n  " + cores.aviso(
                "Nenhuma vulnerabilidade cadastrada ainda.\n"))
            return
        print()
        imprimir_falhas(sorted(base_falhas.items()), base_ativos)

    return ler_inteiro("  ID da vulnerabilidade: ", mostrar_lista=listar)


def mostrar_ativo(id_ativo, registro):
    """Mostra a ficha de um ativo."""
    print(f"\n  ID ............ {id_ativo}")
    print(f"  Hostname ...... {registro['hostname']}")
    print(f"  Responsável ... {registro['custodiante']}")
    print(f"  Lotação ....... {registro['lotacao']}")
    print(f"  Tipo .......... {registro['categoria'].rotulo}")
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
    nivel, estado = registro["gravidade"], registro["situacao"]
    print(f"  Severidade .... {cores.gravidade(nivel.rotulo, nivel)}")
    print(f"  Status ........ {cores.situacao(estado.rotulo, estado)}")


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
        estado = registro["situacao"]
        legenda = (f"{cores.situacao(estado.rotulo, estado)} · "
                   f"{registro['origem'].rotulo}")
        if base_ativos is not None:
            hostname = base_ativos[registro["ativo_id"]]["hostname"]
            legenda = f"{hostname} · {legenda}"
        # Alinha a severidade antes de pintar, para a coluna não andar.
        nivel = registro["gravidade"]
        severidade = cores.gravidade(f"{nivel.rotulo.upper():<9}", nivel)
        print(f"    {severidade} "
              f"{marcador:<{largura_id}} {registro['descricao']}")
        print(f"    {'':<9} {'':<{largura_id}} {legenda}\n")


def mostrar_falhas(base_falhas, id_ativo):
    """Mostra as falhas do ativo (requisito 8)."""
    encontradas = falhas.listar_por_ativo(base_falhas, id_ativo)

    if not encontradas:
        print("\n  " + cores.aviso(
            "Este ativo está sem vulnerabilidades registradas."))
        return

    print(f"\n  Vulnerabilidades ({len(encontradas)}), da mais grave:\n")
    imprimir_falhas(encontradas)


def cadastrar_falha_para(base_ativos, base_falhas, id_ativo):
    """Pergunta os campos de uma vulnerabilidade, registra e grava.

    Usada no cadastro do ativo (requisito 3) e na opção 6 (requisito
    7), para as duas telas se comportarem igual.
    """
    descricao = ler_campo("  Descrição da vulnerabilidade: ")
    origem = ler_enum("  Categoria:", OrigemFalha)
    gravidade = ler_enum("  Severidade:", NivelGravidade)
    situacao = ler_enum("  Status:", SituacaoTratamento)

    id_falha = falhas.cadastrar(base_falhas, id_ativo, descricao,
                                origem, gravidade, situacao)
    arquivo.salvar(base_ativos, base_falhas)
    print("\n  " + cores.sucesso(f"Vulnerabilidade {id_falha} registrada."))


def acao_cadastrar_ativo(base_ativos, base_falhas):
    """Opção 1: cadastra um ativo e as falhas iniciais (requisito 3)."""
    print("\n" + cores.titulo("--- CADASTRAR ATIVO ---") + "\n")
    hostname = ler_hostname("  Hostname: ", base_ativos)
    custodiante = ler_campo("  Responsável: ")
    lotacao = ler_campo("  Lotação (setor): ")
    descricao = ler_campo("  Descrição: ")
    categoria = ler_enum("  Tipo de ativo:", CategoriaAtivo)

    try:
        id_novo = ativos.cadastrar(base_ativos, hostname, custodiante,
                                   lotacao, descricao, categoria)
    except ValueError as erro:
        print("\n  " + cores.erro(f"! {erro}"))
        return

    arquivo.salvar(base_ativos, base_falhas)
    print("\n  " + cores.sucesso(f"Ativo cadastrado com o ID {id_novo}."))

    # A lista inicial de vulnerabilidades do requisito 3.
    while confirmar("\n  Cadastrar uma vulnerabilidade para este ativo?"):
        cadastrar_falha_para(base_ativos, base_falhas, id_novo)


def acao_listar_todos(base_ativos, base_falhas):
    """Opção 2: mostra todos os ativos em tabela."""
    print("\n" + cores.titulo("--- ATIVOS CADASTRADOS ---"))

    if not base_ativos:
        print("\n  " + cores.aviso("Nenhum ativo cadastrado ainda."))
        return

    mostrar_tabela(base_falhas, sorted(base_ativos.items()))
    # No fim, porque numa lista longa o título já saiu da tela.
    print(f"\n  Total: {len(base_ativos)} ativo(s).")


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
    print("\n" + cores.titulo("--- BUSCAR ATIVO ---") + "\n")
    print(f"    {cores.destaque('1')} - Por ID")
    print(f"    {cores.destaque('2')} - Por hostname")
    print(f"    {cores.destaque('3')} - Por responsável")
    print(f"    {cores.destaque('4')} - Por lotação")
    print(f"    {cores.destaque('5')} - Por tipo")
    opcao = ler_inteiro("  Opção: ")

    if opcao == 1:
        id_ativo = ler_id_ativo(base_ativos, base_falhas, "  ID: ")
        registro = ativos.buscar_por_id(base_ativos, id_ativo)
        encontrados = []
        if registro is not None:
            encontrados.append((id_ativo, registro))
    elif opcao in BUSCAS_POR_TEXTO:
        campo, pergunta = BUSCAS_POR_TEXTO[opcao]
        termo = ler_texto(pergunta)
        encontrados = ativos.buscar_por_texto(base_ativos, campo, termo)
    elif opcao == 5:
        categoria = ler_enum("  Tipo de ativo:", CategoriaAtivo)
        encontrados = ativos.buscar_por_categoria(base_ativos, categoria)
    else:
        print("\n  " + cores.erro("! Opção inválida."))
        return

    if not encontrados:
        print("\n  " + cores.erro("! Nenhum ativo encontrado."))
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
    print("\n" + cores.titulo("--- ATUALIZAR ATIVO ---") + "\n")
    id_ativo = ler_id_ativo(base_ativos, base_falhas)
    registro = ativos.buscar_por_id(base_ativos, id_ativo)
    if registro is None:
        print("\n  " + cores.erro(f"! Nenhum ativo com o ID {id_ativo}."))
        return

    mostrar_ativo(id_ativo, registro)
    print("\n  Deixe em branco para manter o valor atual.\n")

    alteracoes = {}

    novo = ler_hostname(f"  Hostname [{registro['hostname']}]: ",
                        base_ativos, ignorar_id=id_ativo,
                        obrigatorio=False)
    if novo:
        alteracoes["hostname"] = novo

    novo = ler_campo(f"  Responsável [{registro['custodiante']}]: ",
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
        print("\n  " + cores.aviso("Nada foi alterado."))
        return

    try:
        ativos.atualizar(base_ativos, id_ativo, alteracoes)
    except ValueError as erro:
        print("\n  " + cores.erro(f"! {erro}"))
        return

    arquivo.salvar(base_ativos, base_falhas)
    print("\n  " + cores.sucesso(
        f"Ativo atualizado ({len(alteracoes)} campo(s))."))


def acao_excluir(base_ativos, base_falhas):
    """Opção 5: exclui o ativo e, em cascata, as falhas dele.

    Requisito 6. A cascata fica aqui porque é o main.py que coordena
    ativos.py e falhas.py.
    """
    print("\n" + cores.titulo("--- EXCLUIR ATIVO ---") + "\n")
    id_ativo = ler_id_ativo(base_ativos, base_falhas)
    registro = ativos.buscar_por_id(base_ativos, id_ativo)
    if registro is None:
        print("\n  " + cores.erro(f"! Nenhum ativo com o ID {id_ativo}."))
        return

    mostrar_ativo(id_ativo, registro)
    mostrar_falhas(base_falhas, id_ativo)

    if not confirmar("\n  Confirma a exclusão do ativo e das falhas dele?"):
        print("\n  " + cores.aviso("Exclusão cancelada."))
        return

    # Falhas primeiro: se algo der errado no meio, não sobra falha
    # apontando para ativo inexistente.
    removidas = falhas.excluir_por_ativo(base_falhas, id_ativo)
    ativos.excluir(base_ativos, id_ativo)

    arquivo.salvar(base_ativos, base_falhas)
    print("\n  " + cores.sucesso(
        f"Ativo excluído, junto com {removidas} vulnerabilidade(s)."))


def acao_cadastrar_falha(base_ativos, base_falhas):
    """Opção 6: cadastra uma vulnerabilidade num ativo (requisito 7)."""
    print("\n" + cores.titulo("--- CADASTRAR VULNERABILIDADE ---") + "\n")
    id_ativo = ler_id_ativo(base_ativos, base_falhas)

    # falhas.py não recebe os ativos; a existência é conferida aqui.
    if ativos.buscar_por_id(base_ativos, id_ativo) is None:
        print("\n  " + cores.erro(f"! Nenhum ativo com o ID {id_ativo}."))
        return

    cadastrar_falha_para(base_ativos, base_falhas, id_ativo)


def acao_ver_falhas(base_ativos, base_falhas):
    """Opção 7: mostra o ativo e as falhas dele (requisito 8)."""
    print("\n" + cores.titulo("--- VULNERABILIDADES DE UM ATIVO ---") + "\n")
    id_ativo = ler_id_ativo(base_ativos, base_falhas)
    registro = ativos.buscar_por_id(base_ativos, id_ativo)
    if registro is None:
        print("\n  " + cores.erro(f"! Nenhum ativo com o ID {id_ativo}."))
        return

    mostrar_ativo(id_ativo, registro)
    mostrar_falhas(base_falhas, id_ativo)


def acao_atualizar_falha(base_ativos, base_falhas):
    """Opção 8: corrige uma vulnerabilidade já cadastrada.

    Mesma mecânica da opção 4: Enter mantém o valor atual. Serve também
    para mudar só a situação do tratamento.
    """
    print("\n" + cores.titulo("--- ATUALIZAR VULNERABILIDADE ---") + "\n")
    id_falha = ler_id_falha(base_ativos, base_falhas)

    if id_falha not in base_falhas:
        print("\n  " + cores.erro(
            f"! Nenhuma vulnerabilidade com o ID {id_falha}."))
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
        f"  Status (atual: {registro['situacao'].rotulo})"
        " - Enter para manter:",
        SituacaoTratamento, opcional=True)
    if nova_situacao is not None:
        alteracoes["situacao"] = nova_situacao

    if not alteracoes:
        print("\n  " + cores.aviso("Nada foi alterado."))
        return

    try:
        falhas.atualizar(base_falhas, id_falha, alteracoes)
    except ValueError as erro:
        print("\n  " + cores.erro(f"! {erro}"))
        return

    arquivo.salvar(base_ativos, base_falhas)
    print("\n  " + cores.sucesso(
        f"Vulnerabilidade atualizada ({len(alteracoes)} campo(s))."))


def acao_excluir_falha(base_ativos, base_falhas):
    """Opção 9: exclui uma vulnerabilidade cadastrada por engano.

    Falha resolvida deve ser marcada como Corrigida (opção 8), não
    excluída, para não perder o histórico; a tela avisa isso.
    """
    print("\n" + cores.titulo("--- EXCLUIR VULNERABILIDADE ---") + "\n")
    id_falha = ler_id_falha(base_ativos, base_falhas)

    if id_falha not in base_falhas:
        print("\n  " + cores.erro(
            f"! Nenhuma vulnerabilidade com o ID {id_falha}."))
        return

    mostrar_falha(id_falha, base_falhas[id_falha], base_ativos)

    print("\n  " + cores.aviso(
        "Atenção: exclua apenas cadastro errado ou duplicado."))
    print("  " + cores.aviso(
        "Se a vulnerabilidade foi resolvida, use a opção 8 e marque"))
    print("  " + cores.aviso(
        "como Corrigida - apagar destrói o histórico."))

    if not confirmar("\n  Confirma a exclusão?"):
        print("\n  " + cores.aviso("Exclusão cancelada."))
        return

    falhas.excluir(base_falhas, id_falha)
    arquivo.salvar(base_ativos, base_falhas)
    print("\n  " + cores.sucesso("Vulnerabilidade excluída."))


def resumo_por_severidade(lista_falhas):
    """Monta a linha "Crítica 6 · Alta 21 · ..." com a contagem.

    Só aparecem as severidades presentes na lista, da mais grave para
    a menos grave.
    """
    contagem = {}
    for _, registro in lista_falhas:
        nivel = registro["gravidade"]
        contagem[nivel] = contagem.get(nivel, 0) + 1

    mais_grave_primeiro = sorted(contagem, key=lambda nivel: nivel.value,
                                 reverse=True)
    partes = [cores.gravidade(f"{nivel.rotulo} {contagem[nivel]}", nivel)
              for nivel in mais_grave_primeiro]
    return " · ".join(partes)


def acao_pendentes(base_ativos, base_falhas):
    """Opção 10: lista as falhas pendentes de todos os ativos.

    Vai além do enunciado: mostra o que corrigir primeiro sem abrir a
    ficha de cada ativo.
    """
    print("\n" + cores.titulo("--- VULNERABILIDADES PENDENTES ---"))
    pendentes = falhas.listar_pendentes(base_falhas)

    if not pendentes:
        print("\n  " + cores.sucesso(
            "Nenhuma vulnerabilidade aberta ou em tratamento."))
        return

    print(f"\n  {len(pendentes)} aberta(s) ou em tratamento, da mais grave:")
    print("  " + resumo_por_severidade(pendentes) + "\n")
    imprimir_falhas(pendentes, base_ativos)


# Número da opção -> função que a executa. Substitui uma cadeia de
# if/elif: ligar uma opção nova custa uma linha aqui e uma em
# OPCOES_MENU.
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


# Texto de cada opção, na ordem do menu. A opção 0 fica por último.
OPCOES_MENU = (
    (1, "Cadastrar ativo"),
    (2, "Listar todos os ativos"),
    (3, "Buscar ativo (por ID, hostname, responsável...)"),
    (4, "Atualizar ativo"),
    (5, "Excluir ativo (e suas vulnerabilidades)"),
    (6, "Cadastrar vulnerabilidade"),
    (7, "Ver vulnerabilidades de um ativo"),
    (8, "Atualizar vulnerabilidade"),
    (9, "Excluir vulnerabilidade"),
    (10, "Vulnerabilidades pendentes (todas, da mais grave)"),
    (0, "Sair"),
)


def exibir_menu():
    """Mostra o menu, com os números alinhados à direita.

    O número é alinhado antes de ser pintado: os códigos de cor contam
    como caracteres e desalinhariam a coluna.
    """
    print("\n" + cores.discreto("=" * 62))
    for numero, texto in OPCOES_MENU:
        print(f"  {cores.destaque(f'{numero:>2}')} - {texto}")
    print(cores.discreto("=" * 62))
    print(cores.discreto("  Em qualquer pergunta: voltar · sair · limpar · "
                         "ajuda"))


def ler_opcao_do_menu():
    """Lê a opção do menu principal.

    Aqui "limpar" limpa a tela e desenha o menu de novo, e "voltar" não
    tem para onde voltar: a pergunta só se repete.
    """
    while True:
        try:
            bruto = ler_resposta("  Opção: ", depois_de_limpar=exibir_menu)
        except VoltarAoMenu:
            continue
        try:
            return int(bruto)
        except ValueError:
            print("  " + cores.erro("! Digite apenas números."))


def pausar():
    """Espera o Enter antes de o menu voltar, para o resultado ser lido.

    Sem a pausa, o menu seria impresso logo abaixo do resultado e
    empurraria o começo de uma listagem longa para fora da tela. Com a
    entrada vinda de um arquivo (testes automáticos), não há quem leia
    e a pausa é pulada.
    """
    if not sys.stdin.isatty():
        return
    try:
        ler_resposta(cores.discreto("\n  Enter para voltar ao menu... "))
    except VoltarAoMenu:
        pass  # "voltar" aqui é o próprio Enter


def main():
    """Carrega a base e repete o menu até o usuário escolher 0."""
    cores.ativar()
    print("\n" + cores.titulo("=" * 62))
    print(cores.titulo("  INVENTÁRIO DE ATIVOS E VULNERABILIDADES"))
    print(cores.titulo("=" * 62))

    # A base é lida uma vez; cada alteração é gravada na hora.
    base_ativos, base_falhas = arquivo.carregar()
    print(f"\n  Base carregada: {len(base_ativos)} ativo(s), "
          f"{len(base_falhas)} vulnerabilidade(s).")

    try:
        while True:
            exibir_menu()
            opcao = ler_opcao_do_menu()

            if opcao == 0:
                break

            acao = ACOES.get(opcao)
            if acao is None:
                print("\n  " + cores.erro(
                    "! Opção inexistente. Escolha um número do menu."))
                continue

            base_ativos, base_falhas = executar(acao, base_ativos,
                                                base_falhas)
    except SairDoPrograma:
        pass  # "sair" digitado em qualquer pergunta

    print("\n  " + cores.titulo("Até logo.") + "\n")


def executar(acao, base_ativos, base_falhas):
    """Executa uma ação do menu e devolve a base a usar dali em diante.

    Ponto de isolamento (requisito 1): um erro inesperado não derruba o
    programa, e a base é recarregada, porque a ação pode ter parado
    entre a memória e o disco. "voltar" não precisa recarregar: as
    ações só mexem na base depois da última pergunta.
    """
    # A ordem dos except importa: o Python usa o primeiro que servir.
    # Os pedidos do usuário vêm antes do "except Exception" genérico,
    # senão "voltar" e "sair" seriam tratados como erro inesperado.
    try:
        acao(base_ativos, base_falhas)
    except VoltarAoMenu:
        # Sem pausa: o usuário acabou de pedir para voltar.
        print("\n  " + cores.aviso(
            "Voltando ao menu. O que não foi gravado foi descartado."))
        return base_ativos, base_falhas
    except (SairDoPrograma, EOFError):
        raise  # EOFError: Ctrl+Z ou Ctrl+D, encerramento limpo
    except Exception as erro:
        # O tipo diz o que houve mesmo quando a mensagem é curta: um
        # KeyError('x') sozinho apareceria só como "'x'".
        print("\n  " + cores.erro(
            f"! Erro inesperado ({type(erro).__name__}): {erro}"))
        base_ativos, base_falhas = arquivo.carregar()
        print("  " + cores.erro(
            "! Base recarregada do disco: o que não chegou a ser "
            "gravado foi descartado."))
    pausar()
    return base_ativos, base_falhas


if __name__ == "__main__":
    try:
        main()
    except arquivo.BaseInvalida as erro:
        # Não abre base ruim: a primeira gravação apagaria o original.
        print("\n  " + cores.erro(
            f"! Não foi possível carregar a base de dados: {erro}"))
        print("  " + cores.erro(f"! Arquivo: {arquivo.ARQUIVO_DADOS}"))
        print("  " + cores.erro(
            "! O programa para aqui, para não sobrescrever dados bons."))
        print("  " + cores.erro(
            "! Corrija o arquivo, ou mova-o para fora da pasta"))
        print(cores.erro("    e o programa começa uma base nova.") + "\n")
    except (KeyboardInterrupt, EOFError):
        print("\n\n  Encerrado pelo usuário.\n")
