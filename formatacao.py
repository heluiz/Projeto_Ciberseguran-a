"""
formatacao.py
-------------
Padroniza maiúsculas e minúsculas do texto digitado pelo operador.

Por que um módulo só para isso?
Porque a mesma regra vale para equipamentos e para vulnerabilidades. Se cada
módulo tivesse a sua cópia, um dia elas divergiriam. E importar função de um
módulo de dados no outro amarraria os dois sem necessidade - este módulo não
sabe o que é equipamento nem o que é falha, só mexe em texto.

A REGRA CENTRAL
Se o operador escreveu tudo em caixa alta ou tudo em caixa baixa, ele não
formatou nada - só digitou. Aí o programa formata. Se ele misturou maiúsculas
e minúsculas, formatou de propósito, e o programa respeita.

Isso protege acrônimos, que são comuns num inventário de TI: "Setor de TI"
chega misturado e passa intacto, enquanto "setor de ti" vira "Setor de Ti".
"""

# Partículas que ficam em minúscula quando não são a primeira palavra.
# Sem elas, "Sala de Máquinas" viraria "Sala De Máquinas" - errado em
# português, e o .title() do Python comete exatamente esse erro.
PARTICULAS = ("de", "da", "do", "das", "dos", "e")


def ja_formatado(texto):
    """
    True se o texto tem maiúsculas E minúsculas misturadas.

    Um texto todo em caixa alta (isupper) ou todo em caixa baixa (islower)
    significa que o operador não se preocupou com formatação. Qualquer outra
    coisa significa que ele escolheu como escrever.
    """
    return not texto.isupper() and not texto.islower()


def titulo(texto):
    """
    Para nome de pessoa e nome de lugar: inicial maiúscula em cada palavra,
    partículas em minúscula.

        "escrivão de plantão"  -> "Escrivão de Plantão"
        "ESCRIVÃO DE PLANTÃO"  -> "Escrivão de Plantão"
        "Setor de TI"          -> "Setor de TI"   (misturado: respeita)

    O split() de quebra também limpa espaços repetidos, de graça.
    """
    texto = texto.strip()
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
    """
    Para descrição: só a primeira letra em maiúscula, o resto como veio.

        "porta RDP exposta"    -> "Porta RDP exposta"
        "PORTA RDP EXPOSTA"    -> "Porta rdp exposta"

    Descrição é frase, não nome próprio. Se eu usasse titulo() aqui, sairia
    "Porta Rdp Exposta" - e o acrônimo estaria destruído.

    Manter o resto do texto intacto é justamente o que preserva RDP, CPD,
    SIGI, TI. A exceção é o texto todo em caixa alta, que precisa ser
    rebaixado: ali não há como distinguir "RDP" de "PORTA", então o acrônimo
    se perde. É o preço de digitar com Caps Lock ligado.
    """
    texto = texto.strip()
    if not texto:
        return texto
    if texto.isupper():
        texto = texto.lower()
    return texto[0].upper() + texto[1:]


if __name__ == "__main__":
    casos_titulo = [
        ("escrivão de plantão", "Escrivão de Plantão"),
        ("ESCRIVÃO DE PLANTÃO", "Escrivão de Plantão"),
        ("Setor de TI",         "Setor de TI"),
        ("sala   de  máquinas", "Sala de Máquinas"),
        ("cartório",            "Cartório"),
    ]
    casos_frase = [
        ("porta RDP exposta",      "Porta RDP exposta"),
        ("PORTA RDP EXPOSTA",      "Porta rdp exposta"),
        ("senha padrão de fábrica", "Senha padrão de fábrica"),
        ("Já estava certo",        "Já estava certo"),
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

    print("\nOK - formatação passou em todos os casos.")
