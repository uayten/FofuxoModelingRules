---
name: roadmap
description: Cria e mantém o ROADMAP.md de um projeto (só o que falta fazer, para agentes) - transforma ideias aceitas em itens R-NNN com "Esperado", ordena por prioridade e move itens entre A fazer, Em andamento e Em teste. Use sempre que o usuário quiser montar, começar ou mexer num roadmap, inclusive no início da conversa enquanto ainda gera as ideias do projeto, mesmo que diga só "vamos fazer um roadmap", "anota isso no roadmap", "isso entra", "põe isso como próximo", "isso fica pra depois", "tira isso do roadmap", "o que falta?" ou "mudei de ideia, agora vai ser X". Não usar para retomar o trabalho de um roadmap existente ("vamos continuar o roadmap"), que segue o CLAUDE.md do projeto, nem para encerrar a sessão, que é da skill project-docs.
---

# Roadmap

`ROADMAP.md` é para agentes: sem ambiguidade, sem textos de motivação. Só
trabalho pendente; item aprovado é apagado. Esta skill é dona do formato; a
project-docs usa ela no handoff.

## Montar enquanto as ideias surgem

1. **Pasta:** raiz do projeto. Sem pasta de projeto (sessão sem pasta, ideia
   ainda sem repositório), perguntar onde antes do primeiro item; nunca na
   pasta temporária da sessão. `ROADMAP.md` existente: ler os títulos
   (`grep "^### R-"`) e o contador, e acrescentar.
2. **Conversa livre.** Claude pode propor, questionar e juntar ideias, mas o
   item só entra quando o usuário aceita ("entra", "pode pôr", "sim").
   Sugestão da IA não aceita não entra.
3. **Gravar na hora:** cada ideia aceita vira item no arquivo, numa edição
   pontual, com uma linha no chat (`R-004 anotado`). Nada se perde se a
   conversa parar.
4. **Separar as camadas.** O que o usuário quer (abstrato) vai para o
   `Esperado`; como fazer (navegador, HTML, biblioteca), para o `Como`. Fala
   que mistura as duas ("uma interface web em HTML") é separada: `Esperado:
   configurar sem editar arquivos`, `Como: navegador; HTML`. Item sem `Como`
   é normal.
5. **Esperado** nas palavras do usuário. Ideia vaga: uma pergunta para chegar
   nele; se o usuário ainda não sabe, o item entra com o que foi dito e uma
   linha `Em aberto:` com a pergunta. Dúvida que trava vários itens ("áudio
   ou MIDI?") vira item `[pesquisa]` antes deles.
   Ideia grande demais para um teste vira vários itens (ver **Tamanho**).
6. **Ordem:** fim de `A fazer`, antes das traduções, salvo indicação ("isso é
   o primeiro", "isso fica pra depois").
7. **Ideia em dúvida** ("talvez", "vou pensar") não vai para o arquivo; fica
   no chat.
8. **Fechar a rodada** quando o usuário parar de gerar ideias: mostrar só os
   títulos na ordem e perguntar se a prioridade está certa; listar as ideias
   em dúvida, uma linha cada, para entrar ou cair.
9. **Não começar a implementar.** Montar o roadmap não é pedido de trabalho.
   Se o projeto ainda não segue a convenção project-docs, oferecer o handoff
   dela: a implementação começa numa janela nova, e é o handoff que ensina o
   CLAUDE.md do projeto a retomar pelo ROADMAP.

Escolha que vale para o projeto todo, e não para um item, não vai para o
ROADMAP: fica para o DECISIONS no handoff, ou já, se o usuário pedir
([decisions.md](../project-docs/references/decisions.md)).

## Mudança de rumo

Tudo nos arquivos vale até o usuário mudar de ideia. Quando muda uma premissa
(o que o projeto é, para quem, com que entrada: "não é só música, agora é
efeito sonoro também"), não encaixar o novo no desenho velho:

1. **Substitui ou soma?** Se a fala não deixar claro, perguntar.
2. **Mapear** o que dependia da premissa: itens (`Esperado`, `Como`,
   `Depende de`), decisões e fatos (`Por quê`, `Afeta`, `Não escolhido`),
   linhas do CLAUDE.md e do README. Ler só títulos e as entradas citadas.
3. **Pensar do zero:** propor o workflow que se faria se a premissa nova
   fosse a original. Reaproveitar o que já existe só onde encaixa sem forçar,
   dizendo o quê e por quê. Alternativa recusada antes pode voltar a valer.
4. **Esperar o aceite.** Até lá, nada é apagado; a proposta é sugestão.
5. **Aplicar:** apagar o que só existia pela premissa velha (item, decisão,
   fato que não afeta mais nada), reescrever no lugar o que mudou (mesmo
   ID), criar os itens novos. Código já feito para a premissa velha vira item
   `[ajuste]` ou de remoção. Relatório com uma linha por entrada apagada ou
   reescrita.

Sem histórico: o rumo antigo fica no git.

## Modelo

```markdown
# Roadmap

<!-- project-docs: só pendências; aprovado é apagado. Ordem = prioridade. Próximo ID: R-001 -->

## Em teste

## Em andamento

## A fazer
```

## Item

```markdown
### R-012 [feature] Seletor de bone collections na sidebar
Esperado: o que o usuário consegue fazer quando estiver pronto.
Como:
- Painel na sidebar do Viewport
- Lista com busca (escolha do agente)
Depende de: R-009
Em aberto: mostra collections ocultas?
Ajustes pedidos:
- [x] Seletor largo demais em telas pequenas
- [ ] Destacar a collection ativa
```

- **ID** do contador, incrementado na hora, nunca reutilizado.
- **Tipo:** `[feature]` para algo novo; `[ajuste]` para mudar algo aprovado,
  apontando a feature por nome e doc (`Ajusta: Seletor de collections (README
  > Recursos)`), já que o item original não existe mais; `[pesquisa]` para
  uma pergunta que precisa de resposta checada antes de decidir ou construir.
  O `Esperado` dela é a pergunta e o que conta como resposta (`Esperado: qual
  modelo transcreve áudio para notas localmente; testar com 3 músicas`).
- **Esperado:** obrigatório, nas palavras do usuário; é contra isso que ele
  testa.
- **Como:** opcional; as escolhas concretas já feitas. As do usuário valem
  como regra. Sem `Como`, ou onde ele não cobre, o agente pode escolher ou
  perguntar; escolha dele entra com `(escolha do agente)`, para o usuário ver
  e poder trocar no teste. Escolha que vale para o projeto todo vai para o
  DECISIONS, não para o item.
- **Depende de:** opcional.
- **Em aberto:** opcional; perguntas que o usuário ainda não respondeu. Sai
  quando respondida, e a resposta vai para o Esperado ou para o corpo.
- **Ajustes pedidos:** entram depois da primeira entrega. ~90% das entregas
  precisam; é o caminho normal.
- **Design** que só vale para o item vai no corpo, com `####` se ajudar.

## Tamanho

Cada item cabe num teste: o usuário consegue conferir o `Esperado` de uma
vez, ao fim de uma entrega. O que não cabe ("plugin que habilita controles
da Sony e da Nintendo") vira vários itens, cada um testável sozinho
("controle da Sony conectado aparece na Unreal", "botões chegam como input",
"giroscópio"...), ligados por `Depende de:`. O design comum vai no primeiro, e
os outros apontam para ele. Item em `Em andamento` por várias sessões é sinal
de que precisava ser dividido: propor a divisão.

## Eventos

| Na conversa | Fazer |
|---|---|
| Usuário aceitou uma ideia | Item em `A fazer`, na posição indicada (padrão: fim, antes das traduções) |
| Usuário mudou a prioridade | Mover o item; prioridade é posição |
| Usuário desistiu de um item | Apagar |
| Trabalho começou / entrega para teste | Item para `Em andamento` / `Em teste` |
| Ajustes pedidos | Caixinhas no item, marcadas as feitas |
| Item aprovado | O que continuar verdadeiro vai para os docs ([readme.md](../project-docs/references/readme.md)); do `Como`, o que um agente poderia errar ou reabrir vira decisão no DECISIONS (escolha do agente aprovada no teste conta como aceita); depois apagar |
| `[pesquisa]` aprovada | Resposta vira fato verificado no DECISIONS, com fonte; escolha que saiu dela vira decisão; itens que dependiam dela recebem o `Como`; depois apagar |
| Feature aprovada precisa mudar | Item `[ajuste]` |
| Premissa do projeto mudou | **Mudança de rumo** |

## Ciclo

`A fazer → Em andamento → Em teste → aprovado (apagado)`

- Em ajuste, o item fica em `Em teste`; não volta para `Em andamento`.
- Só o usuário tira um item de `Em teste`, testando e dizendo explicitamente
  ("aprovado", "pode fechar").
- Prioridade é posição. Itens de tradução ficam sempre por último.

## Não entra

Sugestão não aceita ou recusada, ideia em dúvida, item concluído, histórico,
bug achado e resolvido na mesma sessão (bug que fica aberto vira item).
