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


class BaseInvalida(Exception):
    """
    A base em disco não pode ser carregada: está ilegível, corrompida ou
    foi adulterada.

    Crio uma exceção própria para separar "o arquivo de dados está ruim" de
    qualquer outro erro do Python. Assim o main.py consegue tratar só este
    caso e dar uma mensagem útil, em vez de despejar um traceback.
    """


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
        # flush() tira o texto da memória do Python; fsync() obriga o
        # sistema a gravar no disco de verdade. Sem os dois, o sistema pode
        # registrar a troca de nome abaixo antes do conteúdo - e, numa queda
        # de energia, o inventario.json voltaria vazio.
        f.flush()
        os.fsync(f.fileno())
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


def _exige_inteiro(valor, nome):
    """
    Confere que o valor é um número inteiro de verdade.

    isinstance(valor, int) sozinho não basta: True e False também passam,
    porque em Python bool é um tipo de int. E um contador 10.0 (float)
    geraria o id 11.0, gravado como "11.0" - que a própria carga recusaria
    na próxima vez que o programa abrisse.

    Levanta TypeError, que a carga já converte em BaseInvalida.
    """
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise TypeError(f"{nome} deveria ser um número inteiro, veio {valor!r}")


def _chave_para_id(chave):
    """
    Converte a chave do JSON ("7") de volta para o id inteiro (7).

    Exijo exatamente a forma que o salvar() escreve. O int() sozinho aceita
    "07", " 7" e "+7" - e aí "7" e "07" virariam o mesmo id, um registro
    apagando o outro em silêncio. Id zero ou negativo o programa nunca gera,
    então também é sinal de arquivo mexido à mão.

    Levanta ValueError, que a carga já converte em BaseInvalida.
    """
    numero = int(chave)
    if str(numero) != chave or numero < 1:
        raise ValueError(f"id fora do formato: {chave!r}")
    return numero


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

    # utf-8-sig lê o arquivo com ou sem BOM - a marca invisível que o Bloco
    # de Notas e o PowerShell às vezes põem no início. Para gravar, o
    # salvar() continua usando utf-8 puro.
    try:
        with open(ARQUIVO_DADOS, "r", encoding="utf-8-sig") as f:
            dados = json.load(f)
    except OSError as erro:
        raise BaseInvalida(f"não foi possível abrir o arquivo ({erro})") from erro
    except UnicodeDecodeError as erro:
        # Arquivo salvo em outra codificação (ANSI, UTF-16...). Este except
        # vem ANTES do próximo porque UnicodeDecodeError é um tipo de
        # ValueError - na ordem inversa, ele nunca seria alcançado.
        raise BaseInvalida("o arquivo não está em UTF-8 - foi salvo em "
                           "outra codificação") from erro
    except (ValueError, RecursionError) as erro:
        # ValueError cobre o JSON mal escrito (JSONDecodeError é um tipo de
        # ValueError) e número com milhares de dígitos. RecursionError: um
        # arquivo com milhares de colchetes aninhados estoura o leitor.
        raise BaseInvalida(f"não é um JSON válido ({erro})") from erro

    # A conversão inteira vai dentro de um try. Campo faltando, código de Enum
    # inválido, id fora do formato ou vulnerabilidade sem equipamento levam
    # todos à mesma conclusão: a base não está confiável. Não adianta tratar
    # cada um de um jeito diferente.
    #
    # Uso dados["equipamentos"] e não dados.get(...): com o .get(), um arquivo
    # sem essa chave carregaria como base vazia, e a primeira gravação apagaria
    # tudo em silêncio. Falta de chave tem que ser erro.
    try:
        equipamentos = {}
        for chave, registro in dados["equipamentos"].items():
            item = {
                "hostname":    registro["hostname"],
                "custodiante": registro["custodiante"],
                "lotacao":     registro["lotacao"],
                "descricao":   registro["descricao"],
                "categoria":   CategoriaEquipamento(registro["categoria"]),
            }
            _exige_texto(item, ("hostname", "custodiante",
                                "lotacao", "descricao"))
            # O JSON devolve a chave como texto; ela volta a ser o id
            # inteiro (ver salvar() e _chave_para_id()).
            equipamentos[_chave_para_id(chave)] = item

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
            _exige_inteiro(item["equipamento_id"], "equipamento_id")
            # Integridade referencial: toda vulnerabilidade tem de apontar
            # para um equipamento que existe. Órfã, ela não apareceria em tela
            # nenhuma - e seria "herdada" pelo equipamento que um dia
            # recebesse aquele id.
            if item["equipamento_id"] not in equipamentos:
                raise ValueError(
                    f"a vulnerabilidade {chave} aponta para o equipamento "
                    f"{item['equipamento_id']}, que não existe")
            falhas[_chave_para_id(chave)] = item
        # Restaura a marca d'água. Isto fica DENTRO do try de propósito: um
        # contador adulterado ("abc", null, 10.0) é recusado pelo
        # _exige_inteiro(), e aí a base inteira é recusada como qualquer
        # outro conteúdo fora do formato. Fora do try, esse erro escaparia e
        # derrubaria o programa - foi o defeito que esta parte já teve.
        #
        # Uso .get() com reserva, ao contrário de dados["equipamentos"]:
        # arquivo antigo, gravado antes deste recurso existir, não tem esta
        # chave, e a reserva (o maior id que existe) é exatamente o
        # comportamento que o programa tinha antes. Falta de contador não
        # corrompe nada; falta de "equipamentos" corromperia.
        ultimo_equipamento = dados.get("ultimo_id_equipamento", 0)
        ultimo_falha = dados.get("ultimo_id_falha", 0)
        _exige_inteiro(ultimo_equipamento, "ultimo_id_equipamento")
        _exige_inteiro(ultimo_falha, "ultimo_id_falha")
        _marca_alta["equipamentos"] = max(ultimo_equipamento,
                                          max(equipamentos, default=0))
        _marca_alta["falhas"] = max(ultimo_falha, max(falhas, default=0))
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

    # --- bases adulteradas: todas recusadas com mensagem, nenhum traceback ---
    # Cada valor é o conteúdo exato do arquivo, em bytes.
    bom = {"hostname": "PC-01", "custodiante": "A", "lotacao": "B",
           "descricao": "C", "categoria": 1}
    orfa = {"equipamento_id": 9, "descricao": "D",
            "origem": 1, "gravidade": 1, "situacao": 1}
    adulteradas = {
        "id '01'": json.dumps({"equipamentos": {"01": bom},
                               "falhas": {}}).encode(),
        "contador 10.0": json.dumps({"equipamentos": {}, "falhas": {},
                                     "ultimo_id_equipamento": 10.0}).encode(),
        "falha órfã": json.dumps({"equipamentos": {"1": bom},
                                  "falhas": {"1": orfa}}).encode(),
        # Salvo em ANSI, como o Bloco de Notas antigo faz: o "ó" vira um
        # byte que não existe em UTF-8.
        "salva em ANSI": '{"lotacao": "Cartório"}'.encode("cp1252"),
    }
    print()
    for nome, conteudo in adulteradas.items():
        with open(ARQUIVO_DADOS, "wb") as f:
            f.write(conteudo)
        try:
            carregar()
            raise AssertionError(f"aceitou a base adulterada: {nome}")
        except BaseInvalida as erro:
            print(f"Recusada ({nome}): {erro}")
    print("\nOK - base adulterada é recusada com mensagem, sem traceback.")

    os.remove(ARQUIVO_DADOS)   # limpa o arquivo de teste
    print("\nA base real (inventario.json) não foi tocada.")
