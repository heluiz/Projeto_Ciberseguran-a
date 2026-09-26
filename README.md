# Inventário de Ativos e Vulnerabilidades

Programa de linha de comando em Python para cadastro, consulta, atualização e
remoção (CRUD) de ativos de TI e das vulnerabilidades associadas a eles.

1ª atividade avaliativa (sprints 1 e 2) do Bacharelado em Cibersegurança —
FEELT/UFU, 2026/2.

## Como executar

Requer Python 3.8 ou superior. Não há dependências externas: o programa usa
apenas a biblioteca padrão (`json`, `os`, `sys`, `enum`, `string`,
`unicodedata` e, nos testes embutidos, `tempfile`).

```
git clone https://github.com/heluiz/Projeto_Ciberseguran-a.git
cd Projeto_Ciberseguran-a
python main.py
```

O programa começa com a base vazia. Para testá-lo com dados fictícios, veja a
[base de exemplo](#base-de-exemplo).

## Como usar

O menu numerado dá acesso a todas as operações. Depois de cada uma, o
resultado fica na tela até o Enter. Além dos números, estas palavras valem em
qualquer pergunta do programa:

| Comando | Efeito |
| --- | --- |
| `voltar` | Abandona a tela atual e volta ao menu, sem gravar o que estava pela metade |
| `sair` | Fecha o programa |
| `limpar` | Limpa a tela; no menu, desenha o menu de novo |
| `ajuda` ou `?` | Mostra a lista de comandos |
| `lista` | Nas perguntas de ID, mostra os ativos ou as vulnerabilidades e repete a pergunta |

As cores precisam de um terminal que interprete códigos ANSI: o Windows
Terminal, o terminal do VS Code, ou o PowerShell e o Prompt de Comando do
Windows 10 em diante. No IDLE elas se desligam sozinhas. Com a variável de
ambiente `NO_COLOR` definida, o programa imprime texto puro em qualquer
terminal.

## Estrutura

O projeto é dividido em sete módulos, cada um com uma responsabilidade única.
Apenas o `main.py` interage com o usuário — nos demais não há `input()`, e
`print()` só aparece no bloco de teste, o que permite testá-los isoladamente
executando cada arquivo diretamente (`python ativos.py`, por exemplo).

| Arquivo | Responsabilidade |
| --- | --- |
| `classificacoes.py` | Enums: tipo do ativo; categoria, severidade e status da vulnerabilidade |
| `cores.py` | Cores da saída no terminal (códigos ANSI), desligadas fora de um terminal e no IDLE |
| `formatacao.py` | Padronização de maiúsculas e minúsculas do texto digitado e comparação sem acento nas buscas |
| `arquivo.py` | Gravação e leitura da base em JSON, validação na carga e geração de identificadores |
| `ativos.py` | CRUD e buscas dos ativos de TI |
| `falhas.py` | Cadastro, listagem, correção e exclusão das vulnerabilidades, incluindo a cascata e a lista de pendentes |
| `main.py` | Menu textual, comandos globais, tratamento de erros e coordenação entre módulos |

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
| 9 | Uso de dicionário | Índice por ID, despacho do menu e tabela de comandos |
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
  opção nova custa uma linha nele e uma na tupla `OPCOES_MENU`, que monta o
  menu na tela.
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
- **Um nome por campo nas telas.** As telas usam os termos do enunciado —
  Responsável, Tipo (do ativo), Categoria (da vulnerabilidade), Severidade e
  Status — e cada um significa a mesma coisa em todas elas. No código e no
  arquivo de dados ficam os nomes internos (`custodiante`, `categoria`,
  `origem`, `gravidade`, `situacao`): trocar as chaves do JSON tornaria
  ilegíveis as bases já gravadas.

### Integridade da base

- **Gravação atômica.** A base é escrita num arquivo temporário, forçada
  para o disco (`os.fsync`) e só então substitui o definitivo
  (`os.replace`). Uma queda de energia no meio da escrita custa a última
  alteração, nunca a base inteira.
- **Validação na carga.** Arquivo corrompido, adulterado ou salvo em outra
  codificação faz o programa recusar abrir, explicando o motivo e qual
  registro está errado. Isso inclui identificador fora do formato (`"01"`),
  vulnerabilidade que aponta para um ativo inexistente e texto com caractere
  de controle. Abrir com base parcial seria pior: a primeira gravação
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
  programa avisa, com o tipo do erro, e recarrega a base do disco: a tela
  nunca mostra um cadastro que não foi gravado.

### Segurança

- **Caracteres de controle recusados.** Nenhum campo aceita caracteres
  invisíveis como ESC, nem na digitação nem na leitura do arquivo, que pode
  ser editado fora do programa. Exibidos, eles seriam interpretados pelo
  terminal e poderiam mudar cores, apagar linhas ou disfarçar o que aparece
  na tela (injeção de sequências de escape); alguns terminais aceitam até
  sequências que escrevem na área de transferência.
- **Hostname no formato que a rede aceita.** Só letras sem acento, números
  e hífen; não começa nem termina com hífen; no máximo 63 caracteres; e não
  pode ser só números. As regras vêm das RFC 952 e 1123, que definem nome de
  máquina, e da documentação da Microsoft para Active Directory. Hostname
  repetido também é recusado: duas máquinas com o mesmo nome são um conflito
  real na rede. Formato e repetição são conferidos na hora em que o operador
  digita, não depois de ele preencher os outros campos.

### Uso

- **Comandos em qualquer pergunta.** Toda leitura do teclado passa por uma
  única função, `ler_resposta()`, e por isso `voltar`, `sair`, `limpar` e
  `ajuda` valem em qualquer tela sem código repetido. Os comandos ficam numa
  tabela só, `COMANDOS`, que decide o que cada palavra faz e monta o texto da
  ajuda — o mesmo padrão do dicionário do menu. `voltar` e `sair` levantam
  exceções próprias (`VoltarAoMenu` e `SairDoPrograma`), capturadas no laço
  do menu antes do tratamento genérico de erros; é o mesmo mecanismo que o
  Python usa em `sys.exit()`. A alternativa, cada leitura devolver um valor
  especial, obrigaria cada ação a testá-lo depois de cada pergunta. Nada fica
  gravado pela metade, porque as ações só alteram a base depois da última
  pergunta. As palavras só contam como comando quando são a resposta
  inteira — "Sair do sistema legado" continua sendo uma descrição válida —,
  mas um campo que seja só "sair" deixa de ser aceito como dado.
- **Texto com cara de engano.** Responsável, lotação e descrições precisam
  ter pelo menos uma letra: "12" é recusado. Texto com menos de 3 caracteres
  pede confirmação, porque "TI" pode ser um setor, mas "a" costuma ser
  engano. Nas confirmações, "s" ou "sim" confirmam; qualquer outra resposta
  vale como não.
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
  responsável, lotação e tipo — o operador costuma lembrar de quem usa a
  máquina e de onde ela fica, não do nome dela. As buscas por texto aceitam
  parte do nome e ignoram maiúscula e acento: "plantao" encontra "Plantão".
  Um resultado mostra a ficha completa; vários, a tabela da listagem.
- **Relatório de pendentes (opção 10).** As vulnerabilidades abertas ou em
  tratamento de todos os ativos, da mais grave para a menos, com o hostname
  de cada uma. Uma linha no topo resume o total por severidade ("Crítica 10 ·
  Alta 30 · ..."), para a visão geral vir antes do detalhe. Responde à
  primeira pergunta de quem cuida da segurança: o que corrigir agora.
- **Pausa depois de cada ação.** O resultado fica na tela até o Enter; sem
  isso, o menu seria impresso logo abaixo e empurraria o começo de uma
  listagem longa para fora da janela. A pausa é pulada quando a entrada vem
  de um arquivo, para os testes automáticos rodarem sem ninguém digitando.

### Exibição

- **Listagem que cabe na tela.** Uma linha por ativo. Cada coluna tem a
  largura do maior valor da lista, com um teto; texto à esquerda, número à
  direita; dois espaços entre colunas. A linha mais larga possível tem 113
  caracteres, dentro das 120 colunas com que o Windows Terminal abre. O total
  de ativos vem no fim, porque numa lista longa o título já saiu da tela.
- **Hierarquia na listagem de vulnerabilidades.** Severidade numa coluna fixa
  à esquerda, descrição em seguida, status e categoria como legenda na linha
  de baixo. A largura da coluna do identificador é calculada a partir da
  própria lista, para o alinhamento não quebrar quando os IDs passarem de um
  dígito.
- **Cores com significado fixo.** Vermelho para erro, verde para ação
  concluída, amarelo para aviso e para os números das opções; a severidade
  vai de verde (Baixa) a vermelho em negrito (Crítica), e cada status tem sua
  cor. A cor reforça a hierarquia, não a substitui: o texto continua completo
  e legível sem ela. Os códigos ANSI ficam só em `cores.py` e só na tela —
  nada colorido é gravado na base. O texto sai puro quando a saída vai para
  um arquivo, quando o programa roda no IDLE (que se declara terminal, mas
  mostraria os códigos crus) e quando a variável `NO_COLOR` está definida,
  como pede a convenção [no-color.org](https://no-color.org/). Texto é
  alinhado antes de ser pintado, porque os códigos contam como caracteres e
  desalinhariam as colunas.

## Limitações conhecidas

- O programa assume **um operador por vez**. Duas instâncias abertas
  simultaneamente gravam por cima uma da outra. Num sistema real isso pediria
  um banco de dados com controle de concorrência.
- A base é gravada em **texto claro**, sem cifragem nem controle de acesso.
  A mitigação adotada aqui é não versionar o arquivo.
- No **IDLE**, as cores ficam desligadas e `limpar` não tem efeito: o IDLE
  não interpreta códigos de terminal. Os outros comandos funcionam.

## Base de dados

Os dados ficam em `inventario.json`, criado ao lado do código na primeira
gravação. O arquivo não é versionado: o repositório guarda código, não dado
gerado — e, num sistema de segurança, o inventário de vulnerabilidades é
justamente o que não se publica.

### Base de exemplo

Para testar o programa com dados, o repositório traz `inventario_exemplo.json`:
76 ativos e 88 vulnerabilidades, distribuídos pelos setores da 1ª DRPC
Uberlândia. Os setores e os sistemas citados existem, mas hostnames,
vulnerabilidades e status são fictícios e não descrevem a rede real. Para
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
