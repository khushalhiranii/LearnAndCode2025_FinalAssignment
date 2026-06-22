import json
import re

import httpx

from src.domain.exceptions import AIProviderError
from src.domain.ports.ai_provider import (
    IAIProvider,
    ParsedTeamRole,
    RiskSummaryContext,
    SkillCatalogEntry,
    SkillMatchCandidate,
    SkillMatchResult,
)


class GemmaAdapter(IAIProvider):

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = 60.0,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._model = model
        self._timeout = timeout

    @property
    def provider_name(self) -> str:
        return "gemma"

    async def _complete(self, prompt: str) -> str:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["apikey"] = self._api_key
        payload = {"model": self._model, "prompt": prompt, "stream": False}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(self._base_url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", data.get("text", str(data)))
        except Exception as exc:
            raise AIProviderError(f"Gemma API call failed: {exc}") from exc

    async def rank_resources(
        self,
        query: str,
        candidates: list[SkillMatchCandidate],
        hours_per_week: float | None = None,
    ) -> list[SkillMatchResult]:
        if not candidates:
            return []
        prompt = _build_skill_match_prompt(query, candidates, hours_per_week)
        text = await self._complete(prompt)
        return _parse_skill_match_response(text, candidates)

    async def summarize_risk(self, context: RiskSummaryContext) -> str:
        prompt = _build_risk_prompt(context)
        return await self._complete(prompt)

    async def parse_team_requirements(
        self,
        query: str,
        skills: list[SkillCatalogEntry],
    ) -> list[ParsedTeamRole]:
        if not skills:
            return []
        prompt = _build_team_parse_prompt(query, skills)
        text = await self._complete(prompt)
        return _parse_team_requirements_response(text, skills)


class GeminiAdapter(GemmaAdapter):
    """Gemini via Google Generative Language API (REST)."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        super().__init__(
            api_key=api_key,
            base_url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            model=model,
        )
        self._gemini_key = api_key

    @property
    def provider_name(self) -> str:
        return "gemini"

    async def _complete(self, prompt: str) -> str:
        url = f"{self._base_url}?key={self._gemini_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as exc:
            raise AIProviderError(f"Gemini API call failed: {exc}") from exc


class GroqAdapter(GemmaAdapter):
    """Groq OpenAI-compatible chat completions."""

    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant") -> None:
        super().__init__(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1/chat/completions",
            model=model,
        )

    @property
    def provider_name(self) -> str:
        return "groq"

    async def _complete(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(self._base_url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as exc:
            raise AIProviderError(f"Groq API call failed: {exc}") from exc


class MockAIProvider(IAIProvider):

    @property
    def provider_name(self) -> str:
        return "mock"

    async def rank_resources(
        self,
        query: str,
        candidates: list[SkillMatchCandidate],
        hours_per_week: float | None = None,
    ) -> list[SkillMatchResult]:
        return [
            SkillMatchResult(
                resource_profile_id=c.resource_profile_id,
                full_name=c.full_name,
                rank=i + 1,
                reason=f"Mock match for '{query}' — skills: {', '.join(c.skills[:3])}",
            )
            for i, c in enumerate(candidates[:5])
        ]

    async def summarize_risk(self, context: RiskSummaryContext) -> str:
        flags = ", ".join(context.risk_flags) if context.risk_flags else "none"
        return (
            f"Project '{context.project_name}' is {context.health_status}. "
            f"Key concerns: {flags}."
        )

    async def parse_team_requirements(
        self,
        query: str,
        skills: list[SkillCatalogEntry],
    ) -> list[ParsedTeamRole]:
        from src.application.ai.team_query_parser import parse_team_query_rule_based

        return parse_team_query_rule_based(query, skills)


def _build_skill_match_prompt(
    query: str,
    candidates: list[SkillMatchCandidate],
    hours_per_week: float | None,
) -> str:
    lines = [
        "You are a resource matching assistant. Rank candidates for the requirement.",
        f"Requirement: {query}",
    ]
    if hours_per_week:
        lines.append(f"Required hours per week: {hours_per_week}")
    lines.append("Candidates (JSON):")
    lines.append(
        json.dumps(
            [
                {
                    "id": c.resource_profile_id,
                    "name": c.full_name,
                    "skills": c.skills,
                    "free_percent": c.free_percent,
                    "recent_tags": c.recent_activity_tags,
                }
                for c in candidates
            ]
        )
    )
    lines.append(
        'Respond ONLY with JSON array: [{"id": int, "rank": int, "reason": "string"}, ...]'
    )
    return "\n".join(lines)


def _build_risk_prompt(context: RiskSummaryContext) -> str:
    return (
        f"Summarize project risks in 2-4 plain English sentences.\n"
        f"Project: {context.project_name}\n"
        f"Health: {context.health_status}\n"
        f"Milestones: {json.dumps(context.milestones)}\n"
        f"Resource effort: {json.dumps(context.resource_effort)}\n"
        f"Flags: {context.risk_flags}\n"
    )


def _build_team_parse_prompt(query: str, skills: list[SkillCatalogEntry]) -> str:
    catalog = json.dumps(
        [{"id": s.skill_id, "name": s.name, "category": s.category} for s in skills]
    )
    return (
        "Extract every distinct team role from the manager's request.\n"
        f"Request: {query}\n"
        f"Skill catalog (use only these skill ids): {catalog}\n"
        "Map senior/lead/principal to ADVANCED, mid/intermediate to INTERMEDIATE, "
        "junior/entry to BEGINNER, otherwise BEGINNER.\n"
        "Respond ONLY with a JSON array:\n"
        '[{"role_title": "string", "skill_id": int, '
        '"min_proficiency": "BEGINNER|INTERMEDIATE|ADVANCED", '
        '"utilization_percent": 100}]\n'
    )


def _parse_team_requirements_response(
    text: str,
    skills: list[SkillCatalogEntry],
) -> list[ParsedTeamRole]:
    valid_ids = {s.skill_id for s in skills}
    valid_prof = {"BEGINNER", "INTERMEDIATE", "ADVANCED"}
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return []
    try:
        items = json.loads(match.group())
        results: list[ParsedTeamRole] = []
        used_ids: set[int] = set()
        for item in items:
            skill_id = int(item["skill_id"])
            if skill_id not in valid_ids or skill_id in used_ids:
                continue
            prof = str(item.get("min_proficiency", "BEGINNER")).upper()
            if prof not in valid_prof:
                prof = "BEGINNER"
            used_ids.add(skill_id)
            util = int(item.get("utilization_percent", 100))
            util = max(1, min(100, util))
            results.append(
                ParsedTeamRole(
                    role_title=str(item.get("role_title", "Role"))[:100],
                    skill_id=skill_id,
                    min_proficiency=prof,
                    utilization_percent=util,
                )
            )
        return results
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return []


def _parse_skill_match_response(
    text: str,
    candidates: list[SkillMatchCandidate],
) -> list[SkillMatchResult]:
    by_id = {c.resource_profile_id: c for c in candidates}
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return _fallback_rank(candidates, "AI response could not be parsed; showing by availability.")
    try:
        items = json.loads(match.group())
        results = []
        for item in items:
            pid = int(item["id"])
            if pid in by_id:
                results.append(
                    SkillMatchResult(
                        resource_profile_id=pid,
                        full_name=by_id[pid].full_name,
                        rank=int(item.get("rank", len(results) + 1)),
                        reason=str(item.get("reason", "Matched by AI")),
                    )
                )
        results.sort(key=lambda r: r.rank)
        return results or _fallback_rank(candidates, "No matches parsed from AI.")
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return _fallback_rank(candidates, "AI response could not be parsed; showing by availability.")


def _fallback_rank(candidates: list[SkillMatchCandidate], note: str) -> list[SkillMatchResult]:
    sorted_c = sorted(candidates, key=lambda c: c.free_percent, reverse=True)
    return [
        SkillMatchResult(
            resource_profile_id=c.resource_profile_id,
            full_name=c.full_name,
            rank=i + 1,
            reason=note if i == 0 else f"Free capacity: {c.free_percent}%",
        )
        for i, c in enumerate(sorted_c[:5])
    ]
