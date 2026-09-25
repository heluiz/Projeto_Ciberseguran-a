# Inventário de Ativos e Vulnerabilidades

Programa de linha de comando em Python para cadastro, consulta, atualização e
remoção (CRUD) de ativos de TI e das vulnerabilidades associadas a eles.

1ª atividade avaliativa (sprints 1 e 2) do Bacharelado em Cibersegurança —
FEELT/UFU, 2026/2.

## Como executar

Requer Python 3.8 ou superior. Não há dependências externas: o programa usa
apenas a biblioteca padrão (`json`, `os`, `enum`, `string`, `unicodedata` e,
nos testes embutidos, `tempfile`).

```
git clone https://github.com/heluiz/Projeto_Ciberseguran-a.git
cd Projeto_Ciberseguran-a
python main.py
```

O programa começa com a base vazia. Para testá-lo com dados fictícios, veja a
[base de exemplo](#base-de-exemplo).

## Estrutura

O projeto é dividido em seis módulos, cada um com uma responsabilidade única.
Apenas o `main.py` interage com o usuário — nos demais não há `input()`, e
`print()` só aparece no bloco de teste, o que permite testá-los isoladamente
executando cada arquivo diretamente (`python ativos.py`, por exemplo).

| Arquivo | Responsabilidade |
| --- | --- |
| `classificacoes.py` | Enums: tipo de ativo, origem, gravidade e situação da falha |
| `formatacao.py` | Padronização de maiúsculas e minúsculas do texto digitado e comparação sem acento nas buscas |
| `arquivo.py` | Gravação e leitura da base em JSON, validação na carga e geração de identificadores |
| `ativos.py` | CRUD e buscas dos ativos de TI |
| `falhas.py` | Cadastro, listagem, correção e exclusão das vulnerabilidades, incluindo a cascata e a lista de pendentes |
| `main.py` | Menu textual, tratamento de erros e coordenação entre módulos |

## Requisitos atendidos

| Nº | Requisito | Onde |
| --- | --- | --- |
| 1 | Menu textual com tratamento de erros | `main.py` |
| 2 | Enumeração de tipos de ativo com código inteiro | `classificacoes.py` |
| 3 | Cadastro gravado em arquivo de texto | `ativos.py`, `arquivo.py` |
| 4 | Busca por identificador ou hostname | `ativos.py` |
| 5 | Atualização de ativo | `ativos.py` |
| 6 | Exclusão com remoção das vulnerabilidades | `main.py`, `falhas.py` |
| 7 | Cadastro de vulnerabilidades | `falhas.py` |
| 8 | Visualização das vulnerabilidades | `main.py` |
| 9 | Uso de dicionário | Índice por ID e despacho do menu |
| 10 | Repositório com múltiplas branches e merges | Histórico deste repositório |

## Padrão de código

O código segue o [PEP 8](https://peps.python.org/pep-0008/) (estilo) e o
[PEP 257](https://peps.python.org/pep-0257/) (docstrings). Toda função tem
docstring: uma linha de resumo e, quando preciso, o que ela devolve e que
erro levanta. Os comentários seguem o
[guia de estilo do Google](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings):
explicam só o porquê que o código não mostra, sem repetir o que o Python já
diz. As justificativas mais longas ficam na seção de decisões, abaixo.

A conformidade pode ser conferida com duas ferramentas opcionais, que não são
necessárias para rodar o programa:

```
pip install pycodestyle pydocstyle
pycodestyle --max-doc-length=72 .
pydocstyle .
```

## Decisões de projeto

### Estrutura e dados

- **"Ativo", não "equipamento".** O enunciado fala em ativos de TI, e o
  inventário inclui sistemas internos e bancos de dados, que não são
  equipamentos. O termo é o mesmo nas telas, no código e no arquivo de dados.
- **Enum para os tipos, e não lista de textos.** Uma lista aceitaria
  "servidorr" ou "SERVIDOR" e o erro só apareceria depois, com a base já
  suja. O Enum é um conjunto fechado: código fora da lista levanta erro na
  hora, e o menu pede de novo. É `Enum` e não `IntEnum` porque o código é um
  identificador, não uma quantidade.
- **Dicionário indexado pelo ID.** A busca por ID é direta, com o mesmo
  custo para 10 ou 10.000 ativos; a busca por hostname percorre a base,
  porque o hostname não é a chave. O menu também é um dicionário, de número
  da opção para função: substitui uma cadeia de `if`/`elif`, e ligar uma
  opção nova custa uma linha nele e um `print` no menu.
- **Módulos que não se enxergam.** `ativos.py` e `falhas.py` não importam
  um ao outro, para serem testados sozinhos. Por isso `falhas.py` não confere
  se o ativo existe, e a exclusão em cascata fica no `main.py`, que coordena
  os dois: primeiro as vulnerabilidades, depois o ativo, para nunca sobrar
  vulnerabilidade apontando para ativo inexistente.
- **Categoria "Outro", com descrição obrigatória.** Um inventário real sempre
  tem exceção — um nobreak, um switch, um scanner. Sem essa opção o operador
  seria forçado a classificar errado, e dado errado é pior que dado genérico.
  "Outro" continua sendo membro do Enum, não texto livre, e o rótulo avisa
  que a descrição diz o que é.

### Integridade da base

- **Gravação atômica.** A base é escrita num arquivo temporário, forçada
  para o disco (`os.fsync`) e só então substitui o definitivo
  (`os.replace`). Uma queda de energia no meio da escrita custa a última
  alteração, nunca a base inteira.
- **Validação na carga.** Arquivo corrompido, adulterado ou salvo em outra
  codificação faz o programa recusar abrir, explicando o motivo. Isso inclui
  identificador fora do formato (`"01"`) e vulnerabilidade que aponta para um
  ativo inexistente. Abrir com base parcial seria pior: a primeira gravação
  sobrescreveria o arquivo bom.
- **Identificadores que não se repetem.** O maior id já entregue fica gravado
  na própria base, então excluir um registro não devolve o número ao rodízio.
  Uma anotação externa apontando para "ativo 2" continua significando o mesmo
  ativo.
- **Atualização tudo ou nada.** Todas as mudanças pedidas são conferidas
  antes de qualquer uma ser aplicada: um hostname recusado não deixa os
  outros campos já trocados.
- **Mensagem de sucesso só depois de gravar.** Toda ação que altera dados só
  mostra a mensagem de sucesso depois que o dado já está no disco. E os
  testes embutidos usam um arquivo temporário: rodar `python arquivo.py`
  não toca na base real.
- **Erro no meio de uma ação.** O laço do menu captura qualquer erro
  inesperado — é o ponto de isolamento do programa (requisito 1). Se uma
  gravação falhar (disco cheio, arquivo travado por outro programa), o
  programa avisa e recarrega a base do disco: a tela nunca mostra um cadastro
  que não foi gravado.

### Uso

- **Hostname no formato que a rede aceita.** Só letras sem acento, números
  e hífen; não começa nem termina com hífen; no máximo 63 caracteres; e não
  pode ser só números. As regras vêm das RFC 952 e 1123, que definem nome de
  máquina, e da documentação da Microsoft para Active Directory. Hostname
  repetido também é recusado: duas máquinas com o mesmo nome são um conflito
  real na rede. Formato e repetição são conferidos na hora em que o operador
  digita, não depois de ele preencher os outros campos.
- **Texto com cara de engano.** Responsável, lotação e descrições precisam
  ter pelo menos uma letra: "12" é recusado. Texto com menos de 3 caracteres
  pede confirmação, porque "TI" pode ser um setor, mas "a" costuma ser
  engano. Nas confirmações, "s" ou "sim" confirmam; qualquer outra resposta
  vale como não.
- **Caracteres de controle recusados.** Nenhum campo aceita caracteres
  invisíveis como ESC. Gravados, eles seriam enviados ao terminal toda vez
  que o texto aparecesse e poderiam mudar cores, apagar a tela ou disfarçar
  o que é exibido (injeção de sequências de escape).
- **Padronização do texto digitado.** Hostname em caixa alta, responsável e
  lotação com iniciais maiúsculas, descrição com a primeira letra maiúscula.
  A regra só formata quando o operador escreveu tudo em caixa alta ou tudo em
  baixa; texto com maiúsculas e minúsculas misturadas é respeitado, o que
  preserva acrônimos no meio do texto ("Setor de TI", "porta RDP exposta") e
  nomes como iDRAC e pfSense. Quando formata, a regra devolve as siglas
  conhecidas à grafia certa: sem isso, "DEAM" viraria "Deam" e "1ª DP",
  "1ª Dp". Elas ficam na lista `SIGLAS`, em `formatacao.py`, assim como as
  partículas "de" e "da" ficam na lista que as mantém em minúscula. Sigla
  fora da lista não tem como ser reconhecida.
- **Correção e exclusão de vulnerabilidades.** O enunciado pede apenas o
  cadastro. Sem edição, um erro de digitação na severidade — que distorce a
  priorização, razão de ser do inventário — só teria conserto excluindo o
  ativo inteiro e perdendo as demais vulnerabilidades dele. Vulnerabilidade
  resolvida não se exclui: marca-se como Corrigida, para manter o histórico.
- **Mais formas de busca.** Além de ID e hostname, a busca aceita
  responsável, lotação e categoria — o operador costuma lembrar de quem usa
  a máquina e de onde ela fica, não do nome dela. As buscas por texto aceitam
  parte do nome e ignoram maiúscula e acento: "plantao" encontra "Plantão".
  Um resultado mostra a ficha completa; vários, a tabela da listagem.
- **Relatório de pendentes (opção 10).** As vulnerabilidades abertas ou em
  tratamento de todos os ativos, da mais grave para a menos, com o hostname
  de cada uma. Responde à primeira pergunta de quem cuida da segurança: o que
  corrigir agora.
- **Listagem que cabe na tela.** Uma linha por ativo. Cada coluna tem a
  largura do maior valor da lista, com um teto; texto à esquerda, número à
  direita; dois espaços entre colunas. A linha mais larga possível tem 113
  caracteres, dentro das 120 colunas com que o Windows Terminal abre.
- **Hierarquia na listagem de vulnerabilidades.** O programa imprime texto
  puro, sem cor nem negrito, então a hierarquia vem de ordem, posição e
  espaço em branco: severidade numa coluna fixa à esquerda, descrição em
  seguida, situação e categoria como legenda na linha de baixo. A largura da
  coluna do identificador é calculada a partir da própria lista, para o
  alinhamento não quebrar quando os IDs passarem de um dígito.

## Limitações conhecidas

- O programa assume **um operador por vez**. Duas instâncias abertas
  simultaneamente gravam por cima uma da outra. Num sistema real isso pediria
  um banco de dados com controle de concorrência.
- A base é gravada em **texto claro**, sem cifragem nem controle de acesso.
  A mitigação adotada aqui é não versionar o arquivo.

## Base de dados

Os dados ficam em `inventario.json`, criado ao lado do código na primeira
gravação. O arquivo não é versionado: o repositório guarda código, não dado
gerado — e, num sistema de segurança, o inventário de vulnerabilidades é
justamente o que não se publica.

### Base de exemplo

Para testar o programa com dados, o repositório traz `inventario_exemplo.json`:
76 ativos e 88 vulnerabilidades, distribuídos pelos setores da 1ª DRPC
Uberlândia. Os setores e os sistemas citados existem, mas hostnames,
vulnerabilidades e situações são fictícios e não descrevem a rede real. Para
usar o exemplo, copie-o por cima da base (a base atual é substituída):

```
copy inventario_exemplo.json inventario.json
```

No Linux e no macOS, o comando é `cp` em vez de `copy`. O exemplo fica num
arquivo à parte, e não no próprio `inventario.json`, porque o programa regrava
a base a cada alteração: versionada, ela levaria para o repositório cada teste
feito, e uma base real poderia ser publicada por engano.

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
