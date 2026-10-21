# Preferências globais

Responder em português.

## Código em inglês

- Identificador, comentário, log e mensagem de commit em inglês, desde a
  primeira linha: traduzir depois custa reescrever o projeto.
- Código novo nasce em inglês mesmo em arquivo que está em português. O que já
  existe não é renomeado de passagem; renomeação em massa é pedido à parte.
- Português nos arquivos mexidos: avisar no fim da tarefa, uma linha por
  arquivo com o tamanho aproximado (`X.cpp: ~12 nomes`). Não achou, não dizer
  nada, nem que está tudo em inglês. Não varrer o projeto atrás disso.
- Texto que o usuário final lê (UI, README) segue a decisão do projeto

## README

Antes de escrever ou mexer num README, ler
`~/.claude/skills/project-docs/references/readme.md`.

## Commits

O commit é o "salvar" de uma feature validada. O CLAUDE.md do projeto pode
acrescentar passos ou trocar o idioma da mensagem.

- Não commitar no fim da resposta que fez a mudança.
- Mensagem que confirma que os testes da feature passaram: é a validação.
  Commitar tudo o que estiver pendente nessa mesma resposta, sem esperar a
  mudança de tópico.
- Mensagem que muda de tópico: antes de começar, commitar tudo o que estiver
  pendente (`git add -A`), meu e do usuário. A mensagem descreve o conjunto; o
  que veio do usuário é descrito pelo `git status`.
- Mensagem que pede correção da feature em andamento: corrigir sem commitar. As
  correções entram no mesmo commit da feature.
- Na dúvida, tratar como correção: commitar depois é fácil, separar um commit
  misturado não.

## Janela de contexto nova

Tarefa extensa e sem relação com a conversa, ou conversa já longa numa pausa
natural (feature aprovada, troca de item do roadmap): avisar que rende mais
numa janela nova. Em projeto que segue a convenção project-docs, oferecer o
handoff da skill em vez de escrever o prompt; nos outros, entregar um prompt de
abertura autossuficiente (arquivos a ler, arquivos a evitar, o que já foi
decidido). Vale quando reler os arquivos da tarefa nova custa menos que
arrastar o histórico. Continuar é escolha do usuário.

Com o contexto abaixo da metade e a próxima tarefa ligada à conversa, seguir
sem sugerir. Quando sugerir, mostrar os números (contexto atual e custo
estimado de começar de novo), sem dizer que a conversa "está longa".

## Caminho barato indisponível

Se o caminho mais barato em tokens falhar (MCP fora do ar, permissão negada,
Editor fechado, índice ausente), avisar e parar em vez de contornar lendo
arquivos inteiros ou varrendo o projeto. Dizer o que falhou, o que custa
religar e quanto custaria a alternativa; só seguir por ela se o usuário mandar.

Sem verificação barata para confirmar algo, dizer isso. Nunca ler o arquivo
inteiro por falta de atalho, nem afirmar de memória o que não foi verificado.
