# Domain Docs

## Before exploring, read these

- Root `GLOSSARY.md`, or root `GLOSSARY-MAP.md` when present.
- Relevant ADRs in `docs/adr/`.

If these files do not exist, proceed silently. The domain-modeling workflow
creates them only when the project resolves terminology or architectural
decisions.

## File structure

This is a single-context repository. Domain documentation belongs here:

```
/
├── GLOSSARY.md
├── docs/adr/
└── src/
```

## Use the glossary's vocabulary

Use terms defined in `GLOSSARY.md` in issue titles, proposals, hypotheses, and
test names. If a needed concept is absent, reconsider whether the term is
needed or record the gap for domain modeling.

## Flag ADR conflicts

Explicitly identify output that contradicts an existing ADR rather than
silently overriding it.
