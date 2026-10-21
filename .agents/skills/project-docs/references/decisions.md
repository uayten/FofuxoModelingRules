# DECISIONS.md

O que um agente poderia errar, reabrir ou checar de novo. Estado atual: o que
mudou é reescrito no lugar, com o mesmo ID; o que não vale mais é apagado. IDs
`D-` e `F-` vêm dos contadores e nunca são reutilizados.

## Modelo

```markdown
# Decisões

<!-- project-docs: só o que vale agora. Próximo ID: D-001 · Próximo fato: F-001 -->

## Decisões

## Fatos verificados
```

## Decisão

Arquitetura, formatos, nomes, dependências, limites de escopo, regras de
processo. Precisa sobreviver à sessão (o temporário vai para o HANDOFF) e vir
do usuário ou ter sido aceita por ele.

```markdown
### D-004 Dados do metarig ficam em custom properties
Decisão: o que vale, em uma ou duas frases.
Por quê: o motivo, para saber quando deixa de valer.
Origem: usuário | sugestão da IA aceita | <terceiro>, <onde>
Não escolhido: <alternativa> - <motivo>
Afeta: CLAUDE.md, docs/metarig.md
```

- **Por quê** obrigatório: sem motivo, o primeiro agente incomodado reverte.
- **Não escolhido:** opcional, só para alternativa recusada com motivo que um
  agente proporia de novo.
- **Afeta:** opcional. Ao mudar a entrada, conferir esses arquivos e o
  CLAUDE.md.
- Se a decisão muda o jeito de trabalhar, uma linha no CLAUDE.md com o ID:
  `- Guardar dados do metarig em custom properties (D-004).`

## Fato verificado

O que foi checado na sessão (fonte consultada, teste feito, código lido) e a
próxima sessão precisaria. Suposição ou fala de terceiro não checada fica
fora.

```markdown
### F-003 O manual do Rigify está completo e atualizado
Fato: inclui a página Generated Rig Features; falta só um guia para quem não programa.
Fonte: docs.blender.org/manual/en/5.3/addons/rigify/
Verificado: 2026-10-03
Afeta: D-002
```

- **Fonte** obrigatória.
- Fato antigo que sustenta decisão importante é checado de novo antes.
