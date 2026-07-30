"""Canonical Kiro steering text so the agent uses DCE without every prompt mentioning MCP."""

from __future__ import annotations

STEERING_TITLE = "DCE — quando usar o Dev Context Engine"

STEERING_MARKDOWN = """# DCE — quando usar o Dev Context Engine

Você tem acesso às tools MCP do **Dev Context Engine (DCE)**.

## Quando usar
Use o DCE quando a pergunta depender de **conhecimento interno do workspace**:
bugs corporativos, erros conhecidos (ex.: ORA-*), procedimentos, ADRs,
incidentes, tickets, onboarding técnico, “como a gente resolve X aqui”.

## Como usar
1. Prefira a tool **`build_context`** com o texto da pergunta (ou um resumo curto).
2. Se o índice parecer vazio ou a resposta vier sem docs, chame **`workspace_status`**.
3. Se o escopo for claro, pode usar aliases:
   - `search_by_issue` (ex.: PAY-125)
   - `search_by_project` / `search_by_component` / `search_by_technology` / `search_by_tag`
4. Use `list_facets` se não souber slugs válidos.
5. Respeite `diagnostics.truncated` no `ContextPackage` — o pacote já veio cortado de propósito.

## Quando NÃO usar
Não invoque o DCE para dúvidas genéricas de programação, refatoração do arquivo
já aberto, ou qualquer coisa que não dependa do conhecimento corporativo indexado.

## Estilo
Resuma o contexto do DCE em português claro e cite títulos/URIs dos documentos
quando forem relevantes. Não peça ao usuário para “chamar o MCP” — você chama as tools.
"""


def steering_payload() -> dict[str, str | bool]:
    """Payload for UI / CLI / docs consumers."""
    return {
        "ok": True,
        "title": STEERING_TITLE,
        "steering_markdown": STEERING_MARKDOWN.strip() + "\n",
        "notes": (
            "Cole este texto nas regras / steering do Kiro (ou projeto). "
            "Assim o agente usa build_context sozinho quando fizer sentido."
        ),
    }
