---
name: project-docs
description: Último prompt de uma conversa num projeto longo - lê a sessão, atualiza ROADMAP.md (o que falta, para agentes), DECISIONS.md (decisões e fatos verificados), HANDOFF.md (estado + próximo passo), README.md e CLAUDE.md, e entrega o prompt da próxima janela; a conversa termina ali. Use quando o usuário quiser ir para outra conversa, disser que o contexto está grande ou cheio, pedir handoff ou prompt para nova janela, ou quiser encerrar a sessão, mesmo que diga só "vamos para outra conversa que a janela de contexto está muito grande", "o contexto tá cheio", "abre outra conversa", "faz o handoff", "me dá um prompt pra nova janela" ou "vamos parar por hoje".
---

# Project docs

Último prompt da conversa: ler a sessão, pôr cada fato no arquivo certo,
escrever o HANDOFF e entregar o prompt da próxima janela. Tudo numa resposta
só, pelo processo de [handoff.md](references/handoff.md).

## Arquivos

| Arquivo | Guarda |
|---|---|
| `README.md`, `docs/`, `docs/images/` | O que o projeto é e faz; para humanos, geralmente público |
| `DECISIONS.md` | Decisões que valem entre sessões, com o porquê; fatos verificados |
| `ROADMAP.md` | Só o que falta fazer; para agentes |
| `HANDOFF.md` | Estado atual e próximo passo; só para a próxima sessão |
| `CLAUDE.md` | Como trabalhar no projeto (brief interno) |

Só existem os que fazem sentido. Projeto de documento (proposta, issue,
discussão) costuma ter só HANDOFF, DECISIONS, CLAUDE.md e um ROADMAP de
pendências.

## Regras

- **Estado, não história.** Reversão sobrescreve; o passado fica no git.
- **Só o usuário aprova**, testando e dizendo explicitamente ("aprovado",
  "pode fechar"). Silêncio, mudança de assunto ou "ficou bom" de passagem não
  contam; na dúvida, perguntar.
- **Sugestão da IA não é decisão** até ser aceita. Recusada não é registrada.
- **Edições pontuais**, nunca reescrever um doc inteiro. Aplicar direto e
  listar no relatório; o usuário confere no `git show` do commit (sem git,
  nos arquivos).
- **Commit antes do prompt**, só se a pasta dos docs está num repositório
  git: `git add -A` e um commit com tudo o que estiver pendente, docs e
  trabalho da sessão, meu e do usuário, no idioma e com os passos que o
  CLAUDE.md do projeto pedir. Sem push. Sem git, nada.
- **Idioma** dos docs existentes; em projeto novo, o do usuário.
- **Memória automática só aponta** para os arquivos ("estado do projeto X em
  `<pasta>/HANDOFF.md`"); decisões, fatos e pendências vivem nos arquivos.

## Eventos

| Na sessão | Fazer |
|---|---|
| Ideia aceita, prioridade, trabalho começou, entrega para teste, ajustes, `[ajuste]` | Skill [roadmap](../roadmap/SKILL.md) |
| Item aprovado | Apagar do ROADMAP; documentar no nível certo ([readme.md](references/readme.md)); DECISIONS se houve escolha relevante, inclusive do `Como` do item; `[pesquisa]` vira fato verificado |
| README mudou e há traduções | Item de tradução por idioma ([readme.md](references/readme.md)) |
| Feature de Destaque que o texto não explica | Sugerir imagem ([readme.md](references/readme.md)) |
| Premissa do projeto mudou | **Mudança de rumo** da skill [roadmap](../roadmap/SKILL.md), também para DECISIONS, README e CLAUDE.md |
| Decisão de arquitetura ou processo | DECISIONS; linha no CLAUDE.md se mudar o jeito de trabalhar |
| Fato checado (fonte, teste) | DECISIONS > Fatos verificados |
| Feedback de terceiros | Mapear cada ponto ao item/seção; vira trabalho só se o usuário aceitou |

## Primeira vez num projeto

O projeto segue a convenção se o CLAUDE.md dele tem a linha abaixo ou os
arquivos existem; um `ROADMAP.md` sozinho, criado pela skill roadmap, não
conta. Se não, a primeira pergunta é **adotar** ou **só o prompt**
(prompt autossuficiente, nada criado).

Ao adotar:

1. **Pasta:** raiz do projeto. Em repositório de outra pessoa (fork para
   upstream), nada dentro dele: perguntar onde (por exemplo, pasta irmã).
2. **Arquivos soltos do projeto:** propor "estes → esta pasta" e mover só o
   aprovado (`git mv` se houver git). Não tocar no que não é do projeto.
   Atualizar toda referência ao caminho antigo (docs, CLAUDE.md, memória,
   scripts). Repetir só quando surgirem soltos novos.
3. **Migrar** roadmap ou notas antigos (`ROADMAP.md` já no formato da skill
   roadmap fica como está) e o conteúdo da memória automática para
   os arquivos; reduzir a memória a ponteiro. Não sobrescrever nada.
4. **Criar** os arquivos que faltam pelos modelos das referências.
5. **CLAUDE.md** do projeto (criar se preciso) recebe:

   ```markdown
   Este projeto segue a convenção project-docs (ROADMAP.md, DECISIONS.md, HANDOFF.md).
   Quando o usuário pedir para retomar ("retoma", "vamos continuar o projeto", "vamos continuar o desenvolvimento do roadmap"), antes de agir: ler HANDOFF.md; do ROADMAP.md, só os títulos (`grep "^### R-" ROADMAP.md`) e o item do próximo passo ou do pedido. Confirmar em 3 linhas o estado e o próximo passo e esperar o ok.
   ```

## Depois do prompt de abertura

A conversa acabou ali: não começar trabalho nem oferecer próximos passos. Se o
usuário continuar, lembrar uma vez que o trabalho segue na janela nova; a
escolha é dele.

## Referências

| Ler | Quando |
|---|---|
| [handoff.md](references/handoff.md) | Sempre |
| Skill [roadmap](../roadmap/SKILL.md) | Item criado, movido ou apagado, ou ROADMAP a criar |
| [decisions.md](references/decisions.md) | Decisão nova ou revertida, fato checado, ou DECISIONS a criar |
| [readme.md](references/readme.md) | Item aprovado, README mudou, imagem. O CLAUDE.md global também manda ler ao escrever qualquer README |
