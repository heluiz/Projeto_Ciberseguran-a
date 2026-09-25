"""Listas fechadas do sistema: tipos de ativo e classificação de falhas.

Cada lista é um Enum: o valor inteiro vai para o arquivo, e o rótulo
com acento, para a tela. Atende aos requisitos 2 e 7.
"""

from enum import Enum


class CategoriaAtivo(Enum):
    """Tipo de ativo de TI, com código inteiro (requisito 2).

    Código fora da lista levanta ValueError, que o menu trata.
    """

    ESTACAO_TRABALHO = 1
    SERVIDOR = 2
    ROTEADOR = 3
    IMPRESSORA_REDE = 4
    SISTEMA_INTERNO = 5
    BANCO_DADOS = 6
    OUTRO = 7  # para exceções; a descrição obrigatória diz o que é

    @property
    def rotulo(self):
        """Nome com acento, para mostrar na tela."""
        return _ROTULOS_ATIVO[self]


# Os rótulos ficam depois de cada classe porque usam os membros dela
# como chave; a propriedade rotulo só consulta o dicionário quando é
# lida, e aí ele já existe.
_ROTULOS_ATIVO = {
    CategoriaAtivo.ESTACAO_TRABALHO: "Estação de trabalho",
    CategoriaAtivo.SERVIDOR: "Servidor",
    CategoriaAtivo.ROTEADOR: "Roteador",
    CategoriaAtivo.IMPRESSORA_REDE: "Impressora de rede",
    CategoriaAtivo.SISTEMA_INTERNO: "Sistema interno",
    CategoriaAtivo.BANCO_DADOS: "Banco de dados",
    CategoriaAtivo.OUTRO: "Outro (ver descrição)",
}


class OrigemFalha(Enum):
    """Origem da vulnerabilidade: a categoria pedida no requisito 7."""

    ERRO_CONFIGURACAO = 1
    FALTA_ATUALIZACAO = 2
    SENHA_FRACA = 3
    SERVICO_EXPOSTO = 4
    PERMISSAO_INDEVIDA = 5
    OUTRA = 6  # a lista do enunciado é só de exemplos

    @property
    def rotulo(self):
        """Nome com acento, para mostrar na tela."""
        return _ROTULOS_ORIGEM[self]


_ROTULOS_ORIGEM = {
    OrigemFalha.ERRO_CONFIGURACAO: "Erro de configuração",
    OrigemFalha.FALTA_ATUALIZACAO: "Falta de atualização",
    OrigemFalha.SENHA_FRACA: "Senha fraca",
    OrigemFalha.SERVICO_EXPOSTO: "Serviço exposto indevidamente",
    OrigemFalha.PERMISSAO_INDEVIDA: "Permissão de acesso inadequada",
    OrigemFalha.OUTRA: "Outra (ver descrição)",
}


class NivelGravidade(Enum):
    """Severidade da vulnerabilidade; valor maior é mais grave.

    A ordem dos valores é usada para ordenar as falhas.
    """

    BAIXA = 1
    MEDIA = 2
    ALTA = 3
    CRITICA = 4

    @property
    def rotulo(self):
        """Nome com acento, para mostrar na tela."""
        return _ROTULOS_GRAVIDADE[self]


_ROTULOS_GRAVIDADE = {
    NivelGravidade.BAIXA: "Baixa",
    NivelGravidade.MEDIA: "Média",
    NivelGravidade.ALTA: "Alta",
    NivelGravidade.CRITICA: "Crítica",
}


class SituacaoTratamento(Enum):
    """Situação do tratamento: os quatro estados do requisito 7."""

    ABERTA = 1
    EM_TRATAMENTO = 2
    CORRIGIDA = 3
    ACEITA_COMO_RISCO = 4

    @property
    def rotulo(self):
        """Nome com acento, para mostrar na tela."""
        return _ROTULOS_SITUACAO[self]


_ROTULOS_SITUACAO = {
    SituacaoTratamento.ABERTA: "Aberta",
    SituacaoTratamento.EM_TRATAMENTO: "Em tratamento",
    SituacaoTratamento.CORRIGIDA: "Corrigida",
    SituacaoTratamento.ACEITA_COMO_RISCO: "Aceita como risco",
}


# Teste rápido: roda só com "python classificacoes.py", nunca no import.
if __name__ == "__main__":
    for classe in (CategoriaAtivo, OrigemFalha,
                   NivelGravidade, SituacaoTratamento):
        print(f"\n--- {classe.__name__} ---")
        for item in classe:
            print(f"  {item.value} - {item.rotulo}")

    # Código inexistente levanta ValueError: é o que o menu trata.
    print("\nTeste de busca por código:")
    print("  código 2 ->", CategoriaAtivo(2).rotulo)
    try:
        CategoriaAtivo(99)
    except ValueError:
        print("  código 99 -> ValueError (correto: não existe)")
