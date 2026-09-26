"""Gravação e leitura da base de dados em JSON.

Único módulo que acessa o disco: trocar o formato do arquivo mexeria
só aqui. Atende aos requisitos 3 e 9.
"""

import json
import os

from classificacoes import (
    CategoriaAtivo,
    OrigemFalha,
    NivelGravidade,
    SituacaoTratamento,
)


class BaseInvalida(Exception):
    """A base em disco está ilegível, corrompida ou adulterada."""


# Caminho absoluto: a base fica ao lado do código, de onde quer que o
# programa seja executado.
PASTA_DO_PROJETO = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_DADOS = os.path.join(PASTA_DO_PROJETO, "inventario.json")

# Maior id já entregue em cada coleção (marca d'água). Vai gravado com
# os registros, para que um id excluído nunca volte a ser usado.
_marca_alta = {"ativos": 0, "falhas": 0}


def salvar(ativos, falhas):
    """Grava ativos e falhas no arquivo JSON (requisito 3).

    A escrita vai para um arquivo temporário, que depois substitui o
    definitivo: se a gravação for interrompida, a base anterior
    continua inteira.
    """
    # A marca nunca fica abaixo do maior id existente.
    dados = {
        "ativos": {},
        "falhas": {},
        "ultimo_id_ativo": max(_marca_alta["ativos"],
                               max(ativos, default=0)),
        "ultimo_id_falha": max(_marca_alta["falhas"],
                               max(falhas, default=0)),
    }

    for id_ativo, registro in ativos.items():
        # Chave de objeto JSON é sempre texto; carregar() converte de
        # volta para inteiro.
        dados["ativos"][str(id_ativo)] = {
            "hostname": registro["hostname"],
            "custodiante": registro["custodiante"],
            "lotacao": registro["lotacao"],
            "descricao": registro["descricao"],
            "categoria": registro["categoria"].value,
        }

    for id_falha, registro in falhas.items():
        dados["falhas"][str(id_falha)] = {
            "ativo_id": registro["ativo_id"],
            "descricao": registro["descricao"],
            "origem": registro["origem"].value,
            "gravidade": registro["gravidade"].value,
            "situacao": registro["situacao"].value,
        }

    temporario = ARQUIVO_DADOS + ".tmp"
    with open(temporario, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)
        # Garante o conteúdo no disco antes da troca de nome.
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporario, ARQUIVO_DADOS)  # troca atômica


def _exige_texto(registro, campos, origem):
    """Levanta erro se algum dos campos não for texto visível.

    TypeError se o valor não for texto: um nulo no arquivo é recusado
    na carga, e não numa busca mais tarde. ValueError se o texto tiver
    caractere de controle, como ESC: é a mesma regra da digitação, que
    vale também aqui porque o arquivo pode ser editado fora do
    programa, e o caractere seria enviado ao terminal toda vez que o
    texto aparecesse na tela. origem ("ativo 3") vai na mensagem.
    """
    for campo in campos:
        valor = registro[campo]
        if not isinstance(valor, str):
            raise TypeError(
                f"{origem}: campo '{campo}' deveria ser texto, "
                f"veio {type(valor).__name__}")
        if not valor.isprintable():
            invisivel = next(c for c in valor if not c.isprintable())
            raise ValueError(
                f"{origem}: campo '{campo}' tem caractere de controle "
                f"({invisivel!r})")


def _exige_inteiro(valor, nome):
    """Levanta TypeError se o valor não for um inteiro de verdade.

    bool é subclasse de int e precisa ser recusado à parte.
    """
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise TypeError(
            f"{nome} deveria ser um número inteiro, veio {valor!r}")


def _chave_para_id(chave):
    """Devolve o id inteiro (7) que corresponde à chave do JSON ("7").

    Só aceita a forma que salvar() escreve: "07" e "7" virariam o mesmo
    id, e um registro apagaria o outro. Levanta ValueError fora disso.
    """
    numero = int(chave)
    if str(numero) != chave or numero < 1:
        raise ValueError(f"id fora do formato: {chave!r}")
    return numero


def carregar():
    """Lê a base e devolve (ativos, falhas).

    Sem arquivo, devolve dois dicionários vazios (primeira execução).
    Levanta BaseInvalida se o arquivo existir mas não puder ser lido ou
    estiver fora do formato: carregar pela metade faria a próxima
    gravação apagar os dados bons.
    """
    if not os.path.exists(ARQUIVO_DADOS):
        return {}, {}

    # utf-8-sig aceita o arquivo com ou sem BOM (Bloco de Notas).
    try:
        with open(ARQUIVO_DADOS, "r", encoding="utf-8-sig") as f:
            dados = json.load(f)
    except OSError as erro:
        raise BaseInvalida(
            f"não foi possível abrir o arquivo ({erro})") from erro
    except UnicodeDecodeError as erro:
        # Vem antes do ValueError, do qual é subclasse.
        raise BaseInvalida("o arquivo não está em UTF-8 - foi salvo em "
                           "outra codificação") from erro
    except (ValueError, RecursionError) as erro:
        # JSON malformado ou aninhado demais.
        raise BaseInvalida(f"não é um JSON válido ({erro})") from erro

    # Qualquer campo faltando ou fora do formato invalida a base
    # inteira. Por isso dados["ativos"] e não .get(): sem a chave, a
    # base seria lida vazia e a próxima gravação apagaria tudo.
    try:
        ativos = {}
        for chave, registro in dados["ativos"].items():
            item = {
                "hostname": registro["hostname"],
                "custodiante": registro["custodiante"],
                "lotacao": registro["lotacao"],
                "descricao": registro["descricao"],
                "categoria": CategoriaAtivo(registro["categoria"]),
            }
            _exige_texto(item, ("hostname", "custodiante",
                                "lotacao", "descricao"), f"ativo {chave}")
            ativos[_chave_para_id(chave)] = item

        falhas = {}
        for chave, registro in dados["falhas"].items():
            item = {
                "ativo_id": registro["ativo_id"],
                "descricao": registro["descricao"],
                "origem": OrigemFalha(registro["origem"]),
                "gravidade": NivelGravidade(registro["gravidade"]),
                "situacao": SituacaoTratamento(registro["situacao"]),
            }
            _exige_texto(item, ("descricao",), f"vulnerabilidade {chave}")
            _exige_inteiro(item["ativo_id"], "ativo_id")
            # Integridade referencial: falha sem ativo seria invisível.
            if item["ativo_id"] not in ativos:
                raise ValueError(
                    f"a vulnerabilidade {chave} aponta para o ativo "
                    f"{item['ativo_id']}, que não existe")
            falhas[_chave_para_id(chave)] = item

        # Sem contador gravado, vale o maior id existente.
        ultimo_ativo = dados.get("ultimo_id_ativo", 0)
        ultimo_falha = dados.get("ultimo_id_falha", 0)
        _exige_inteiro(ultimo_ativo, "ultimo_id_ativo")
        _exige_inteiro(ultimo_falha, "ultimo_id_falha")
        _marca_alta["ativos"] = max(ultimo_ativo, max(ativos, default=0))
        _marca_alta["falhas"] = max(ultimo_falha, max(falhas, default=0))
    except (KeyError, ValueError, TypeError, AttributeError) as erro:
        raise BaseInvalida(
            f"conteúdo fora do formato esperado "
            f"({type(erro).__name__}: {erro})") from erro

    return ativos, falhas


def _proximo_id(colecao, nome_colecao):
    """Devolve um id novo, que nunca repete um id já entregue.

    Usa a marca d'água, e não só o maior id existente: com {1, 2},
    excluir o 2 faria max() + 1 devolver 2 de novo.
    """
    maior_existente = max(colecao, default=0)
    novo = max(maior_existente, _marca_alta[nome_colecao]) + 1
    _marca_alta[nome_colecao] = novo
    return novo


def proximo_id_ativo(ativos):
    """Devolve o próximo id de ativo."""
    return _proximo_id(ativos, "ativos")


def proximo_id_falha(falhas):
    """Devolve o próximo id de vulnerabilidade."""
    return _proximo_id(falhas, "falhas")


# Teste rápido: grava, lê de volta e confere que nada se perdeu.
if __name__ == "__main__":
    import tempfile

    # O teste grava num arquivo temporário e nunca toca na base real.
    # Funciona porque salvar() e carregar() leem ARQUIVO_DADOS na hora
    # da chamada.
    ARQUIVO_DADOS = os.path.join(tempfile.gettempdir(),
                                 "inventario_teste.json")

    ativos = {
        1: {"hostname": "PC-CARTORIO-01",
            "custodiante": "Escrivão de plantão",
            "lotacao": "Cartório",
            "descricao": "Estação de atendimento ao público",
            "categoria": CategoriaAtivo.ESTACAO_TRABALHO},
    }
    falhas = {
        1: {"ativo_id": 1,
            "descricao": "Sistema operacional sem atualização há 8 meses",
            "origem": OrigemFalha.FALTA_ATUALIZACAO,
            "gravidade": NivelGravidade.ALTA,
            "situacao": SituacaoTratamento.ABERTA},
    }

    salvar(ativos, falhas)
    print(f"Gravado em: {ARQUIVO_DADOS}\n")

    lidos_ativos, lidos_falhas = carregar()

    chave = list(lidos_ativos.keys())[0]
    print("Lido de volta:")
    print(f"  id {chave} - tipo {type(chave).__name__}  (tem que ser 'int')")
    print(f"  categoria: {lidos_ativos[1]['categoria'].rotulo}")
    print(f"  gravidade: {lidos_falhas[1]['gravidade'].rotulo}")
    print(f"  próximo id livre: {proximo_id_ativo(lidos_ativos)}")

    assert lidos_ativos == ativos, "os dados lidos diferem dos gravados"
    assert lidos_falhas == falhas, "as falhas lidas diferem das gravadas"
    print("\nOK - o que saiu e o que voltou são idênticos.")

    # O id excluído não volta a circular, nem depois de reiniciar.
    base = dict(lidos_ativos)
    id_a = proximo_id_ativo(base)
    base[id_a] = dict(base[1])
    del base[id_a]
    salvar(base, lidos_falhas)

    _marca_alta["ativos"] = 0  # simula o programa reiniciando
    base, _ = carregar()
    id_b = proximo_id_ativo(base)

    print(f"\nEntreguei o id {id_a}, excluí o registro e reiniciei.")
    print(f"O próximo id foi {id_b} - o {id_a} não voltou a circular.")
    assert id_b > id_a, "o identificador foi reaproveitado"
    print("\nOK - identificadores não se repetem.")

    # Bases adulteradas: todas recusadas com mensagem, sem traceback.
    bom = {"hostname": "PC-01", "custodiante": "A", "lotacao": "B",
           "descricao": "C", "categoria": 1}
    orfa = {"ativo_id": 9, "descricao": "D",
            "origem": 1, "gravidade": 1, "situacao": 1}
    adulteradas = {
        "id '01'": json.dumps({"ativos": {"01": bom},
                               "falhas": {}}).encode(),
        "contador 10.0": json.dumps({"ativos": {}, "falhas": {},
                                     "ultimo_id_ativo": 10.0}).encode(),
        "falha órfã": json.dumps({"ativos": {"1": bom},
                                  "falhas": {"1": orfa}}).encode(),
        # ESC gravado no arquivo mexeria no terminal ao ser exibido.
        "ESC no hostname": json.dumps({"ativos": {"1": dict(
            bom, hostname="PC-01\u001b[2J")}, "falhas": {}}).encode(),
        # O "ó" em cp1252 é um byte inválido em UTF-8.
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

    os.remove(ARQUIVO_DADOS)
    print("\nA base real (inventario.json) não foi tocada.")
