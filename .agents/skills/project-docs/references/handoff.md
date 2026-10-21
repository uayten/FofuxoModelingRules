# Handoff

Entrega o projeto a uma sessão sem memória desta: estado atual e próximo
passo, não a história.

## Processo

1. **Localizar.** A conversa no contexto e, se houver git, `git status`,
   `git diff --stat` e `git log` recente. Mudança que esta conversa não fez
   (outra conversa, o próprio usuário) entra no Estado como externa, sem
   inventar motivo. Se parte foi compactada, usar o resumo e avisar no
   relatório. Dos arquivos, ler só o necessário:
   - ROADMAP e DECISIONS: títulos (`grep "^### R-"`, `grep "^### [DF]-"`) e
     as entradas tocadas.
   - README e docs: só as seções de features aprovadas ou mudadas.
   - HANDOFF e CLAUDE.md: inteiros.
2. **Extrair eventos:** decisões, reversões, entregas, aprovações, ajustes,
   ideias, fatos checados, perguntas em aberto, desvios e feedback de
   terceiros (cada ponto mapeado à seção a que se refere).
3. **Marcar a origem:** usuário decidiu / IA sugeriu (aceita, pendente,
   ignorada) / terceiro (quem, onde, respondendo a quem).
4. **Estado final:** por assunto, vale a última palavra. O que não estiver
   claro vai para o passo 7.
5. **Classificar:** durável → DECISIONS, ROADMAP, README/docs, CLAUDE.md;
   volátil → HANDOFF; ruído (desvio resolvido, tentativa abandonada, sugestão
   recusada) → descartado, exceto lição recorrente ("X falha no Windows, usar
   Y") → CLAUDE.md.
6. **Comparar com o que foi lido**, sem abrir mais nada: contradições,
   lacunas e obsoletos, e também:
   - nenhum item aprovado sobrando no ROADMAP;
   - contadores `Próximo ID` acima de todos os IDs em uso;
   - o próximo passo do HANDOFF existe no ROADMAP ou se explica sozinho;
   - CLAUDE.md não contradiz DECISIONS; README não descreve nada removido ou
     não aprovado;
   - toda tradução desatualizada tem item.
7. **Perguntar uma vez** (AskUserQuestion, na mesma resposta): ambiguidades,
   imagens sugeridas e, em projeto novo, adotar ou só o prompt, pasta e
   arquivos soltos. Pular se não houver nada; não perguntar o que a conversa
   já resolveu.
8. **Aplicar e encerrar:** edições pontuais, HANDOFF sobrescrito, commit
   (só com git; regra em [SKILL.md](../SKILL.md)), relatório com uma linha
   por arquivo e o hash do commit, prompt de abertura. Nada depois dele.
   Commit falhou (hook, conflito): avisar no relatório e entregar o prompt
   mesmo assim.

## HANDOFF.md

Cabe em ~30 linhas; se não couber, algo durável está no lugar errado. Sem
histórico, sem "o que fizemos hoje".

```markdown
# Handoff

Atualizado: 2026-10-04

## Estado
O que funciona, o que está quebrado ou pela metade; branch, e o que ficou de fora do commit do handoff (se algo ficou).

## Próximo passo
Uma ação concreta, geralmente um item (R-012), e por onde começar.

## Perguntas em aberto
Esperando o usuário ou terceiros. Omitir se vazio.

## Notas para a próxima sessão
Contorno temporário, arquivo a evitar, peculiaridade do ambiente. Omitir se vazio.

## Ler primeiro
Arquivos a ler antes de agir, e os que não vale a pena ler.
```

## Prompt de abertura

Se o CLAUDE.md tem a linha de retomada, avisar que na janela nova, aberta na
pasta do projeto, basta "vamos continuar o projeto". Entregar mesmo assim o
prompt completo, em bloco, para o caso de a sessão abrir em outra pasta:

```
Continue o projeto <projeto> em <caminho>. Antes de agir, leia CLAUDE.md e HANDOFF.md; do ROADMAP.md, só os títulos (### R-...) e o item do próximo passo (DECISIONS.md quando surgir uma escolha). Confirme em 3 linhas o estado e o próximo passo e espere meu ok.
```

Acrescentar só o que os arquivos não dizem (por exemplo, "o usuário vai colar
o comentário do revisor").
