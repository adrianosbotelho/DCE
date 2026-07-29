# Glossary — Dev Context Engine (DCE)

**Última atualização:** 2026-07-29

| Termo | Definição |
|-------|-----------|
| **DCE** | Dev Context Engine — motor de contexto para agentes de IA. |
| **Context Builder** | Componente central que, a partir de uma query/âncora, recupera, ranqueia e monta um `ContextPackage`. |
| **ContextPackage** | Objeto estruturado retornado ao Kiro com seções, documentos ranqueados e diagnostics. |
| **ContextQuery** | Entrada tipada do Builder (texto, âncoras, filtros, budget, mode). |
| **ContextBudget** | Limites de documentos/caracteres/por fonte para não estourar o contexto do agente. |
| **Document** | Unidade canônica indexada, independente da fonte. |
| **source_type** | Tipo da origem (`markdown`, `jira`, `git`, `adr`, `memory`, …). |
| **Indexer** | Componente que descobre itens de uma fonte e os transforma em `Document`. Sem dependência de outros indexers. |
| **Âncora** | Identificador forte na query (ex.: `PROJ-123`, `ORA-12541`, path de arquivo). |
| **RetrievalPlanner** | Escolhe estratégia de busca (fontes, quotas) com base na query. |
| **PackageAssembler** | Dedupa, ordena, aplica budget e preenche seções do pacote. |
| **FTS5** | Full-Text Search do SQLite usado como índice lexical. |
| **BM25** | Ranking lexical padrão do FTS5. |
| **MCP** | Model Context Protocol — interface pela qual o Kiro consome o DCE. |
| **Kiro** | Consumidor principal do DCE (agente/IDE). |
| **Cursor** | Ferramenta usada para *desenvolver* o DCE; não é o consumidor-alvo do runtime. |
| **Memory** | Notas curadas locais; uma fonte (`source_type=memory`), não o produto inteiro. |
| **Workspace** | Unidade operacional local (config + `dce.sqlite`) de um time/projeto. |
| **Diagnostics** | Metadados de recuperação (tempos, hits, truncamentos) embutidos no pacote. |
| **ADR** | Architecture Decision Record — decisão arquitetural versionada. |
| **Offline-first** | Consulta e operação principal sem rede; imports/APIs são ingestão opcional. |
| **Contract test** | Teste que trava o formato de entrada/saída MCP (ou CLI JSON). |
| **Composition root** | Ponto que instancia concretos e injeta dependências. |
| **Port / Protocol** | Interface (typing.Protocol) entre application e infrastructure. |
