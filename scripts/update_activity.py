#!/usr/bin/env python3
"""Actualiza automáticamente el bloque dinámico del README de perfil."""

from __future__ import annotations

import datetime
import json
import pathlib
import re
import urllib.request

USERNAME = "facupeletay"
README_PATH = pathlib.Path(__file__).resolve().parent.parent / "README.md"
START_MARKER = "<!-- START_DYNAMIC_ACTIVITY -->"
END_MARKER = "<!-- END_DYNAMIC_ACTIVITY -->"
# Repos que nunca se listan: el propio perfil y proyectos de trabajo.
EXCLUDED_REPOS = {USERNAME.lower(), "agentecreditos"}

TIPS_SISTEMAS_QA = [
    "💡 **Principio QA del día:** Probar temprano (*Shift-Left Testing*) reduce exponencialmente el costo de corregir defectos en producción.",
    "💡 **Tip SQL del día:** Revisá siempre los planes de ejecución (`EXPLAIN ANALYZE`) antes de agregar índices compuestos innecesarios.",
    "💡 **Ingeniería de Sistemas:** Un requerimiento bien documentado y con criterios de aceptación claros ahorra horas de retrabajo.",
    "💡 **Tip Pascal / Clean Code:** Mantener rutinas cohesivas y desacoplar la lógica de negocio del acceso a datos facilita el mantenimiento evolutivo.",
    "💡 **Testing & Automatización:** Combinar pruebas exploratorias manuales con regresiones automatizadas da la mejor cobertura real.",
    "💡 **Arquitectura & APIs:** Validar contratos de entrada y manejar errores de forma predecible hace que el frontend (React/Flutter) sea mucho más resiliente.",
    "💡 **Bases de Datos:** Las transacciones deben ser lo más cortas posible para evitar bloqueos (*locks*) en tablas de alta concurrencia.",
]


def fetch_github_summary(username: str) -> tuple[int, list[str]] | None:
    url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": f"{username}-profile-updater"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            repos = json.loads(resp.read().decode("utf-8"))
            own = [r for r in repos if not r.get("fork") and r["name"].lower() not in EXCLUDED_REPOS]
            recent = [f"[`{r['name']}`]({r['html_url']})" for r in own[:4]]
            return len(own), recent
    except Exception as exc:
        print(f"No se pudo consultar la API de GitHub: {exc}")
        return None


def build_dynamic_block(previous_block: str) -> str:
    # Sin fecha/hora en el bloque: así solo hay commit cuando cambia el contenido real.
    now_ar = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3)))
    day_index = now_ar.timetuple().tm_yday % len(TIPS_SISTEMAS_QA)
    tip = TIPS_SISTEMAS_QA[day_index]
    summary = fetch_github_summary(USERNAME)

    if summary is None:
        # Si la API falla, se conserva la línea de repos anterior en vez de borrarla.
        prev = re.search(r"^- 📦 .*\n", previous_block, re.MULTILINE)
        repos_line = prev.group(0) if prev else ""
    else:
        repo_count, recent_repos = summary
        repos_line = (
            f"- 📦 **Repositorios públicos activos:** `{repo_count}` ({', '.join(recent_repos)})\n"
            if recent_repos
            else ""
        )

    return (
        f"{START_MARKER}\n"
        f"{repos_line}"
        f"- 🎯 **Enfoque actual:** Análisis de Sistemas • Desarrollo en Pascal & SQL • Full Stack (React/TS/Python/Java) & Flutter • QA Testing\n\n"
        f"> {tip}\n"
        f"{END_MARKER}"
    )


def main() -> None:
    content = README_PATH.read_text(encoding="utf-8")
    if START_MARKER not in content or END_MARKER not in content:
        raise RuntimeError("No se encontraron los marcadores dinámicos en README.md")

    before, rest = content.split(START_MARKER, 1)
    previous, after = rest.split(END_MARKER, 1)
    updated = before + build_dynamic_block(previous) + after
    README_PATH.write_text(updated, encoding="utf-8")
    print("README.md actualizado correctamente.")


if __name__ == "__main__":
    main()
