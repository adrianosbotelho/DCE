# Coding Standards — Dev Context Engine (DCE)

**Última atualização:** 2026-07-29  
**Stack-alvo:** Python 3.12+, ruff, mypy, pytest

---

## 1. Objetivos

Código legível daqui a anos, fácil de testar, difícil de acoplar acidentalmente. Preferir clareza a cleverness.

---

## 2. Estilo e ferramentas

| Ferramenta | Papel |
|------------|--------|
| **ruff** | Lint + format (substituir black/isort/flake8) |
| **mypy** | Type checking estrito no pacote `dce` |
| **pytest** | Testes |

- Line length: **100** (ruff)
- Aspas: preferir double em novos arquivos (alinhar ruff)
- Python: `>=3.12` (usar `list`, `dict`, `X | Y`, `match` quando legível)

Nenhum `--no-verify`. Hooks locais opcionais; CI é a rede de segurança.

---

## 3. Type hints e docstrings

- Type hints **obrigatórios** em assinaturas públicas e quase tudo em domain/application.
- Docstrings em módulos públicos, classes públicas e funções públicas — estilo Google ou Sphinx curto; **uma linha** quando óbvio.
- Evitar comentários que repetem o código; comentar **porquês** e trade-offs locais.

---

## 4. Arquitetura no código

### 4.1 Dependências

```text
interfaces → application → domain
infrastructure → domain (e implementa ports)
application → ports (Protocol), não classes concretas de infra
```

Composition root (`build_container` / `main`) é o **único** lugar que amarra concretos.

### 4.2 Tamanho

- Arquivos pequenos; classes pequenas; funções pequenas.
- Se uma função precisa de “seção com comentário H2”, divida.
- Evitar god-objects (`ContextBuilder` orquestra, mas delega plan/assemble/rank).

### 4.3 SOLID (pragmático)

- **S:** indexer não ranqueia pacote final  
- **O:** novo indexer sem editar Builder  
- **L/I:** Protocols focados (`DocumentRepository` não vira “UnitOfWorkMega”)  
- **D:** application depende de Protocol  

Não criar interface “por SOLID” sem segundo uso ou teste com fake.

---

## 5. Pydantic e dados

- Modelos de domínio/API com Pydantic v2.
- `model_config` explícito quando necessário (`extra="forbid"` em inputs MCP/CLI).
- JSON de metadata: validar na borda do indexer, não no SQL solto.

---

## 6. Persistência

- SQL explícito; sem ORM no MVP.
- Migrations versionadas e testadas.
- Sem strings SQL espalhadas em use cases — só no repositório.
- Sempre usar parâmetros bind (`?`) — nunca f-string com input.

---

## 7. Indexers

- Sem import cruzado entre indexers.
- `transform` puro e testável (bytes/path → `Document`).
- Guard contra path traversal e symlinks perigosos.
- Idempotência: mesmo URI → mesmo `id` → upsert.

---

## 8. MCP / CLI

- CLI: Typer; saída humana com Rich; máquina com `--format json`.
- MCP: retornar modelos estruturados; erros com código estável.
- Não logar secrets (tokens Jira).

---

## 9. Logging

- Logging estruturado (key=value ou JSON).
- Níveis: DEBUG para diagnostics internos; INFO para operações; WARNING recuperável; ERROR falha.
- Sem `print` em library code.

---

## 10. Dependências

Toda dependência nova exige:

1. Justificativa escrita (PR ou ADR se arquitetural)
2. Manutenção ativa / licença OK
3. Alternativa stdlib considerada

**Proibido:** clientes OpenAI, SDKs de vector DB, telemetria paga.

---

## 11. Testes no fluxo de desenvolvimento

- Código de produção sem teste do comportamento novo = incompleto.
- Preferir testes de comportamento a testes de implementação frágil.
- Fixtures pequenas em `tests/`; sem depender de Jira real.

---

## 12. O que não fazer

- Código morto, TODOs eternos sem issue, abstrações “para o futuro”
- `Any` sem necessidade
- Catch genérico `Exception` engolindo erro
- Monkeypatch de rede escondendo violação offline
- Arquivos &gt; ~400 linhas sem motivo forte (cheiro — fatiar)

---

## 13. Revisão arquitetural (por sprint)

Checklist rápido:

- [ ] Ports intactas?
- [ ] Novo acoplamento entre indexers?
- [ ] Builder ainda agnóstico de fonte?
- [ ] Resposta MCP/CLI ainda estruturada?
- [ ] Budget respeitado onde aplicável?
