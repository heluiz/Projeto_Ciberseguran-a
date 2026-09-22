"""
arquivo.py
----------
Cuida de gravar e ler a base de dados em disco.

Por que separar isso dos outros módulos?
Porque é a única parte do programa que conversa com o disco. Se um dia eu
trocar JSON por CSV, ou por um banco de dados de verdade, mexo só aqui -
equipamentos.py e falhas.py nem ficam sabendo que mudou.

Atende aos requisitos 3 e 9.
"""

import json
import os

from classificacoes import (
    CategoriaEquipamento,
    OrigemFalha,
    NivelGravidade,
    SituacaoTratamento,
)


# ===========================================================================
# ONDE O ARQUIVO FICA
#
# Se eu escrevesse só "inventario.json", o Python criaria o arquivo na pasta
# de onde o programa foi CHAMADO, não na pasta onde o código está. Rodando de
# lugares diferentes eu acabaria com bases diferentes sem perceber - foi
# exatamente o risco que corri quando o terminal estava na pasta do VS Code.
#
# __file__ é o caminho deste próprio arquivo. Pegando a pasta dele, o
# inventario.json fica sempre ao lado do código, rode eu de onde rodar.
class BaseInvalida(Exception):
    """
    A base em disco está corrompida ou foi adulterada.

    Crio uma exceção própria para separar "o arquivo de dados está ruim" de
    qualquer outro erro do Python. Assim o main.py consegue tratar só este
    caso e dar uma mensagem útil, em vez de despejar um traceback.
    """


# ===========================================================================
PASTA_DO_PROJETO = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_DADOS = os.path.join(PASTA_DO_PROJETO, "inventario.json")


# ===========================================================================
# MARCA D'ÁGUA DOS IDENTIFICADORES
#
# Guarda o MAIOR id já entregue para cada coleção - não o maior que existe
# agora, e sim o maior que já existiu. É o que impede um id de ser
# reaproveitado depois que o registro dele foi excluído.
#
# Por que aqui, e não dentro do dicionário de dados? Porque isto é estado
# PERSISTIDO: precisa ser gravado junto com os registros e restaurado na
# próxima execução. Este módulo é justamente o dono do que vai para o disco.
#
# Começa zerado. carregar() restaura do arquivo e salvar() grava de volta.
# ===========================================================================
_marca_alta = {"equipamentos": 0, "falhas": 0}


# ===========================================================================
# REQUISITO 3 - gravar em arquivo de texto.
#
# Uso JSON, que é arquivo de texto puro (abre no Bloco de Notas e dá para
# ler). A vantagem sobre inventar meu próprio formato com ";" ou "|" é que o
# módulo json já resolve os casos chatos: texto com vírgula, com acento, com
# quebra de linha. Menos código meu = menos bug meu.
#
# Enum não vai direto para JSON, então gravo o .value (o código inteiro).
# ===========================================================================
def salvar(equipamentos, falhas):
    # Os contadores vão junto com os registros. Uso max(...) por segurança:
    # se por algum motivo a marca estiver atrasada em relação aos ids que
    # existem, grava o maior dos dois e a base continua coerente.
    dados = {
        "equipamentos": {},
        "falhas": {},
        "ultimo_id_equipamento": max(_marca_alta["equipamentos"],
                                     max(equipamentos, default=0)),
        "ultimo_id_falha": max(_marca_alta["falhas"],
                               max(falhas, default=0)),
    }

    for id_equip, registro in equipamentos.items():
        # str(id_equip) porque JSON só aceita texto como chave.
        dados["equipamentos"][str(id_equip)] = {
            "hostname":    registro["hostname"],
            "custodiante": registro["custodiante"],
            "lotacao":     registro["lotacao"],
            "descricao":   registro["descricao"],
            "categoria":   registro["categoria"].value,   # Enum -> inteiro
        }

    for id_falha, registro in falhas.items():
        dados["falhas"][str(id_falha)] = {
            # equipamento_id é VALOR, não chave, então o JSON preserva o
            # inteiro. Só as chaves viram texto.
            "equipamento_id": registro["equipamento_id"],
            "descricao":      registro["descricao"],
            "origem":         registro["origem"].value,
            "gravidade":      registro["gravidade"].value,
            "situacao":       registro["situacao"].value,
        }

    # Gravação em duas etapas - integridade da base.
    # Escrevo num arquivo temporário e só então substituo o definitivo.
    # Se faltar energia no meio da escrita, o inventario.json antigo continua
    # inteiro: perco a última alteração, não a base toda. os.replace é
    # atômico - ou troca por completo, ou não troca.
    temporario = ARQUIVO_DADOS + ".tmp"
    with open(temporario, "w", encoding="utf-8") as f:
        # indent=4 deixa o arquivo legível para humanos (capricho).
        # ensure_ascii=False mantém os acentos como acentos, em vez de
        # virarem códigos tipo \u00e7.
        json.dump(dados, f, indent=4, ensure_ascii=False)
    os.replace(temporario, ARQUIVO_DADOS)


def _exige_texto(registro, campos):
    """
    Confere que os campos citados são mesmo texto.

    Sem isto, um "hostname": null no arquivo entraria na base sem reclamar e
    só quebraria muito depois - na primeira busca, com uma mensagem que não
    ajuda ninguém a entender a causa. Erro de dado tem que aparecer na carga,
    perto de onde nasceu.

    Levanta TypeError, que a carga já converte em BaseInvalida.
    """
    for campo in campos:
        if not isinstance(registro[campo], str):
            raise TypeError(
                f"campo '{campo}' deveria ser texto, "
                f"veio {type(registro[campo]).__name__}")


def carregar():
    """
    Devolve (equipamentos, falhas). Arquivo inexistente devolve dois vazios -
    primeira execução do programa não é erro.

    Levanta BaseInvalida se o arquivo existir mas estiver ilegível ou fora do
    formato. Prefiro recusar a abrir a carregar pela metade: com base parcial,
    a primeira gravação sobrescreveria o arquivo bom com dados incompletos.
    Perder a última alteração é aceitável; perder a base inteira não é.
    """
    if not os.path.exists(ARQUIVO_DADOS):
        return {}, {}

    try:
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except json.JSONDecodeError as erro:
        raise BaseInvalida(f"não é um JSON válido ({erro})") from erro
    except OSError as erro:
        raise BaseInvalida(f"não foi possível abrir o arquivo ({erro})") from erro

    # A conversão inteira vai dentro de um try. Campo faltando, código de Enum
    # inválido ou chave não numérica levam todos à mesma conclusão: a base não
    # está confiável. Não adianta tratar cada um de um jeito diferente.
    #
    # Uso dados["equipamentos"] e não dados.get(...): com o .get(), um arquivo
    # sem essa chave carregaria como base vazia, e a primeira gravação apagaria
    # tudo em silêncio. Falta de chave tem que ser erro.
    try:
        equipamentos = {}
        for chave, registro in dados["equipamentos"].items():
            # int(chave): o JSON devolve a chave como texto (ver salvar()).
            item = {
                "hostname":    registro["hostname"],
                "custodiante": registro["custodiante"],
                "lotacao":     registro["lotacao"],
                "descricao":   registro["descricao"],
                "categoria":   CategoriaEquipamento(registro["categoria"]),
            }
            _exige_texto(item, ("hostname", "custodiante",
                                "lotacao", "descricao"))
            equipamentos[int(chave)] = item

        falhas = {}
        for chave, registro in dados["falhas"].items():
            item = {
                "equipamento_id": registro["equipamento_id"],
                "descricao":      registro["descricao"],
                "origem":         OrigemFalha(registro["origem"]),
                "gravidade":      NivelGravidade(registro["gravidade"]),
                "situacao":       SituacaoTratamento(registro["situacao"]),
            }
            _exige_texto(item, ("descricao",))
            if not isinstance(item["equipamento_id"], int):
                raise TypeError("equipamento_id deveria ser um número inteiro")
            falhas[int(chave)] = item
        # Restaura a marca d'água. Isto fica DENTRO do try de propósito: um
        # contador adulterado ("abc", null, uma lista) faz o max() levantar
        # TypeError, e aí a base inteira é recusada como qualquer outro
        # conteúdo fora do formato. Fora do try, esse erro escaparia e
        # derrubaria o programa - foi o defeito que esta linha já teve.
        #
        # Uso .get() com reserva, ao contrário de dados["equipamentos"]:
        # arquivo antigo, gravado antes deste recurso existir, não tem esta
        # chave, e a reserva (o maior id que existe) é exatamente o
        # comportamento que o programa tinha antes. Falta de contador não
        # corrompe nada; falta de "equipamentos" corromperia.
        _marca_alta["equipamentos"] = max(dados.get("ultimo_id_equipamento", 0),
                                          max(equipamentos, default=0))
        _marca_alta["falhas"] = max(dados.get("ultimo_id_falha", 0),
                                    max(falhas, default=0))
    except (KeyError, ValueError, TypeError, AttributeError) as erro:
        raise BaseInvalida(
            f"conteúdo fora do formato esperado "
            f"({type(erro).__name__}: {erro})") from erro

    return equipamentos, falhas


def _proximo_id(colecao, nome_colecao):
    """
    Entrega um identificador que NUNCA se repete, nem depois de exclusões.

    A versão ingênua seria max(colecao) + 1. Ela tem um defeito: com {1, 2},
    apagando o 2, max({1}) + 1 devolve 2 outra vez. O número volta a
    circular, e uma anotação externa apontando para "equipamento 2" passa a
    apontar para outra máquina.

    A correção é comparar com a marca d'água - o maior id já entregue,
    lembrado mesmo depois que o registro sumiu. Comparo com o maior id
    existente também, como rede de segurança para uma base montada à mão.
    """
    maior_existente = max(colecao, default=0)
    novo = max(maior_existente, _marca_alta[nome_colecao]) + 1
    _marca_alta[nome_colecao] = novo
    return novo


def proximo_id_equipamento(equipamentos):
    """Próximo id de equipamento. Duas funções nomeadas em vez de uma com
    parâmetro de texto: a chamada fica legível e não há nome mágico solto."""
    return _proximo_id(equipamentos, "equipamentos")


def proximo_id_falha(falhas):
    """Próximo id de vulnerabilidade."""
    return _proximo_id(falhas, "falhas")


# ===========================================================================
# Teste rápido: grava, lê de volta e confere que nada se perdeu no caminho.
# ===========================================================================
if __name__ == "__main__":
    # O teste NUNCA pode tocar na base real. Sem as duas linhas abaixo, rodar
    # "python arquivo.py" para estudar sobrescrevia o inventario.json com
    # dados de exemplo - e apagava os equipamentos de verdade.
    #
    # Aponto o módulo para um arquivo na pasta temporária do sistema. Funciona
    # porque salvar() e carregar() leem ARQUIVO_DADOS na hora em que são
    # chamadas, não na hora em que foram escritas.
    import tempfile
    ARQUIVO_DADOS = os.path.join(tempfile.gettempdir(), "inventario_teste.json")

    equipamentos = {
        1: {"hostname":    "PC-CARTORIO-01",
            "custodiante": "Escrivão de plantão",
            "lotacao":     "Cartório",
            "descricao":   "Estação de atendimento ao público",
            "categoria":   CategoriaEquipamento.ESTACAO_TRABALHO},
    }
    falhas = {
        1: {"equipamento_id": 1,
            "descricao":      "Sistema operacional sem atualização há 8 meses",
            "origem":         OrigemFalha.FALTA_ATUALIZACAO,
            "gravidade":      NivelGravidade.ALTA,
            "situacao":       SituacaoTratamento.ABERTA},
    }

    salvar(equipamentos, falhas)
    print(f"Gravado em: {ARQUIVO_DADOS}\n")

    lidos_equip, lidos_falhas = carregar()

    chave = list(lidos_equip.keys())[0]
    print("Lido de volta:")
    print(f"  id {chave} - tipo {type(chave).__name__}  (tem que ser 'int')")
    print(f"  categoria: {lidos_equip[1]['categoria'].rotulo}")
    print(f"  gravidade: {lidos_falhas[1]['gravidade'].rotulo}")
    print(f"  próximo id livre: {proximo_id_equipamento(lidos_equip)}")

    # assert: se a comparação for falsa, o programa para e avisa.
    # É a forma mais curta de testar que salvar() e carregar() são de fato
    # operações inversas uma da outra.
    assert lidos_equip == equipamentos, "os dados lidos diferem dos gravados"
    assert lidos_falhas == falhas, "as falhas lidas diferem das gravadas"
    print("\nOK - o que saiu e o que voltou são idênticos.")

    # --- o id não volta a circular, nem depois de fechar o programa ---
    base = dict(lidos_equip)
    id_a = proximo_id_equipamento(base)
    base[id_a] = dict(base[1])
    del base[id_a]                      # excluiu o de maior id
    salvar(base, lidos_falhas)

    _marca_alta["equipamentos"] = 0     # simula o programa reiniciando
    base, _ = carregar()
    id_b = proximo_id_equipamento(base)

    print(f"\nEntreguei o id {id_a}, excluí o registro e reiniciei.")
    print(f"O próximo id foi {id_b} - o {id_a} não voltou a circular.")
    assert id_b > id_a, "o identificador foi reaproveitado"
    print("\nOK - identificadores não se repetem.")

    os.remove(ARQUIVO_DADOS)   # limpa o arquivo de teste
    print("\nA base real (inventario.json) não foi tocada.")