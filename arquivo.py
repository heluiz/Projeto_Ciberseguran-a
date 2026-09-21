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
    dados = {"equipamentos": {}, "falhas": {}}

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
            equipamentos[int(chave)] = {
                "hostname":    registro["hostname"],
                "custodiante": registro["custodiante"],
                "lotacao":     registro["lotacao"],
                "descricao":   registro["descricao"],
                "categoria":   CategoriaEquipamento(registro["categoria"]),
            }

        falhas = {}
        for chave, registro in dados["falhas"].items():
            falhas[int(chave)] = {
                "equipamento_id": registro["equipamento_id"],
                "descricao":      registro["descricao"],
                "origem":         OrigemFalha(registro["origem"]),
                "gravidade":      NivelGravidade(registro["gravidade"]),
                "situacao":       SituacaoTratamento(registro["situacao"]),
            }
    except (KeyError, ValueError, TypeError, AttributeError) as erro:
        raise BaseInvalida(
            f"conteúdo fora do formato esperado "
            f"({type(erro).__name__}: {erro})") from erro

    return equipamentos, falhas


def proximo_id(colecao):
    """
    Próximo identificador livre: dicionário vazio devolve 1, senão maior + 1.

    Não reaproveito id de registro excluído de propósito. Se o equipamento 3
    foi apagado e eu desse 3 para o próximo, qualquer anotação feita fora do
    sistema apontando para "equipamento 3" passaria a apontar para a coisa
    errada.
    """
    if not colecao:
        return 1
    return max(colecao) + 1


# ===========================================================================
# Teste rápido: grava, lê de volta e confere que nada se perdeu no caminho.
# ===========================================================================
if __name__ == "__main__":
    equipamentos = {
        1: {"hostname":    "PC-CARTORIO-01",
            "custodiante": "Escrivao de plantao",
            "lotacao":     "Cartorio",
            "descricao":   "Estacao de atendimento ao publico",
            "categoria":   CategoriaEquipamento.ESTACAO_TRABALHO},
    }
    falhas = {
        1: {"equipamento_id": 1,
            "descricao":      "Sistema operacional sem atualizacao ha 8 meses",
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
    print(f"  proximo id livre: {proximo_id(lidos_equip)}")

    # assert: se a comparação for falsa, o programa para e avisa.
    # É a forma mais curta de testar que salvar() e carregar() são de fato
    # operações inversas uma da outra.
    assert lidos_equip == equipamentos, "os dados lidos diferem dos gravados"
    assert lidos_falhas == falhas, "as falhas lidas diferem das gravadas"
    print("\nOK - o que saiu e o que voltou sao identicos.")