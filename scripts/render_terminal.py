#!/usr/bin/env python3
"""Gera o terminal do perfil com o último commit dos projetos públicos."""

import json
import os
from datetime import datetime
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen


REPOSITORIES = (
    "Ilhe8l/plan-bot",
    "Ilhe8l/multi-agent-orchestrator",
    "leds-conectafapes/workshop-whatsapp-agents",
)
OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "terminal.svg"


def latest_public_commit() -> tuple[str, datetime]:
    # Consulta só os projetos públicos, sem trazer dados dos repositórios privados.
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ilhe8l-profile-renderer",
    }
    if token := os.environ.get("GH_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"

    commits = []
    for repository in REPOSITORIES:
        request = Request(
            f"https://api.github.com/repos/{repository}/commits?per_page=1",
            headers=headers,
        )
        with urlopen(request, timeout=15) as response:
            data = json.load(response)
        if not data:
            continue
        commit = data[0]["commit"]
        timestamp = commit["committer"]["date"] or commit["author"]["date"]
        commits.append((repository, datetime.fromisoformat(timestamp.replace("Z", "+00:00"))))

    # Sem dados da API, mantém o SVG anterior em vez de publicar um cartão vazio.
    if not commits:
        raise RuntimeError("Nenhum commit público encontrado nos repositórios selecionados")
    return max(commits, key=lambda item: item[1])


def render(repository: str, timestamp: datetime) -> str:
    latest = escape(f"{repository}  ·  {timestamp:%d %b %Y}")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="960" height="398" viewBox="0 0 960 398" role="img" aria-labelledby="title desc">
  <title id="title">Guilherme Souza — AI and backend developer</title>
  <desc id="desc">Terminal-style profile featuring work on EDITE and Oráculo. Latest public commit: {latest}.</desc>
  <rect x="1" y="1" width="958" height="396" rx="16" fill="#0d1117" stroke="#303d4d" stroke-width="2"/>
  <path d="M17 1h926a16 16 0 0 1 16 16v34H1V17A16 16 0 0 1 17 1Z" fill="#161f2a"/>
  <path d="M1 51h958" stroke="#303d4d"/>
  <circle cx="28" cy="26" r="6" fill="#f7768e"/>
  <circle cx="49" cy="26" r="6" fill="#e0af68"/>
  <circle cx="70" cy="26" r="6" fill="#9ece6a"/>
  <g font-family="ui-monospace, SFMono-Regular, Consolas, 'Liberation Mono', monospace">
    <text x="480" y="31" text-anchor="middle" font-size="14" fill="#95a6bb">guilherme@github: ~</text>
    <text x="36" y="92" font-size="16" fill="#7dcfff">$ whoami</text>
    <text x="36" y="135" font-size="29" font-weight="700" fill="#edf2f7">Guilherme Souza</text>
    <text x="36" y="166" font-size="16" fill="#b9c5d2">AI &amp; backend developer  /  Information Systems student at IFES</text>
    <path d="M36 190h888" stroke="#27384a"/>
    <text x="36" y="222" font-size="16" fill="#7dcfff">$ current_work</text>
    <text x="36" y="257" font-size="16" fill="#9ece6a">EDITE</text>
    <text x="139" y="257" font-size="16" fill="#d4dde7">AI assistant for FAPES</text>
    <text x="36" y="288" font-size="16" fill="#9ece6a">ORÁCULO</text>
    <text x="139" y="288" font-size="16" fill="#d4dde7">internal natural-language-to-SQL backend</text>
    <path d="M36 309h888" stroke="#27384a"/>
    <text x="36" y="342" font-size="16" fill="#7dcfff">$ latest_public_commit</text>
    <text x="36" y="374" font-size="16" fill="#d4dde7">{latest}</text>
    <text x="914" y="374" text-anchor="end" font-size="16" fill="#9ece6a">▌</text>
  </g>
</svg>
"""


if __name__ == "__main__":
    repository_name, committed_at = latest_public_commit()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(repository_name, committed_at), encoding="utf-8")
