# Inventário de Segurança de TI

Programa de linha de comando em Python para cadastro, consulta, atualização e
remoção (CRUD) de ativos de TI e das vulnerabilidades associadas a eles.

1ª atividade avaliativa (sprints 1 e 2) do Bacharelado em Cibersegurança —
FEELT/UFU, 2026/2.

## Como executar

Requer Python 3.8 ou superior. Não há dependências externas: o programa usa
apenas a biblioteca padrão (`json`, `os`, `enum`).

```
git clone https://github.com/heluiz/Projeto_Ciberseguran-a.git
cd Projeto_Ciberseguran-a
python main.py
```

## Estrutura

O projeto é dividido em seis módulos, cada um com uma responsabilidade única.
Apenas o `main.py` interage com o usuário — os demais não possuem `input()` nem
`print()`, o que permite testá-los isoladamente executando cada arquivo
diretamente (`python equipamentos.py`, por exemplo).

| Arquivo | Responsabilidade |
| --- | --- |
| `classificacoes.py` | Enums: tipo de equipamento, origem, gravidade e situação da falha |
| `formatacao.py` | Padronização de maiúsculas e minúsculas do texto digitado |
| `arquivo.py` | Leitura e gravação da base em JSON, com escrita atômica |
| `equipamentos.py` | CRUD dos equipamentos de TI |
| `falhas.py` | Cadastro, listagem e exclusão em cascata das vulnerabilidades |
| `main.py` | Menu textual, tratamento de erros e coordenação entre módulos |

## Requisitos atendidos

| Nº | Requisito | Onde |
| --- | --- | --- |
| 1 | Menu textual com tratamento de erros | `main.py` |
| 2 | Enumeração de tipos de ativo com código inteiro | `classificacoes.py` |
| 3 | Cadastro gravado em arquivo de texto | `equipamentos.py`, `arquivo.py` |
| 4 | Busca por identificador ou hostname | `equipamentos.py` |
| 5 | Atualização de ativo | `equipamentos.py` |
| 6 | Exclusão com remoção das vulnerabilidades | `main.py`, `falhas.py` |
| 7 | Cadastro de vulnerabilidades | `falhas.py` |
| 8 | Visualização das vulnerabilidades | `main.py` |
| 9 | Uso de dicionário | Índice por ID e despacho do menu |
| 10 | Repositório com múltiplas branches e merges | Histórico deste repositório |

## Base de dados

Os dados ficam em `inventario.json`, criado na primeira execução ao lado do
código. O arquivo não é versionado: o repositório guarda código, não dado
gerado — e, num sistema de segurança, o inventário de vulnerabilidades é
justamente o que não se publica.

## Desenvolvimento

Cada módulo foi desenvolvido em uma branch própria (`feature/persistencia`,
`feature/equipamentos`, `feature/falhas`, `feature/menu`) e integrado à `main`
por merge. O fast-forward está desabilitado no repositório para que cada
integração gere um commit de merge e o histórico preserve a topologia das
branches:

```
git log --oneline --graph --all
```

## Autor

Heluiz Tavares de Castro Filho — matrícula 12621CBS200
