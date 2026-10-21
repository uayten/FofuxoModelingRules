---
name: comment-replies
description: Como ler, traduzir e responder comentários e mensagens em inglês de outras pessoas (issue e PR no GitHub ou Gitea/projects.blender.org, devtalk, Blender Chat/Matrix, Discord), com o usuário ditando em português, Claude corrigindo, verificando os fatos e traduzindo para o inglês no fim. Use sempre que o usuário mostrar, colar ou citar um comentário ou mensagem de alguém, ou disser coisas como "fulano comentou", "traduz isso", "vamos responder o X", "o Mets respondeu", "prepara a mensagem pro Y no chat". Não usar para troca curta (uma pergunta só, uma mensagem rápida de chat): aí basta traduzir no chat e dar uma sugestão de resposta, sem arquivo. Para descrição de PR, use pull-requests / blender-pull-requests.
---

# Responder comentários e mensagens

O usuário publica, em inglês, um texto que é dele: ele decide o conteúdo,
entende cada frase e consegue defendê-la. Claude busca, traduz, corrige,
verifica e traduz de volta. Quem publica é o usuário.

**Troca curta não usa esta skill.** Se a pessoa fez uma pergunta só ou mandou
uma mensagem rápida de chat: traduzir no chat e dar **uma** sugestão de
resposta (em português e em inglês), sem criar arquivo. Os passos abaixo são
para respostas com vários tópicos.

## Os dois arquivos

Toda resposta, de issue ou de chat, curta ou longa, usa dois arquivos em
`drafts/`:

1. **Trabalho, só em português** (ex.: `reply-cloudrig-382.md`). Cada tópico
   que pede resposta fica separado: a tradução do trecho da outra pessoa
   (citação, incluindo o que ela citou) e, embaixo, `**Resposta:**`.
   Perguntas diretas viram tópicos próprios; itens de lista ganham número para
   o usuário responder por número. Marcar *opcional* o que não pede resposta e
   "não precisa responder" o que a pessoa disse ser só para ela. No chat, uma
   tabela resume os tópicos.
2. **Final, só em inglês** (mesmo nome com `-EN.md`). Gerado **apenas no fim**,
   quando o usuário disser que terminou: só o texto a publicar, pronto para
   copiar e colar. Se o português mudar, regenerar o inglês a partir dele.
   O texto para colar sai sempre de arquivo: copiado de uma citação (`>`) do
   chat, ele perde a formatação (vira tudo citação, blocos de código quebram).
   No chat, só mostrar para leitura.

## Buscar

- **Issue e PR pela API**, não pelo navegador (projects.blender.org trava no
  Cloudflare do navegador interno):
  `curl https://projects.blender.org/api/v1/repos/<dono>/<repo>/issues/<n>/comments`
  (vale para PR também); estado e fechamento em `issues/<n>` e
  `issues/<n>/timeline`; branches e arquivos em `pulls/<n>` e
  `pulls/<n>/files`. GitHub: `gh api repos/<dono>/<repo>/issues/<n>/comments`.
  Salvar o JSON no scratchpad e imprimir só o necessário.
- **Chat**: sem API; o usuário cola o texto ou manda captura.
- Mostrar só o que é novo e avisar mudanças de estado (fechada, label, PR
  aberto). Se o comentário aponta para outro item, buscar e resumir o estado
  dele.

## Traduzir para o usuário

No chat: a tradução inteira em citação e, depois, poucas linhas de "o que
importa para você" (consequências, ligação com o que já foi decidido, o que
foi verificado). Mencionar pessoas pelo `@handle`; se alguém assina com outro
nome (o Mets é o Demeter), dizer isso.

## O usuário dita, Claude corrige

- Ele dita no chat ou direto no arquivo (VS Code). Reler o arquivo antes de
  editar.
- **Só gramática.** Manter voz, tom, piadas e emojis. Toda mudança além de
  vírgula e acento é contada numa linha para ele confirmar o sentido.
- **Nada de conteúdo que ele não ditou.** Sugestão vem como opção, com uma
  frase de exemplo; se ele recusar, não repetir.
- Texto escrito por Claude a pedido dele leva `[NÃO REVISADO]` e a lista do
  que ele precisa conferir.

## Verificar antes de publicar

- Todo fato da resposta é verificado (código, teste ou a própria conversa).
  Ex.: "como você disse antes" → procurar nos comentários da pessoa; sem
  achar, perguntar ou suavizar a frase.
- Nomes de UI, canais e links exatos; sem certeza, perguntar.
- Apontar **uma vez** os riscos de tom: rivalidade entre projetos, insistir
  depois de um "não", esconder o uso de IA de quem desconfia dela, oferta
  importante enterrada num texto longo, conversa deixada sem resposta.
- Inglês natural, com o termo que a outra pessoa usaria ("talk", não "video",
  para palestra de conferência).

## Com mantenedores e comunidades

- O pedido ou a oferta principal vai nas primeiras linhas.
- No chat, um assunto por mensagem.
- Mudança grande: conversar antes com quem decide (no Blender, o dono do
  caminho em `.gitea/CODEOWNERS`); issue de design só depois.
- Mantenedores preferem contribuições pequenas. Dizer quem faz o trabalho e
  com quanto tempo.

Depois de publicada, registrar o resultado onde o projeto guarda o estado
(ROADMAP.md / HANDOFF.md em projetos project-docs).
