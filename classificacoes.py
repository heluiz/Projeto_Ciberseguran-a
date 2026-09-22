"""
classificacoes.py
-----------------
Guarda as listas fixas do sistema: que tipos de equipamento existem, de onde
vem uma falha, qual a gravidade dela e em que situação está o tratamento.

Por que um arquivo só para isso?
Essas listas não mudam durante a execução e são usadas pelos demais
módulos. Isolando aqui, se um dia eu precisar acrescentar um tipo de
equipamento, mexo em um lugar só e o resto do programa acompanha sozinho.

Atende aos requisitos 2 e 7 do enunciado.
"""

from enum import Enum


# ===========================================================================
# REQUISITO 2 - tipos de ativo de TI, cada um com um código inteiro.
#
# Por que Enum e não uma lista comum de textos?
# Uma lista ["servidor", "roteador"] aceitaria qualquer coisa digitada errado
# ("servidorr", "SERVIDOR", "servdor") e eu só descobriria o problema depois,
# com a base já suja. O Enum cria um conjunto FECHADO: existe só o que está
# declarado aqui, e qualquer outro valor levanta erro na hora.
#
# Por que Enum e não IntEnum?
# Com IntEnum o membro se comporta como número (SERVIDOR == 2 daria True).
# Eu não quero isso: o código inteiro é um identificador, não uma quantidade -
# não faz sentido somar ou comparar dois tipos de equipamento. Uso Enum comum
# e pego o número por .value só na hora de gravar no arquivo.
# ===========================================================================
class CategoriaEquipamento(Enum):
    ESTACAO_TRABALHO = 1
    SERVIDOR         = 2
    ROTEADOR         = 3
    IMPRESSORA_REDE  = 4
    SISTEMA_INTERNO  = 5
    BANCO_DADOS      = 6

    @property
    def rotulo(self):
        """Texto com acento, para mostrar na tela."""
        return _ROTULOS_EQUIPAMENTO[self]


# Separo o nome técnico (ESTACAO_TRABALHO, que o código usa) do texto que o
# usuário lê. Assim posso escrever com acento sem quebrar o código.
# Este dicionário fica DEPOIS da classe de propósito: ele usa os membros dela
# como chave, então a classe precisa existir primeiro. Funciona porque o corpo
# da propriedade só roda quando eu chamo .rotulo, e aí o dicionário já existe.
_ROTULOS_EQUIPAMENTO = {
    CategoriaEquipamento.ESTACAO_TRABALHO: "Estação de trabalho",
    CategoriaEquipamento.SERVIDOR:         "Servidor",
    CategoriaEquipamento.ROTEADOR:         "Roteador",
    CategoriaEquipamento.IMPRESSORA_REDE:  "Impressora de rede",
    CategoriaEquipamento.SISTEMA_INTERNO:  "Sistema interno",
    CategoriaEquipamento.BANCO_DADOS:      "Banco de dados",
}


# ===========================================================================
# REQUISITO 7 - a vulnerabilidade precisa de CATEGORIA, GRAVIDADE e SITUAÇÃO.
# São três listas fechadas, pelo mesmo motivo do Enum acima.
# ===========================================================================
class OrigemFalha(Enum):
    ERRO_CONFIGURACAO    = 1
    FALTA_ATUALIZACAO    = 2
    SENHA_FRACA          = 3
    SERVICO_EXPOSTO      = 4
    PERMISSAO_INDEVIDA   = 5

    @property
    def rotulo(self):
        return _ROTULOS_ORIGEM[self]


_ROTULOS_ORIGEM = {
    OrigemFalha.ERRO_CONFIGURACAO:  "Erro de configuração",
    OrigemFalha.FALTA_ATUALIZACAO:  "Falta de atualização",
    OrigemFalha.SENHA_FRACA:        "Senha fraca",
    OrigemFalha.SERVICO_EXPOSTO:    "Serviço exposto indevidamente",
    OrigemFalha.PERMISSAO_INDEVIDA: "Permissão de acesso inadequada",
}


class NivelGravidade(Enum):
    # Aqui a ordem dos números TEM significado: 1 é menos grave que 4.
    # Isso me permite ordenar as falhas da mais crítica para a menos crítica
    # mais adiante, usando .value como critério.
    BAIXA   = 1
    MEDIA   = 2
    ALTA    = 3
    CRITICA = 4

    @property
    def rotulo(self):
        return _ROTULOS_GRAVIDADE[self]


_ROTULOS_GRAVIDADE = {
    NivelGravidade.BAIXA:   "Baixa",
    NivelGravidade.MEDIA:   "Média",
    NivelGravidade.ALTA:    "Alta",
    NivelGravidade.CRITICA: "Crítica",
}


class SituacaoTratamento(Enum):
    # As quatro situações vêm literalmente do requisito 7 do enunciado:
    # "aberta, em tratamento, corrigida ou aceita como risco".
    ABERTA           = 1
    EM_TRATAMENTO    = 2
    CORRIGIDA        = 3
    ACEITA_COMO_RISCO = 4

    @property
    def rotulo(self):
        return _ROTULOS_SITUACAO[self]


_ROTULOS_SITUACAO = {
    SituacaoTratamento.ABERTA:            "Aberta",
    SituacaoTratamento.EM_TRATAMENTO:     "Em tratamento",
    SituacaoTratamento.CORRIGIDA:         "Corrigida",
    SituacaoTratamento.ACEITA_COMO_RISCO: "Aceita como risco",
}


# ===========================================================================
# Bloco de teste rápido.
# Só roda se eu executar ESTE arquivo direto (python classificacoes.py).
# Se outro módulo fizer "import classificacoes", nada aqui é executado.
# Serve para eu conferir que as listas estão certas antes de seguir.
# ===========================================================================
if __name__ == "__main__":
    for classe in (CategoriaEquipamento, OrigemFalha,
                   NivelGravidade, SituacaoTratamento):
        print(f"\n--- {classe.__name__} ---")
        for item in classe:
            print(f"  {item.value} - {item.rotulo}")

    # Busca pelo código inteiro: o Enum já faz isso de graça.
    # CategoriaEquipamento(2) devolve o membro SERVIDOR.
    # Se eu passar um código que não existe, levanta ValueError - que é
    # exatamente o que eu quero tratar no menu (requisito 1).
    print("\nTeste de busca por código:")
    print("  código 2 ->", CategoriaEquipamento(2).rotulo)
    try:
        CategoriaEquipamento(99)
    except ValueError:
        print("  código 99 -> ValueError (correto: não existe)")