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

A BUSCA
O mesmo cuidado com o texto vale para procurar: para_busca() tira acento e
diferença de maiúscula, para "plantao" encontrar "Plantão".
"""

import unicodedata

# Partículas que ficam em minúscula quando não são a primeira palavra.
# Sem elas, "Sala de Máquinas" viraria "Sala De Máquinas" - errado em
# português, e o .title() do Python comete exatamente esse erro.
PARTICULAS = ("de", "da", "do", "das", "dos", "e")


def _sem_ordinais(texto):
    """
    O texto sem ª e º, usado só para conferir maiúsculas e minúsculas.

    O Python conta ª e º como letras minúsculas: "1ª DELEGACIA".isupper()
    dá False. Sem este cuidado, um texto digitado com Caps Lock passaria por
    "misturado" e nunca seria padronizado.
    """
    return texto.replace("ª", "").replace("º", "")


def ja_formatado(texto):
    """
    True se o texto tem maiúsculas E minúsculas misturadas.

    Um texto todo em caixa alta (isupper) ou todo em caixa baixa (islower)
    significa que o operador não se preocupou com formatação. Qualquer outra
    coisa significa que ele escolheu como escrever.
    """
    letras = _sem_ordinais(texto)
    return not letras.isupper() and not letras.islower()


def titulo(texto):
    """
    Para nome de pessoa e nome de lugar: inicial maiúscula em cada palavra,
    partículas em minúscula.

        "escrivão de plantão"  -> "Escrivão de Plantão"
        "ESCRIVÃO DE PLANTÃO"  -> "Escrivão de Plantão"
        "1ª DELEGACIA"         -> "1ª Delegacia"
        "Setor de TI"          -> "Setor de TI"   (misturado: respeita)

    A primeira linha tira os espaços das pontas e junta os repetidos: o
    split() sem argumento separa em qualquer quantidade de espaço, e o
    join() cola de volta com um espaço só.
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
    """
    Para descrição: só a primeira letra em maiúscula, o resto como veio.

        "porta RDP exposta"       -> "Porta RDP exposta"
        "PORTA RDP EXPOSTA"       -> "Porta rdp exposta"
        "iDRAC com senha padrão"  -> "iDRAC com senha padrão"

    Descrição é frase, não nome próprio. Se eu usasse titulo() aqui, sairia
    "Porta Rdp Exposta" - e o acrônimo estaria destruído.

    Manter o resto do texto intacto é justamente o que preserva RDP, CPD,
    SIGI, TI. A exceção é o texto todo em caixa alta, que precisa ser
    rebaixado: ali não há como distinguir "RDP" de "PORTA", então o acrônimo
    se perde. É o preço de digitar com Caps Lock ligado.

    E a primeira letra só sobe se a primeira palavra estiver toda em
    minúscula. "iDRAC" e "pfSense" já vêm com a maiúscula no lugar certo;
    subindo a primeira letra, virariam "IDRAC" e "PfSense".
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
    """
    Versão do texto usada só para COMPARAR numa busca: sem acento, sem
    diferença entre maiúscula e minúscula, sem espaço sobrando.

        "Setor de Informática"  -> "setor de informatica"
        "  PLANTÃO "            -> "plantao"

    Assim o operador encontra "Plantão" digitando "plantao", do jeito que se
    digita com pressa. O texto gravado não muda - isto serve só para comparar.

    casefold() é o lower() feito para comparação: a documentação do Python o
    recomenda para comparar sem diferenciar maiúsculas. O acento sai em dois
    passos: normalize("NFD") separa cada letra acentuada em letra + acento
    ("ã" vira "a" seguido do "~"), e combining() reconhece o acento solto,
    que eu descarto.
    """
    decomposto = unicodedata.normalize("NFD", " ".join(texto.split()).casefold())
    return "".join(c for c in decomposto if not unicodedata.combining(c))


if __name__ == "__main__":
    casos_titulo = [
        ("escrivão de plantão",   "Escrivão de Plantão"),
        ("ESCRIVÃO DE PLANTÃO",   "Escrivão de Plantão"),
        ("Setor de TI",           "Setor de TI"),
        ("sala   de  máquinas",   "Sala de Máquinas"),
        ("cartório",              "Cartório"),
        ("1ª DELEGACIA REGIONAL", "1ª Delegacia Regional"),
        ("Setor  de  TI",         "Setor de TI"),
    ]
    casos_frase = [
        ("porta RDP exposta",       "Porta RDP exposta"),
        ("PORTA RDP EXPOSTA",       "Porta rdp exposta"),
        ("senha padrão de fábrica", "Senha padrão de fábrica"),
        ("Já estava certo",         "Já estava certo"),
        ("iDRAC com senha padrão",  "iDRAC com senha padrão"),
        ("pfSense desatualizado",   "pfSense desatualizado"),
    ]
    casos_busca = [
        ("Setor de Informática",    "setor de informatica"),
        ("  PLANTÃO ",              "plantao"),
        ("Cartório",                "cartorio"),
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
