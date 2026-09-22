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
| `arquivo.py` | Gravação e leitura da base em JSON, validação na carga e geração de identificadores |
| `equipamentos.py` | CRUD dos equipamentos de TI |
| `falhas.py` | Cadastro, listagem, correção e exclusão das vulnerabilidades, incluindo a cascata |
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

## Decisões além dos requisitos

As escolhas abaixo não são exigidas pelo enunciado. Vieram da análise do
problema e estão justificadas em comentário no próprio código.

- **Gravação atômica.** A base é escrita num arquivo temporário que só então
  substitui o definitivo (`os.replace`). Uma queda de energia no meio da
  escrita custa a última alteração, nunca a base inteira.
- **Validação na carga.** Arquivo corrompido ou adulterado faz o programa
  recusar abrir, explicando o motivo. Abrir com base parcial seria pior: a
  primeira gravação sobrescreveria o arquivo bom.
- **Identificadores que não se repetem.** O maior id já entregue fica gravado
  na própria base, então excluir um registro não devolve o número ao rodízio.
  Uma anotação externa apontando para "equipamento 2" continua significando a
  mesma máquina.
- **Correção e exclusão de vulnerabilidades.** O enunciado pede apenas o
  cadastro. Sem edição, um erro de digitação na severidade — que distorce a
  priorização, razão de ser do inventário — só teria conserto excluindo o
  equipamento inteiro e perdendo as demais vulnerabilidades dele.
- **Categoria "Outro", com descrição obrigatória.** Um inventário real sempre
  tem exceção — um nobreak, um switch, um scanner. Sem essa opção o operador
  seria forçado a classificar errado, e dado errado é pior que dado genérico.
  O Enum continua sendo conjunto fechado: "Outro" é um membro dele, não texto
  livre, e o rótulo na tela avisa que a descrição — já obrigatória — é onde
  se diz o que é.
- **Hierarquia na listagem de vulnerabilidades.** O programa imprime texto
  puro, sem cor nem negrito, então a hierarquia vem de ordem, posição e
  espaço em branco: severidade numa coluna fixa à esquerda, descrição em
  seguida, situação e categoria como legenda na linha de baixo. A largura da
  coluna do identificador é calculada a partir da própria lista, para o
  alinhamento não quebrar quando os IDs passarem de um dígito.
- **Padronização do texto digitado.** Hostname em caixa alta, responsável e
  lotação com iniciais maiúsculas, descrição com a primeira letra maiúscula.
  A regra só formata quando o operador escreveu tudo em caixa alta ou tudo em
  baixa; texto com maiúsculas e minúsculas misturadas é respeitado, o que
  preserva acrônimos como TI, CPD e RDP.

## Limitações conhecidas

- O programa assume **um operador por vez**. Duas instâncias abertas
  simultaneamente gravam por cima uma da outra. Num sistema real isso pediria
  um banco de dados com controle de concorrência.
- A base é gravada em **texto claro**, sem cifragem nem controle de acesso.
  A mitigação adotada aqui é não versionar o arquivo.

## Base de dados

Os dados ficam em `inventario.json`, criado na primeira execução ao lado do
código. O arquivo não é versionado: o repositório guarda código, não dado
gerado — e, num sistema de segurança, o inventário de vulnerabilidades é
justamente o que não se publica.

## Desenvolvimento

Cada módulo e cada correção foram desenvolvidos numa branch própria e
integrados à `main` por merge. O fast-forward está desabilitado no repositório
(`git config merge.ff false`) para que toda integração gere um commit de merge
e o histórico preserve a topologia das branches:

```
git log --oneline --graph --all
```

## Autor

Heluiz Tavares de Castro Filho — matrícula 12621CBS200
