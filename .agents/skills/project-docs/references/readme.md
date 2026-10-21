# README e docs

Vale para qualquer README, com ou sem project-docs. O README descreve o
projeto para quem chega sem contexto; não é um catálogo de features.

## Estrutura

- Sumário com links logo depois da abertura.
- Primeiro o que dá para fazer com o projeto; a história de por que ele existe
  vem depois.
- Idioma: ver [Idiomas e traduções](#idiomas-e-traduções).
- Seção que cresce além do que um recém-chegado precisa vai para
  `docs/<assunto>.md`, deixando uma frase e o link: "Para mais detalhes, veja
  [docs/x.md](docs/x.md)."
- Nada de itens do ROADMAP, IDs internos ou trabalho não aprovado.

## Níveis de feature

Ao aprovar um item, documentar num nível. Padrão: o mais baixo que couber; o
usuário promove.

| Nível | Onde |
|---|---|
| Destaque | Menção própria no README |
| Secundária | Uma linha no README, ou só no doc da área |
| Descoberta | Só tooltip/UI ou docs da área |

Um `[ajuste]` muda o texto existente, sem entrada nova.

## Idiomas e traduções

- **Principal em português:** `README.pt-BR.md`. É nele que se escreve e se
  edita; os outros são traduções dele.
- **`README.md` em inglês, secundário.** É o que o GitHub mostra na página do
  repositório. Enquanto não tiver o mesmo conteúdo do principal, abre com o
  aviso abaixo (antes do título) e fica só com título, frase de abertura,
  "in development" e licença:

  ```markdown
  > [!TIP]
  > The full documentation is in Brazilian Portuguese for now: **[README.pt-BR.md](README.pt-BR.md)**.
  ```

  Atualizado, perde o aviso e fica só com os links de idioma.
- **Links de idioma** no topo de cada README, marcando o desatualizado:
  `**Português** · [English](README.md) (em desenvolvimento)`.
- **Projeto novo:** nascer com os dois arquivos, o `README.md` no formato de
  esboço acima.
- **Projeto próprio só com README em inglês:** no primeiro pedido de mexer
  nele, propor criar o `README.pt-BR.md` como principal; não converter sem ok.
- **Repositório de outra pessoa** (fork para upstream, Blender): seguir o
  idioma e os arquivos do projeto; nada desta seção vale.
- **Outras traduções** (`README.ja.md`...) ficam ao lado, também a partir do
  principal.
- Quando o principal muda, não traduzir: garantir um item por idioma
  desatualizado no fim de `A fazer`. Se já existe, não duplicar; um item cobre
  as mudanças acumuladas.

```markdown
### R-031 [ajuste] Atualizar README.ja.md
Ajusta: README.ja.md
Esperado: README.ja.md com o mesmo conteúdo do README.pt-BR.md atual.
```

## Imagens

Raras. Só em features de Destaque que o texto não explica; nunca em
sub-tópicos nem nos docs satélite. Mostram o funcionamento, não a interface em
detalhe, para continuarem verdadeiras quando a UI mudar. Ficam em
`docs/images/` (ou na pasta que o projeto já tem), com caminho relativo.

Sugerir só nesse caso; na dúvida, não. Dizer o que mostrar, onde e o nome do
arquivo. Aprovada vira item (o usuário captura, o agente insere a
referência); recusada não é registrada.

```markdown
### R-032 [ajuste] Imagem: retargeting de uma animação
Ajusta: README.md > Retargeting
Esperado: docs/images/retargeting.png com o rig de origem e o de destino lado a lado na mesma pose, abaixo do título da seção.
```
