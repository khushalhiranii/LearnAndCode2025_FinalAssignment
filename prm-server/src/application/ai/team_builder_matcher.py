"""Deterministic team assignment: one person per role, honest gap reporting."""

from dataclasses import dataclass, field
from datetime import date

from src.domain.enums import ProficiencyLevel, TeamGapType

_PROFICIENCY_RANK = {
    ProficiencyLevel.BEGINNER: 1,
    ProficiencyLevel.INTERMEDIATE: 2,
    ProficiencyLevel.ADVANCED: 3,
}


@dataclass
class TeamRoleSlot:
    role_title: str
    skill_id: int
    skill_name: str
    min_proficiency: ProficiencyLevel
    utilization_percent: int


@dataclass
class TeamMemberPool:
    resource_profile_id: int
    full_name: str
    skills: dict[int, ProficiencyLevel]
    free_percent: int
    allocated_until: date | None = field(default=None)


@dataclass
class RoleAssignment:
    role_index: int
    member_index: int
    score: int


@dataclass
class TeamMatchOutcome:
    assignments: dict[int, int]
    gaps: list[tuple[int, TeamGapType, str, date | None]]
    unfilled_reasons: dict[int, str]


def _proficiency_meets(actual: ProficiencyLevel, required: ProficiencyLevel) -> bool:
    return _PROFICIENCY_RANK[actual] >= _PROFICIENCY_RANK[required]


def _member_score(
    member: TeamMemberPool,
    role: TeamRoleSlot,
    proficiency: ProficiencyLevel,
) -> int:
    bench_bonus = 500 if member.free_percent == 100 else 0
    return _PROFICIENCY_RANK[proficiency] * 1000 + member.free_percent + bench_bonus


def _find_best_assignment(
    roles: list[TeamRoleSlot],
    members: list[TeamMemberPool],
) -> dict[int, int]:
    """Backtracking search for the highest-scoring one-to-one assignment."""
    eligibility: list[list[tuple[int, int]]] = []
    for role in roles:
        options: list[tuple[int, int]] = []
        for idx, member in enumerate(members):
            proficiency = member.skills.get(role.skill_id)
            if proficiency is None or not _proficiency_meets(proficiency, role.min_proficiency):
                continue
            if member.free_percent < role.utilization_percent:
                continue
            options.append((idx, _member_score(member, role, proficiency)))
        eligibility.append(sorted(options, key=lambda item: item[1], reverse=True))

    best: dict[int, int] = {}
    best_score = -1

    def search(role_idx: int, used: set[int], current: dict[int, int], score: int) -> None:
        nonlocal best, best_score
        if role_idx == len(roles):
            if score > best_score or (score == best_score and len(current) > len(best)):
                best_score = score
                best = current.copy()
            return

        search(role_idx + 1, used, current, score)
        for member_idx, member_score in eligibility[role_idx]:
            if member_idx in used:
                continue
            current[role_idx] = member_idx
            search(role_idx + 1, used | {member_idx}, current, score + member_score)
            del current[role_idx]

    search(0, set(), {}, 0)
    return best


def _skilled_members(
    members: list[TeamMemberPool],
    role: TeamRoleSlot,
) -> list[tuple[TeamMemberPool, ProficiencyLevel]]:
    result: list[tuple[TeamMemberPool, ProficiencyLevel]] = []
    for member in members:
        proficiency = member.skills.get(role.skill_id)
        if proficiency and _proficiency_meets(proficiency, role.min_proficiency):
            result.append((member, proficiency))
    return result


def _analyze_gap(
    role: TeamRoleSlot,
    members: list[TeamMemberPool],
    assigned_member_ids: set[int],
) -> tuple[TeamGapType, str, date | None] | None:
    skilled = _skilled_members(members, role)
    if not skilled:
        return (
            TeamGapType.SKILL_GAP,
            f"No team member has {role.skill_name} at {role.min_proficiency.value} "
            f"level or above. Consider hiring or training.",
            None,
        )

    unassigned_available = [
        (member, prof)
        for member, prof in skilled
        if member.resource_profile_id not in assigned_member_ids
        and member.free_percent >= role.utilization_percent
    ]
    if unassigned_available:
        return None

    unassigned_skilled = [
        (member, prof)
        for member, prof in skilled
        if member.resource_profile_id not in assigned_member_ids
    ]
    if unassigned_skilled and not any(
        member.free_percent >= role.utilization_percent for member, _ in unassigned_skilled
    ):
        member, proficiency = max(
            unassigned_skilled,
            key=lambda item: (_PROFICIENCY_RANK[item[1]], item[0].free_percent),
        )
        until = member.allocated_until
        until_text = f" until {until}" if until else ""
        return (
            TeamGapType.AVAILABILITY_GAP,
            f"{member.full_name} has {role.skill_name} ({proficiency.value}) but is "
            f"allocated{until_text} (free capacity: {member.free_percent}%, "
            f"needed: {role.utilization_percent}%).",
            until,
        )

    if all(member.resource_profile_id in assigned_member_ids for member, _ in skilled):
        return None

    member, proficiency = max(
        skilled,
        key=lambda item: (_PROFICIENCY_RANK[item[1]], item[0].free_percent),
    )
    until = member.allocated_until
    until_text = f" until {until}" if until else ""
    return (
        TeamGapType.AVAILABILITY_GAP,
        f"{member.full_name} has {role.skill_name} ({proficiency.value}) but is "
        f"allocated{until_text} (free capacity: {member.free_percent}%, "
        f"needed: {role.utilization_percent}%).",
        until,
    )


def match_team(
    roles: list[TeamRoleSlot],
    members: list[TeamMemberPool],
) -> TeamMatchOutcome:
    assignments = _find_best_assignment(roles, members)
    assigned_member_ids = {members[idx].resource_profile_id for idx in assignments.values()}

    gaps: list[tuple[int, TeamGapType, str, date | None]] = []
    unfilled_reasons: dict[int, str] = {}

    for role_idx, role in enumerate(roles):
        if role_idx in assignments:
            continue

        gap = _analyze_gap(role, members, assigned_member_ids)
        if gap:
            gap_type, message, available_from = gap
            gaps.append((role_idx, gap_type, message, available_from))
            continue

        skilled = _skilled_members(members, role)
        available_count = sum(
            1
            for member, _ in skilled
            if member.free_percent >= role.utilization_percent
        )
        if available_count > 0:
            unfilled_reasons[role_idx] = (
                "All qualified and available members are already assigned to "
                "other roles in this team plan."
            )
        else:
            gap_type, message, available_from = gap or (
                TeamGapType.SKILL_GAP,
                f"No team member has {role.skill_name} at {role.min_proficiency.value} "
                f"level or above. Consider hiring or training.",
                None,
            )
            gaps.append((role_idx, gap_type, message, available_from))

    return TeamMatchOutcome(
        assignments=assignments,
        gaps=gaps,
        unfilled_reasons=unfilled_reasons,
    )
