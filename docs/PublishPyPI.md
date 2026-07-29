# First publish — PyPI Trusted Publisher

**Status:** Sprint 35 (`1.19.0`)  
**Package:** `dev-context-engine`  
**Repo:** `adrianosbotelho/DCE`  
**GitHub environment:** `pypi` (already created)

O pacote ainda **não** existe no PyPI. Use um **Pending Trusted Publisher** — o primeiro upload cria o projeto.

## Passo 1 — Pending publisher (manual, maintainer)

1. Login em https://pypi.org (conta com 2FA).
2. Account settings → **Publishing** → *pending publisher*  
   Docs: https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/
3. Preencher **exatamente**:

| Campo | Valor |
|-------|--------|
| PyPI Project Name | `dev-context-engine` |
| Owner | `adrianosbotelho` |
| Repository name | `DCE` |
| Workflow name | `publish.yml` |
| Environment name | `pypi` |

4. Save / Add.

## Passo 2 — Disparar Publish

```bash
gh workflow run publish.yml --repo adrianosbotelho/DCE -f target=pypi
gh run watch --repo adrianosbotelho/DCE
```

Ou: GitHub → Actions → **Publish** → Run workflow → `pypi`.

## Passo 3 — Smoke

```bash
pip install dev-context-engine==1.19.0   # use a versão da tag publicada
dce --version
```

## Fallback (token)

Se preferir API token em vez de OIDC:

```bash
export PYPI_TOKEN=pypi-...
./scripts/publish.sh --upload
```

## Verificação correlata

- Windows ZIP: https://github.com/adrianosbotelho/DCE/releases  
- Checklist geral: [`ReleaseVerify.md`](ReleaseVerify.md)
