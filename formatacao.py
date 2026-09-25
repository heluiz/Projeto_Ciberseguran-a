"""Padronização do texto digitado e comparação para buscas.

Texto todo em maiúsculas ou todo em minúsculas é padronizado; texto
com caixa misturada foi escrito assim de propósito e é mantido, o que
preserva siglas como TI e RDP. O módulo só trata texto: não conhece
ativos nem falhas.
"""

import unicodedata

# Ficam em minúscula quando não são a primeira palavra do nome.
PARTICULAS = ("de", "da", "do", "das", "dos", "e")


def _sem_ordinais(texto):
    """Devolve o texto sem ª e º, só para testar a caixa.

    O Python trata ª e º como minúsculas: sem isto, "1ª DELEGACIA" não
    seria reconhecido como texto todo em maiúsculas.
    """
    return texto.replace("ª", "").replace("º", "")


def ja_formatado(texto):
    """Diz se o texto mistura maiúsculas e minúsculas."""
    letras = _sem_ordinais(texto)
    return not letras.isupper() and not letras.islower()


def titulo(texto):
    """Formata nome de pessoa ou de lugar com iniciais maiúsculas.

    Espaços repetidos viram um só e as partículas (de, da, do...) ficam
    em minúscula. Se o texto já mistura maiúsculas e minúsculas, a
    caixa é mantida.
    """
    texto = " ".join(texto.split())
    if ja_formatado(texto):
        return texto

    palavras = texto.lower().split()
    saida = []
    for posicao, palavra in enumerate(palavras):
        if posicao > 0 and palavra in PARTICULAS:
            saida.append(palavra)
        else:
            saida.append(palavra.capitalize())
    return " ".join(saida)


def frase(texto):
    """Formata descrição: só a primeira letra vira maiúscula.

    Espaços repetidos viram um só e o resto fica como veio, para
    preservar siglas. Texto todo em maiúsculas é rebaixado antes,
    porque ali não há como distinguir sigla de palavra. A inicial não
    muda se a primeira palavra já tiver maiúscula (iDRAC, pfSense).
    """
    texto = " ".join(texto.split())
    if not texto:
        return texto
    if _sem_ordinais(texto).isupper():
        texto = texto.lower()
    if texto.split()[0].islower():
        texto = texto[0].upper() + texto[1:]
    return texto


def para_busca(texto):
    """Devolve a forma do texto usada só para comparar em buscas.

    Sem acento, sem diferença de caixa e sem espaço sobrando: assim
    "plantao" encontra "Plantão". O texto gravado não muda.
    """
    # casefold() é o lower() próprio para comparação; NFD separa cada
    # letra do seu acento, e o filtro descarta os acentos soltos.
    limpo = " ".join(texto.split()).casefold()
    decomposto = unicodedata.normalize("NFD", limpo)
    return "".join(c for c in decomposto if not unicodedata.combining(c))


# Teste rápido: roda só com "python formatacao.py", nunca no import.
if __name__ == "__main__":
    casos_titulo = [
        ("escrivão de plantão", "Escrivão de Plantão"),
        ("ESCRIVÃO DE PLANTÃO", "Escrivão de Plantão"),
        ("Setor de TI", "Setor de TI"),
        ("sala   de  máquinas", "Sala de Máquinas"),
        ("cartório", "Cartório"),
        ("1ª DELEGACIA REGIONAL", "1ª Delegacia Regional"),
        ("Setor  de  TI", "Setor de TI"),
    ]
    casos_frase = [
        ("porta RDP exposta", "Porta RDP exposta"),
        ("PORTA RDP EXPOSTA", "Porta rdp exposta"),
        ("senha padrão de fábrica", "Senha padrão de fábrica"),
        ("Já estava certo", "Já estava certo"),
        ("iDRAC com senha padrão", "iDRAC com senha padrão"),
        ("pfSense desatualizado", "pfSense desatualizado"),
    ]
    casos_busca = [
        ("Setor de Informática", "setor de informatica"),
        ("  PLANTÃO ", "plantao"),
        ("Cartório", "cartorio"),
    ]

    print("--- titulo() ---")
    for entrada, esperado in casos_titulo:
        obtido = titulo(entrada)
        marca = "ok " if obtido == esperado else "ERRO"
        print(f"  {marca} {entrada!r:28} -> {obtido!r}")
        assert obtido == esperado, f"esperava {esperado!r}"

    print("\n--- frase() ---")
    for entrada, esperado in casos_frase:
        obtido = frase(entrada)
        marca = "ok " if obtido == esperado else "ERRO"
        print(f"  {marca} {entrada!r:28} -> {obtido!r}")
        assert obtido == esperado, f"esperava {esperado!r}"

    print("\n--- para_busca() ---")
    for entrada, esperado in casos_busca:
        obtido = para_busca(entrada)
        marca = "ok " if obtido == esperado else "ERRO"
        print(f"  {marca} {entrada!r:28} -> {obtido!r}")
        assert obtido == esperado, f"esperava {esperado!r}"

    print("\nOK - formatação passou em todos os casos.")
