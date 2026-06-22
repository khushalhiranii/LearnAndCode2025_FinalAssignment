"""HTML email body builders for notification types."""


def timesheet_reminder_html(employee_name: str, week_start: str, reminder_number: int) -> str:
    return f"""
    <h2>Timesheet reminder</h2>
    <p>Hi {employee_name},</p>
    <p>This is reminder #{reminder_number} that your timesheet for the week starting
    <strong>{week_start}</strong> has not been submitted.</p>
    <p>Please log in to the PRM tool and submit it as soon as possible.</p>
    """


def timesheet_frozen_html(employee_name: str, week_start: str, for_manager: bool) -> str:
    if for_manager:
        return f"""
        <h2>Employee timesheet access frozen</h2>
        <p>{employee_name} has not submitted the timesheet for week starting
        <strong>{week_start}</strong> after two reminders.</p>
        <p>Their timesheet submission access has been frozen. You may restore access
        after review from the manager menu.</p>
        """
    return f"""
    <h2>Timesheet submission frozen</h2>
    <p>Hi {employee_name},</p>
    <p>Your timesheet for the week starting <strong>{week_start}</strong> was not submitted
    after two reminders.</p>
    <p>Your ability to create or submit timesheets has been frozen. You can still log in
    and view your data. Contact your manager to restore access.</p>
    """


def timesheet_restored_html(employee_name: str) -> str:
    return f"""
    <h2>Timesheet access restored</h2>
    <p>Hi {employee_name},</p>
    <p>Your manager has restored your timesheet submission access. You may submit
    timesheets again.</p>
    """


def project_at_risk_html(
    project_name: str,
    manager_name: str,
    health_label: str,
    health_color: str,
    milestones_html: str,
    risk_summary: str,
    suggested_help_html: str,
) -> str:
    return f"""
    <h2>Project at risk: {project_name}</h2>
    <p>Hi {manager_name},</p>
    <p>The Project Health Scheduler has flagged <strong>{project_name}</strong> as
    <span style="color:{health_color};font-weight:bold;">{health_label}</span>.</p>
    <h3>Milestones</h3>
    {milestones_html}
    <h3>AI risk summary</h3>
    <p>{risk_summary}</p>
    <h3>Suggested help</h3>
    {suggested_help_html}
    """
