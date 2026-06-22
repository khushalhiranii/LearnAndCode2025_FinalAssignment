"""Rule-based fallback: natural language → structured team roles."""

import re

from src.domain.enums import ProficiencyLevel
from src.domain.ports.ai_provider import ParsedTeamRole, SkillCatalogEntry

_SENIOR_PATTERN = re.compile(r"\b(senior|lead|principal|architect)\b", re.I)
_INTERMEDIATE_PATTERN = re.compile(r"\b(mid|intermediate)\b", re.I)
_JUNIOR_PATTERN = re.compile(r"\b(junior|entry|graduate)\b", re.I)
_NEEDS_PATTERN = re.compile(
    r"(?:needing|needs|requires|require|looking\s+for|want|wants)\s+(.+)",
    re.I,
)
_ROLE_SPLIT_PATTERN = re.compile(r"\s+and\s+|,\s*(?:a\s+|an\s+)?", re.I)


def _infer_proficiency(segment: str) -> ProficiencyLevel:
    if _SENIOR_PATTERN.search(segment):
        return ProficiencyLevel.ADVANCED
    if _INTERMEDIATE_PATTERN.search(segment):
        return ProficiencyLevel.INTERMEDIATE
    if _JUNIOR_PATTERN.search(segment):
        return ProficiencyLevel.BEGINNER
    return ProficiencyLevel.BEGINNER


def _clean_segment(segment: str) -> str:
    text = segment.strip()
    text = re.sub(r"^(?:a|an)\s+", "", text, flags=re.I)
    return text.strip(" .")


def _match_skill(segment: str, skills: list[SkillCatalogEntry]) -> SkillCatalogEntry | None:
    lower = segment.lower()
    best: SkillCatalogEntry | None = None
    best_len = 0
    for skill in skills:
        name_lower = skill.name.lower()
        if name_lower in lower or lower in name_lower:
            if len(name_lower) > best_len:
                best = skill
                best_len = len(name_lower)
        for token in name_lower.split():
            if len(token) >= 2 and token in lower:
                if len(token) > best_len:
                    best = skill
                    best_len = len(token)
    return best


def _extract_role_segments(query: str) -> list[str]:
    match = _NEEDS_PATTERN.search(query)
    roles_text = match.group(1) if match else query
    parts = _ROLE_SPLIT_PATTERN.split(roles_text)
    return [_clean_segment(p) for p in parts if _clean_segment(p)]


def parse_team_query_rule_based(
    query: str,
    skills: list[SkillCatalogEntry],
) -> list[ParsedTeamRole]:
    if not skills:
        return []

    segments = _extract_role_segments(query)
    roles: list[ParsedTeamRole] = []
    seen_skill_ids: set[int] = set()

    for segment in segments:
        skill = _match_skill(segment, skills)
        if skill is None or skill.skill_id in seen_skill_ids:
            continue
        seen_skill_ids.add(skill.skill_id)
        proficiency = _infer_proficiency(segment)
        roles.append(
            ParsedTeamRole(
                role_title=segment[:100],
                skill_id=skill.skill_id,
                min_proficiency=proficiency.value,
                utilization_percent=100,
            )
        )

    return roles
