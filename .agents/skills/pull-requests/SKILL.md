---
name: pull-requests
description: Como preparar e abrir bem um pull request, em qualquer plataforma (GitHub, Gitea, GitLab, Forgejo) - criar a branch a partir da base certa, delimitar a mudança, revisar antes, escrever título e descrição, publicar com segurança e lidar com a revisão depois. Use sempre que o usuário quiser abrir, preparar, rascunhar, atualizar ou dividir um PR / merge request / patch, subir uma branch para revisão, escrever a descrição de um PR, transformar um plano num PR de rascunho ou responder a uma revisão, mesmo que ele diga só "manda pro upstream", "abre o PR" ou "prepara isso pra revisão". Se existir uma skill de PR específica do projeto (por exemplo blender-pull-requests), use-a também, porque ela sobrepõe as regras genéricas daqui.
---

# Pull Requests

Um pull request é um pedido do tempo de um desconhecido. Tudo abaixo serve a um
objetivo: deixar o trabalho do revisor curto e a decisão óbvia. Um PR pequeno,
focado e com um "porquê" claro é aceito; um grande com descrição vaga fica
esperando.

## 0. Ver as regras do projeto primeiro

Antes de tudo, procurar as convenções do próprio projeto, porque elas valem
mais que esta skill. A única exceção é a estrutura da descrição da seção 6:
manter as seções dela e encaixar os campos do modelo do projeto em volta,
a menos que o projeto exija explicitamente outro formato.

- Uma skill específica do projeto (por exemplo `blender-pull-requests`). Se
  houver uma que se aplique, segui-la e usar este arquivo só para o que ela não
  cobre.
- `CONTRIBUTING.md`, o modelo de PR (`.github/pull_request_template.md`,
  `.gitea/pull_request_template.yaml`, `.gitlab/merge_request_templates/`),
  `CODEOWNERS`, e o handbook/docs para onde eles apontam.
- A política do projeto sobre contribuições feitas com IA, se houver.
- PRs recentes aceitos na mesma área: `git log upstream/main -- <path>` mostra
  o formato real dos títulos e o tom melhor que qualquer guia.

## 1. Está pronto?

Um PR é o "salvar" de uma mudança validada, não um backup de trabalho em
andamento. Antes de preparar um, confirmar com o usuário que a mudança foi
testada e funciona. Se não foi, dizer isso e oferecer testar antes, ou abrir
explicitamente como rascunho/WIP.

Exceção: um PR só de design ou WIP (um plano, uma proposta, um protótipo para
discussão) pode ir sem testes, desde que o título e o status digam isso.

## 2. Branch a partir da base certa

- `git fetch upstream` (ou `origin` quando não há fork), e então criar a branch
  a partir da base atualizada: `git switch -c <topic> --no-track upstream/main`.
  O `--no-track` importa: sem ele a branch rastreia o `upstream`, e clientes
  gráficos (GitHub Desktop) passam a dar push no repositório original, onde o
  usuário não tem permissão de escrita, e pedem credenciais.
- Nunca criar a branch a partir de outra branch de feature, a menos que o PR
  deva depender dela. Conferir `git branch --show-current` antes: estar numa
  branch de feature sem relação é o jeito mais comum de commits alheios
  vazarem para um PR.
- Um assunto por branch, com o nome da mudança (`rigify-spine-bbones`,
  `fix-crash-on-undo`), não da pessoa ou da data.

## 3. Escopo

- Uma mudança lógica por PR. Separar limpezas, renomeações e formatação em PRs
  próprios: diffs misturados escondem a mudança real.
- Se a mudança for grande, propor dividi-la numa sequência de PRs que se
  sustentem sozinhos e deixem o projeto funcionando.
- Não mexer em linhas sem relação "já que está ali".

## 4. Commits

- Seguir a convenção de mensagem do projeto (prefixo, tamanho, tempo verbal).
  Se não houver nenhuma documentada, usar: título curto no imperativo com menos
  de ~72 caracteres, linha em branco, corpo explicando o porquê.
- Escrever as mensagens em inglês, a menos que o projeto diga outra coisa.
- Antes de a revisão começar, reescrever o histórico (amend, rebase) não tem
  problema. Depois que ela começa, acrescentar commits novos em vez de dar
  force-push, para os revisores verem o que mudou desde a última olhada - a
  menos que o projeto peça outra coisa.

## 5. Revisar antes de publicar

Rodar, e ler a saída você mesmo:

```bash
git fetch upstream
git log --oneline upstream/main..HEAD
git diff --stat upstream/main...HEAD
git diff upstream/main...HEAD
```

Conferir:

- Commits ou arquivos que não pertencem ao PR (de outra branch, arquivos
  gerados, configuração local, arquivos `.blend1`/backup, prints de debug,
  código comentado).
- O formatador e os linters do projeto (`make format`, `pre-commit` etc.).
- Os testes relevantes para a mudança, rodados localmente.
- Compatibilidade com versões anteriores: arquivos salvos, API pública,
  configurações.

Se algo estiver errado, corrigir antes de seguir.

## 6. Título e descrição

O revisor lê o título e a primeira seção e decide quanta atenção dar. Escrever
para alguém que conhece o projeto mas não a sua mudança. Este é o formato
preferido do usuário em qualquer repositório; o modelo ou a convenção de um
projeto acrescenta a ele, não tira.

**Título**: o que muda, do ponto de vista do usuário, no formato do projeto
(por exemplo `Area: what changes`, `Fix #N: symptom`), com menos de ~72
caracteres. Nada de "Update file.py" ou "Fix bug".

### Seções (features e melhorias)

Manter esta ordem: o problema vem primeiro, porque quem lê o histórico depois
está procurando por que o design é do jeito que é.

```markdown
**Problem:**
**Motivation:**
**Proposed Solution:**
**Rejected alternatives and why:**
**Limitations:**
**Interface Mock-up:**
**Tests:**
```

- **Problem**: o que está errado ou faltando, do ponto de vista do usuário, em
  2-3 frases.
- **Motivation**: os dois lados. Por que o problema importa para os usuários,
  *e* por que esta solução é a melhor. A segunda parte é a mais esquecida.
- **Proposed Solution**: o que o PR faz, com os nomes que o usuário vê, e nomes
  de código entre crases só onde ajudarem. Terminar com a compatibilidade: se
  arquivos, APIs, configurações e fluxos existentes continuam funcionando, ou
  como são migrados. Fazer a primeira ou as duas primeiras frases se
  sustentarem sozinhas: os mantenedores muitas vezes as copiam direto para a
  mensagem do squash commit.
- **Rejected alternatives and why**: lista numerada, uma ou duas linhas cada.
- **Limitations**: o que não resolve, e restrições que introduz (por exemplo,
  código duplicado que precisa continuar sincronizado).
- **Interface Mock-up**: só para mudanças com UI. Duas partes: um screenshot ou
  mock-up, *e* uma descrição escrita de onde aparece, o nome, faixa/padrão, e o
  que muda quando é usado.
- **Tests**: lista numerada de verificações concretas, cada uma com o resultado
  ("setting 1 generates 1 segment"), não "testado e funciona".

**Apêndices (depois de `---`)**: as seções acima são o PR em si. Tudo o que o
enriquece sem fazer parte dele vai depois de uma linha `---`, nesta ordem:
**Images** (com rótulo e referenciadas nas seções), **References**
(`Fixes #123`, `Ref #456`, PRs relacionados, discussões), **Method** (como o
trabalho foi feito, incluindo a ajuda de IA, quando o projeto pede ou a
mudança é substancial), e o texto no idioma original por último.

Tirar as seções que não se aplicam. Para correção de bug, usar uma forma mais
curta: título `Fix #N: <symptom>`, o problema como o usuário vê, opcionalmente
a causa e a correção, e então **Tests** com os passos de reprodução.

### Estilo

- Curto. Um parágrafo pequeno ou uma lista numerada curta por seção; uma
  mudança simples deve ser lida em menos de um minuto. Prolixidade faz o
  revisor suspeitar que o texto não foi escrito com cuidado (ou foi gerado).
- Afirmações honestas e mensuráveis: "mais rápido" precisa de um número,
  "corrige todos os casos" precisa de evidência.
- Não quebrar linhas no texto que vai para o formulário web (descrição de PR ou
  issue, comentários): o Gitea e algumas outras plataformas mostram cada quebra
  simples como quebra de linha. Uma linha por parágrafo e por item de lista;
  quebrar só mensagens de commit.
- Manter atualizado: quando o escopo muda durante a revisão, atualizar a
  descrição, porque ela muitas vezes vira a mensagem do merge commit.
- A descrição sempre tem o texto original em português: o usuário escreve em
  português e publica em inglês. Acrescentar o original por último, depois de
  `---`, sempre dentro de um bloco recolhível (GitHub e Gitea renderizam
  `<details>`), com linhas em branco depois do `<summary>` e antes do
  `</details>`, senão o Markdown de dentro não é formatado:

  ```markdown
  <details>
  <summary>Original Text in Brazilian Portuguese</summary>

  (texto em português)

  </details>
  ```
- Quando o Claude rascunha o texto, apresentá-lo como rascunho para o usuário
  revisar, e dizer isso.

### Exemplo

Um PR pequeno de feature neste formato (publicado em inglês):

```markdown
**Problem:**
The spine, head and tail rig types always generate their deform bones
with 8 B-Bone segments. Unlike limbs, there is no setting for it, so
changing it means editing the generated rig after every generation.

**Motivation:**
Rigs exported to game engines can't use B-Bone segments. A dedicated
parameter keeps the current default (8), so existing metarigs regenerate
exactly as before.

**Proposed Solution:**
Add a "B-Bone Segments" field to the spine, head and tail rig types,
matching the field limbs already have. The default is the previous
hard-coded value, so this is backward compatible.

**Rejected alternatives and why:**
1. Reuse `bbones`: its default is 10, so existing rigs would change.
2. Redefine `bbones` with default 8: Rigify warns about the redefinition
   and the result depends on rig registration order.

**Limitations:**
1. The last deform bone of `super_head` stays at 1 segment, unchanged.
2. The definition is duplicated in two base classes and must stay
   identical (commented in the code).

**Interface Mock-up:**
A "B-Bone Segments" slider (1-32, default 8) appears in the rig type
settings of the spine, head and tail rigs. The value is applied to the
deform bones on generation.
[screenshots]

**Tests:**
1. No redefinition warning when reloading the add-on.
2. Default metarigs: deform bones keep 8 segments; setting 1 generates 1.
3. A file saved before this change regenerates unchanged.
```

## 7. Publicar (visível para outros: confirmar antes)

Dar push num remoto e abrir um PR são ações visíveis para outras pessoas e
difíceis de desfazer. Antes de qualquer uma, mostrar ao usuário:

- branch base e branch head,
- a lista de commits,
- o título e a descrição finais,
- status de rascunho ou pronto,

e esperar um sim explícito. A aprovação de um push não vale para o próximo.

Então:

- **GitHub**: `git push -u origin <topic>`, depois
  `gh pr create --base main --head <user>:<topic> --title ... --body-file ...`
  (acrescentar `--draft` para WIP). Depois de abrir, vincular e acompanhar o CI
  com as ferramentas de PR da sessão, se houver.
- **Gitea / Forgejo / GitLab sem CLI**: dar push, e então passar ao usuário a
  URL de comparação (`<host>/<owner>/<repo>/compare/main...<fork-owner>:<topic>`)
  para ele criar o PR pela interface web. Não pedir nem manusear os tokens de
  API dele.

### PRs só de design / WIP

Para um PR que propõe um plano sem código:

- Prefixar o título com o marcador de WIP do projeto (`WIP:`, ou a opção de
  rascunho).
- Algumas plataformas recusam um PR sem mudança de arquivo. Opções, em ordem de
  preferência: o canal de design issue/proposta do projeto, se houver; um
  commit que acrescenta o documento da proposta (declarado como não destinado a
  merge); um commit vazio (`git commit --allow-empty`), se a plataforma aceitar.
- Colocar o plano na descrição, para ser lido sem abrir arquivos.

## 8. Depois de abrir

- Acompanhar o CI; corrigir falhas com commits novos.
- Responder todo comentário de revisão, com uma mudança ou com um motivo.
  Marcar uma conversa como resolvida só quando ela realmente estiver.
- Usar o botão "re-request review" da plataforma em vez de cutucar.
- Se não houver resposta depois do prazo normal do projeto (muitas vezes alguns
  dias úteis), um lembrete educado no chat do projeto não tem problema.
- Manter a descrição atualizada quando o escopo mudar: ela muitas vezes vira a
  mensagem do merge commit.
