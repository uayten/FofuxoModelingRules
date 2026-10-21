---
name: blender-pull-requests
description: Como preparar e abrir pull requests para o Blender no projects.blender.org (Gitea) - política de contribuição com IA do Blender, formato de título de commit/PR (prefixos Rigify, Fix, WIP), descrição como mensagem de commit, fluxo fork/upstream, make format, testes, revisores, labels e etiqueta de revisão. Use sempre que o trabalho for para o repositório do Blender ou seus add-ons embutidos (Rigify, pose_library, scripts/addons_core etc.), incluindo abrir, rascunhar ou atualizar um PR do Blender, escrever o título ou a descrição, preparar uma branch para revisão, propor um PR de design/WIP, ou responder revisão no projects.blender.org. Use junto com a skill genérica pull-requests; onde elas divergirem, esta vale.
---

# Blender Pull Requests

Parte da skill genérica `pull-requests`. Tudo aqui é específico de
`https://projects.blender.org/blender/blender` e sobrepõe as regras genéricas.

Fontes oficiais (reler se algo aqui parecer desatualizado):

- Contributing: https://developer.blender.org/docs/handbook/contributing/
- Pull requests: https://developer.blender.org/docs/handbook/contributing/pull_requests/
- AI contributions: https://developer.blender.org/docs/handbook/contributing/ai_contributions/
- Commit messages: https://developer.blender.org/docs/handbook/guidelines/commit_messages/

## 1. Política de contribuição com IA (obrigatória)

Os mantenedores do Blender podem fechar um PR sem revisão se ele quebrar estas
regras. Elas existem porque o tempo de revisão é o recurso mais escasso do
projeto.

- **Sem atribuição de IA nos commits.** Só humanos podem ser autores de commit
  ou `Co-authored-by`. Neste repositório, **não** acrescentar o trailer
  `Co-Authored-By: Claude ...` (nem nenhum trailer de IA) aos commits, mesmo
  que a atribuição padrão da sessão mande. O usuário é o autor e o responsável.
- **O usuário precisa entender e testar tudo.** Nunca entregar código que o
  usuário não revisou e rodou. Antes de propor publicar, garantir que o usuário
  testou a mudança no Blender, e dizer claramente se ele não testou.
- **O usuário escreve a descrição do PR e as respostas da revisão.** O Claude
  pode rascunhá-las, mas apresentá-las como rascunho para o usuário reescrever
  com as próprias palavras. Texto colado tal qual de uma ferramenta precisa ser
  marcado como tal. Correções de gramática e clareza no texto do próprio
  usuário não têm problema.
- **Em mudanças substanciais, descrever o método.** Uma nota curta sobre como o
  trabalho foi feito (incluindo a ajuda de IA) ajuda os revisores a achar
  pontos cegos.
- **Não resolver tarefas "Good First Issue" com IA.** Elas existem para ensinar
  quem está chegando. Se o usuário escolher uma, apontar isso.
- **A contribuição precisa acrescentar valor além da ferramenta.** O
  julgamento, os testes e o design do próprio usuário devem aparecer no PR.

## 2. Configuração do repositório (deste usuário)

- Clone local: `C:\Dev\Blender-git\Blender`
- `origin` = o fork do usuário `https://projects.blender.org/Antonio-Froz/blender.git`
- `upstream` = `https://projects.blender.org/blender/blender.git`
- Saída do build: `C:\Dev\Blender-git\build_windows_x64_vc18_Release`
  (compilado com `make_blender_ninja.bat`; os scripts embutidos são copiados
  para `bin/<version>/scripts`, então recompilar ou copiar depois de editar
  Python antes de testar nesse build).

Começar todo PR a partir do upstream atualizado, nunca de outra branch de
feature:

```bash
git -C /c/Dev/Blender-git/Blender fetch upstream
git -C /c/Dev/Blender-git/Blender switch -c <topic> --no-track upstream/main
```

Conferir `git branch --show-current` antes: o usuário costuma ter outras
branches de feature em uso (por exemplo `rigify-action-copy-rig`).

## 3. Título = título do commit

O título e a descrição do PR viram a mensagem do squash commit, então
escrevê-los como uma coisa só.

- `<Module>: <what changes>`: o prefixo nomeia a área que o usuário vê, e o
  mais específico vence. Para o Rigify, usar `Rigify:`, não `Anim:` nem
  `Anim: Rigify`. Outros exemplos: `Cycles:`, `Sculpt:`, `UI:`, `Python API:`.
- Correção de bug: `Fix #12345: <symptom>`, ou `Fix: <symptom>` quando não há
  report.
- Sem mudança funcional: `Cleanup:` ou `Refactor:`.
- Não pronto / esperando acordo de design: prefixo `WIP: `.
- Máximo de 72 caracteres, inglês americano, imperativo ou descritivo, sem
  ponto final.

Para acertar o estilo local, olhar o que de fato foi aceito:

```bash
git log upstream/main --format="%s" -15 -- <path>
```

Exemplo real (o PR #161401 do usuário): enviado como
`Anim: Rigify add max=32 to shared B-Bone Segments parameter`, aceito como
`Rigify: add max=32 to shared B-Bone Segments parameter`.

## 4. Descrição

A descrição do PR é o documento do revisor; quem faz o merge depois a condensa
na mensagem do squash commit (ver o exemplo no fim desta seção).

### Seções (features e melhorias)

Vêm de "Ingredients of a Pull Request" no handbook de Contributing, mais a
seção Tests que o usuário sempre acrescenta. Manter esta ordem: quem lê o
histórico do git procura a razão do design e precisa do problema primeiro.

```
**Problem:**
**Motivation:**
**Proposed Solution:**
**Rejected alternatives and why:**
**Limitations:**
**Interface Mock-up:**
**Tests:**
```

- **Problem**: o que está errado ou faltando, no nível do usuário.
- **Motivation**: cobrir os dois lados. Por que o problema importa para os
  usuários (por exemplo, rigs exportados para game engines), *e* por que esta
  solução é a melhor. A segunda parte é o que o handbook realmente pede: lá, a
  motivação está ligada à solução, não ao problema, e é a parte mais fácil de
  esquecer.
- **Proposed Solution**: o que o PR faz. Sub-itens numerados funcionam bem:
  Code / Interface / Behavior. Declarar a compatibilidade aqui: arquivos
  `.blend` antigos e a API Python continuam funcionando, ou como são migrados.
- **Rejected alternatives and why**: outras opções e por que são piores.
- **Limitations**: o que não resolve, e restrições que introduz.
- **Interface Mock-up**: duas partes, ambas obrigatórias. A imagem (screenshot
  ou mock-up) e uma descrição escrita de como o usuário interage com ela: onde
  aparece, o nome do campo, faixa e padrão, e o que muda quando é usado. Só a
  imagem não satisfaz o handbook.
- **Tests**: o que foi testado e como, concretamente.

### Apêndices (depois de `---`)

As seções acima são o PR em si. Tudo o que o enriquece sem fazer parte dele vai
depois de uma linha `---`, nesta ordem:

- **Images**: screenshots e mock-ups, com rótulo ("Image 1") e referenciados
  nas seções acima.
- **References**: `Fix #N` / `Ref #N`, design task, PRs relacionados,
  discussão no chat ou devtalk.
- **Method**: em mudanças substanciais, uma nota curta sobre como o trabalho
  foi feito, incluindo a ajuda de IA (política de IA).
- **Original Text in Brazilian Portuguese** (ver abaixo), sempre por último.

Algumas frases por seção bastam; tirar as seções que não se aplicam.

**Correção de bug usa outra estrutura.** As seções acima são para features
novas e melhorias (o handbook as apresenta com "before adding a new feature").
Uma correção de bug segue o guia de mensagens de commit:

- Título: `Fix #N: <symptom as the user sees it>`, ou `Fix: <symptom>` quando
  não há report.
- Corpo: exatamente qual era o problema, do ponto de vista do usuário; depois,
  opcionalmente, a causa técnica e como a correção a resolve.
- Manter **Tests** (como a correção foi verificada, de preferência com os
  passos de reprodução do report). Rejected alternatives e Interface Mock-up
  geralmente não se aplicam.

### Texto original em português

O usuário escreve a descrição em português do Brasil e publica a versão em
inglês seguida de `---` e do original num bloco recolhível
`<details><summary>Original Text in Brazilian Portuguese</summary>` (formato
completo na skill `pull-requests`). É assim que a política de IA é cumprida: o texto é do próprio
usuário, e a tradução é transparente. Ao ajudar, traduzir ou polir o texto em
português do usuário; se o Claude rascunhar conteúdo do zero, apresentá-lo como
rascunho para o usuário reescrever em português primeiro.

### Estilo

- Markdown funciona na descrição (o Gitea mostra títulos em negrito, listas e
  imagens). Colocar as imagens depois do texto que as descreve.
- Painéis recolhíveis (`<details><summary>`) funcionam. Sumário clicável não:
  no projects.blender.org, os títulos em descrições de issue não recebem id
  nenhum (dentro ou fora de painéis), e âncoras manuais (`<a id>`,
  `<a name>`) também não funcionam. Verificado na issue #164635, 2026-10-03.
  Usar títulos numerados (`## 1. Problem`) para dar estrutura.
- Imagens precisam ser enviadas arrastando o arquivo para o editor. Um caminho
  local em `![...](...)` aparece como imagem quebrada.
- Não quebrar linhas na descrição: o Gitea mostra cada quebra simples como
  quebra de linha visível. Escrever cada parágrafo e cada item de lista numa
  linha só, com linhas em branco entre parágrafos. Quebra em 72 colunas é só
  para mensagens de commit.
- Usar os nomes da UI ("B-Bone Segments slider in the spine rig settings"), com
  nomes de código entre crases só onde ajudarem.
- Afirmações de desempenho precisam de números.
- A nota de GPL / AUTHORS do modelo não exige ação, a menos que o usuário
  queira ficar fora do AUTHORS.

### O que vai parar no git

Quem faz o merge dá squash e geralmente reescreve a descrição numa mensagem de
commit curta (texto puro, 72 colunas). No PR #161160, a descrição longa com
seções virou:

```
Rigify: expose B-Bone segment count for spine and head rig types

Add a property + UI field for editing the B-Bone segments, identical
in appearance to the ones that already exist in other rig types that
use `bbones` from `rigify_parameters`, such as `limbs.leg` and
`limbs.arm`.

The default values are still the same, so this is a
backward-compatible change.
```

Por isso a Proposed Solution deve conter uma ou duas frases que se sustentem
sozinhas e possam ir direto para o commit: o que o usuário ganha, e se é
compatível com versões anteriores.

## 5. Antes do push

- **Formatação**: `make format` (na raiz do repositório; no Windows
  `make.bat format`). Roda clang-format para C/C++ e autopep8 para Python.
- **Testes**: rodar os testes relevantes se a área tiver
  (`tests/python/bl_animation*` para animação). O Rigify não tem testes
  automáticos de geração: gerar os metarigs embutidos que usam os tipos de rig
  alterados (por exemplo Human, Basic Human, Horse, Cat, Wolf) no Blender
  compilado, e comparar com o comportamento do upstream.
- **Compatibilidade**: arquivos salvos em versões antigas ainda precisam abrir
  e regenerar. Renomear uma propriedade de `rigify_parameters` quebra metarigs
  salvos, a menos que um código de versioning a migre.
- **Revisão própria** com os comandos da skill genérica. Arquivos que sobram
  neste checkout (`*.blend1`, `*.blendgit`, saída do build) nunca podem ser
  commitados.

## 6. Publicar

Mostrar ao usuário base, head, commits, título e descrição, e esperar um sim
explícito antes do push (ver a skill genérica). Então:

```bash
git -C /c/Dev/Blender-git/Blender push -u origin <topic>
```

O usuário muitas vezes dá push pelo GitHub Desktop. Uma branch nova sem
rastreamento mostra **Publish branch**, que dá push no `origin`. Se aparecer
"Pushing to upstream" e ele pedir credenciais, a branch está rastreando o
`upstream`: cancelar, rodar `git branch --unset-upstream <topic>`, e publicar
de novo.

Autenticação: a conta tem 2FA, então push por HTTPS usa um access token
(projects.blender.org > Settings > Applications, token `github-desktop`,
escopo repository read/write) como senha, com o usuário `Antonio-Froz`. Um push
que falhou no remoto errado pode fazer o Git Credential Manager descartar o
token salvo. Se o GitHub Desktop continuar falhando,
`git push -u origin <topic>` no terminal mostra o erro real e a janela de login
do próprio Credential Manager.

O Gitea não tem um CLI no estilo do `gh` aqui, e o Claude não deve manusear os
tokens do usuário. A própria saída do push imprime o link para abrir o PR
(confirmado em 2026-10-02):

```
https://projects.blender.org/Antonio-Froz/blender/pulls/new/<topic>
```

Dizer ao usuário para conferir se a base é `blender/blender` : `main`, não o
fork. No formulário:

- Colar o título e a descrição.
- Deixar **Allow edits by maintainers** ligado.
- Acrescentar a label do módulo (por exemplo `Module/Animation & Rigging`) e a
  label `Interest/...` da área, se alguma couber.
- Pedir revisão a **pessoas**, não a times. Achar o dono do caminho em
  `.gitea/CODEOWNERS` (Rigify: `@dr.sybren`). Quem se ofereceu no chat para
  revisar (para o Rigify: icappiello, antigo mantenedor) também pode ser
  acrescentado.

A checagem de CLA roda automaticamente no primeiro PR.

## 7. Propostas de design e WIP

- Para um plano ou design sem código, usar uma issue de **Design**
  (`Type/Design`, modelo `.gitea/issue_template/design.yaml`) e/ou um tópico no
  devtalk em https://devtalk.blender.org, não um PR. Um PR com o plano de
  refatoração (#164626) foi respondido em um dia com "this should be an Issue".
  Um PR `WIP:` só cabe quando traz um protótipo.
- Regras de issue: issues em branco estão desativadas; os tipos são Bug Report
  (via *Help > Report a Bug*), Python API Documentation, Design e To Do. Design
  e To Do dizem "for developers only", mas contribuidores com PRs aceitos que
  propõem trabalho que eles mesmos vão fazer também abrem. Pedidos de feature
  de usuários vão para o Right-Click Select (rightclickselect.com), não para o
  tracker.
- Uma issue de Design tem descrição livre. Manter as seções de PR que se
  aplicam (Problem, Motivation, Proposal, Limitations, Open questions, e os
  apêndices depois de `---`) e tirar as que só fazem sentido para código
  (Rejected alternatives sem nada rejeitado, Interface Mock-up, Tests). Sem
  prefixo `WIP:`.
- Conseguir o acordo do módulo antes de investir numa mudança grande. Levar o
  assunto ao chat do módulo (`#module-animation:blender.org` para Animation &
  Rigging) ou pedir para incluir na pauta da reunião semanal do módulo.
- Preferir uma sequência de PRs pequenos a uma grande refatoração: um diff
  grande sem um mantenedor ativo por trás trava na revisão.

## 8. Durante a revisão

- Antes de a revisão começar: amend/rebase e force-push à vontade.
- Depois que a revisão começa: acrescentar commits novos, sem force-push, para
  os revisores verem o que mudou.
- Resolver uma conversa só quando a mudança foi feita; deixá-la aberta se
  houver discordância.
- Depois de atender ao feedback, usar **Re-request review** em vez de um
  comentário cutucando.
- `@blender-bot build` (buildbot em todas as plataformas) é acionado pelos
  revisores num comentário; o autor não precisa pedir.
- Os revisores tentam responder em cerca de 3 dias úteis. Depois disso, um
  lembrete educado no chat do módulo não tem problema.
- Manter a descrição atualizada: quem faz o merge geralmente dá squash usando
  ela.
