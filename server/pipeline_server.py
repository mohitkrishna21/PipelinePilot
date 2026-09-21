from fastmcp import FastMCP
import sqlite3
import os
from dotenv import load_dotenv
from typing import Optional
import datetime 
import json

load_dotenv()

project_root = os.path.dirname(os.path.abspath(__file__))
parent_root = os.path.dirname(project_root)

demo_db_path = os.path.join(parent_root, "db", "demo_pipeline.db")

db_path = os.environ.get("DB_PATH", demo_db_path)

conn = sqlite3.connect(db_path, check_same_thread=False)


mcp = FastMCP(
    name="PipelinePilot Server",
    instructions=(
        "Manages a single user's job application pipeline. Use this server to check "
        "pipeline health (counts by stage and tier, which applications have gone stale), "
        "look up full details on a specific application, log new applications or stage "
        "updates, and draft follow-up messages for stale applications. Follow-ups require "
        "explicit human approval before being marked as sent."
    ),
)

@mcp.tool()
def list_applications(stage: Optional[str] = None,tier: Optional[str] = None):

    """
    Return a list of job applications from the pipeline.

    Use stage to filter applications by their current pipeline stage. Valid stage
    values are: applied, oa, phone_screen, onsite, offer, rejected, withdrawn.

    Use tier to filter applications by target-company tier. Valid tier values are:
    tier1, tier2, tier3, stretch.

    Either stage or tier can be omitted to skip that filter. If both are omitted,
    all applications are returned.
    """

    query = "SELECT company, role, tier, current_stage, date_applied, next_action FROM applications"
    conditions = []
    params = []

    if stage is not None:
        conditions.append("current_stage = ?")
        params.append(stage)

    if tier is not None:
       conditions.append("tier = ?")
       params.append(tier)

    if conditions:
       query += " WHERE " + " AND ".join(conditions)

    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()

    if not rows :
        return f"No applications found matching stage={stage}, tier={tier}."

    lines = []
    for row in rows:
        company, role, tier, current_stage, date_applied, next_action = row

        if next_action is None:
            next_action = "none"

        line = f"{company},{role},{tier},{current_stage},{date_applied },{next_action}"
        lines.append(line)

    return "\n".join(lines)

@mcp.tool()
def get_application(company: str):
    """
    Look up a single job application by company name.

    The company parameter should contain the company name, or part of the company
    name, to search for. The database lookup uses substring matching, so partial
    company names can match an application. If no application is found, the tool
    uses fuzzy matching against known company names and may suggest the closest
    match.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM applications WHERE company LIKE ?",
        (f"%{company}%",)
    )
    rows = cursor.fetchall()

    if not rows:
        cursor.execute("SELECT DISTINCT company FROM applications")
        all_names = [r[0] for r in cursor.fetchall()]

        import difflib
        guess = difflib.get_close_matches(company, all_names, n=1)

        if guess:
            return (
                f"No application found for '{company}' — "
                f"did you mean '{guess[0]}'?"
            )

        return f"No application found for '{company}'."

    elif len(rows) > 1:
        summaries = []

        for row in rows:
            (
                id,
                matched_company,
                role,
                tier,
                date_applied,
                current_stage,
                last_activity_date,
                next_action,
                next_action_date,
                contact_name,
                contact_email,
                source,
                notes,
            ) = row

            summaries.append(
                f"{matched_company} — {role} — {tier} — "
                f"{current_stage} — applied {date_applied}"
            )

        return (
            f"Found {len(rows)} applications matching '{company}':\n"
            + "\n".join(summaries)
        )

    else:
        row = rows[0]

    (
        id,
        company,
        role,
        tier,
        date_applied,
        current_stage,
        last_activity_date,
        next_action,
        next_action_date,
        contact_name,
        contact_email,
        source,
        notes,
    ) = row

    last_activity_date = last_activity_date or "none"
    next_action = next_action or "none"
    next_action_date = next_action_date or "none"
    contact_name = contact_name or "none"
    contact_email = contact_email or "none"
    source = source or "none"
    notes = notes or "none"

    return (
        f"Company: {company}\n"
        f"Role: {role}\n"
        f"Tier: {tier}\n"
        f"Current stage: {current_stage}\n"
        f"Date applied: {date_applied}\n"
        f"Last activity date: {last_activity_date}\n"
        f"Next action: {next_action}\n"
        f"Next action date: {next_action_date}\n"
        f"Contact name: {contact_name}\n"
        f"Contact email: {contact_email}\n"
        f"Source: {source}\n"
        f"Notes: {notes}"
    )

@mcp.tool()
def get_stale_applications(threshold_days: int = 10):
    """
    Return active job applications that have gone stale.

    An application is considered stale when the number of days since its last
    activity is greater than or equal to threshold_days. Applications already
    in offer, rejected, or withdrawn stages are excluded.

    threshold_days controls how many days of inactivity are allowed before an
    application is considered stale.
    """

    cursor = conn.cursor()
    cursor.execute(
        "SELECT company, current_stage, last_activity_date FROM applications "
        "WHERE current_stage NOT IN ('offer', 'rejected', 'withdrawn')"
    )
    rows = cursor.fetchall()

    today = datetime.date.today()
    stale_applications = []

    for row in rows:
        company, current_stage, last_activity_date = row

        last_date = datetime.date.fromisoformat(last_activity_date)
        days_since = (today - last_date).days

        if days_since >= threshold_days:
            stale_applications.append(
                (company, current_stage, days_since)
            )

    if not stale_applications:
        return (
            f"No stale applications found with a threshold of "
            f"{threshold_days} days."
        )

    lines = []

    for company, current_stage, days_since in stale_applications:
        line = (
            f"{company} — stage: {current_stage}, "
            f"{days_since} days since last activity"
        )
        lines.append(line)

    return "\n".join(lines)

@mcp.tool()
def get_pipeline_summary(threshold_days: int = 10):
    """
    Return a summary of the job application pipeline.

    The summary includes the number of applications in each pipeline stage,
    the number of applications in each target-company tier, and the number of
    active applications that are considered stale.

    threshold_days controls how many days without activity must pass before an
    active application is counted as stale. Applications in offer, rejected,
    or withdrawn stages are excluded from the stale count.
    """

    cursor = conn.cursor()

    cursor.execute(
        "SELECT current_stage, COUNT(*) "
        "FROM applications GROUP BY current_stage"
    )
    stage_counts = cursor.fetchall()

    cursor.execute(
        "SELECT tier, COUNT(*) "
        "FROM applications GROUP BY tier"
    )
    tier_counts = cursor.fetchall()

    cursor.execute(
        "SELECT last_activity_date FROM applications "
        "WHERE current_stage NOT IN ('offer', 'rejected', 'withdrawn')"
    )
    rows = cursor.fetchall()

    today = datetime.date.today()
    stale_count = 0

    for row in rows:
        last_activity_date = row[0]
        last_date = datetime.date.fromisoformat(last_activity_date)
        days_since = (today - last_date).days

        if days_since >= threshold_days:
            stale_count += 1

    lines = []

    lines.append("By stage:")
    for current_stage, count in stage_counts:
        lines.append(f"- {current_stage}: {count}")

    lines.append("")
    lines.append("By tier:")
    for tier, count in tier_counts:
        lines.append(f"- {tier}: {count}")

    lines.append("")
    lines.append(
        f"Stale applications ({threshold_days}+ days without activity): "
        f"{stale_count}"
    )

    return "\n".join(lines)

@mcp.tool()
def log_application(
    company: str,
    role: str,
    tier: str,
    date_applied: Optional[str] = None,
    source: Optional[str] = None,
    contact_name: Optional[str] = None,
    contact_email: Optional[str] = None,
    notes: Optional[str] = None,
):
    """
    Log a new job application in the pipeline.

    company is the name of the company, role is the job title, and tier is the
    target-company tier. Valid tier values are tier1, tier2, tier3, and stretch.

    date_applied should be an ISO-format date such as 2026-09-17. If it is
    omitted, today's date is used. source, contact_name, contact_email, and notes
    are optional details about the application.

    New applications are always created in the applied stage, and their last
    activity date is initially set to the application date.
    """

    valid_tiers = ("tier1", "tier2", "tier3", "stretch")
    if tier not in valid_tiers:
        return (
            f"Invalid tier '{tier}'. "
            f"Valid values are: {', '.join(valid_tiers)}."
        )

    date_applied = date_applied or datetime.date.today().isoformat()

    current_stage = "applied"
    last_activity_date = date_applied

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO applications "
        "(company, role, tier, date_applied, current_stage, last_activity_date, "
        "source, contact_name, contact_email, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            company,
            role,
            tier,
            date_applied,
            current_stage,
            last_activity_date,
            source,
            contact_name,
            contact_email,
            notes,
        ),
    )
    conn.commit()

    return (
        f"Logged new application: {company} — {role} "
        f"({tier}), applied {date_applied}."
    )

@mcp.tool()
def update_application(
    company: str,
    current_stage: Optional[str] = None,
    next_action: Optional[str] = None,
    next_action_date: Optional[str] = None,
    contact_name: Optional[str] = None,
    contact_email: Optional[str] = None,
    notes: Optional[str] = None,
):
    """
    Update selected fields on an existing job application.

    company must be the exact company name stored in the database. Use
    get_application first if you need to resolve a partial or misspelled name.

    current_stage updates the application's pipeline stage. Valid values are
    applied, oa, phone_screen, onsite, offer, rejected, and withdrawn.

    next_action, next_action_date, contact_name, contact_email, and notes are
    optional fields. Only values that are provided are updated. Any successful
    update also refreshes last_activity_date to today's date.
    """

    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM applications WHERE company = ?",
        (company,)
    )
    row = cursor.fetchone()

    if row is None:
        return (
            f"No application found for '{company}'. "
            f"Try get_application first to confirm the exact name."
        )

    app_id = row[0]

    valid_stages = (
        "applied",
        "oa",
        "phone_screen",
        "onsite",
        "offer",
        "rejected",
        "withdrawn",
    )

    if current_stage is not None and current_stage not in valid_stages:
        return (
            f"Invalid stage '{current_stage}'. "
            f"Valid values are: {', '.join(valid_stages)}."
        )

    updates = []
    params = []
    changed_fields = []

    if current_stage is not None:
        updates.append("current_stage = ?")
        params.append(current_stage)
        changed_fields.append(f"current_stage={current_stage}")

    if next_action is not None:
        updates.append("next_action = ?")
        params.append(next_action)
        changed_fields.append(f"next_action={next_action}")

    if next_action_date is not None:
        updates.append("next_action_date = ?")
        params.append(next_action_date)
        changed_fields.append(f"next_action_date={next_action_date}")

    if contact_name is not None:
        updates.append("contact_name = ?")
        params.append(contact_name)
        changed_fields.append(f"contact_name={contact_name}")

    if contact_email is not None:
        updates.append("contact_email = ?")
        params.append(contact_email)
        changed_fields.append(f"contact_email={contact_email}")

    if notes is not None:
        updates.append("notes = ?")
        params.append(notes)
        changed_fields.append(f"notes={notes}")

    if not updates:
        return "No fields were provided to update."

    updates.append("last_activity_date = ?")
    params.append(datetime.date.today().isoformat())

    params.append(app_id)

    cursor.execute(
        f"UPDATE applications SET {', '.join(updates)} WHERE id = ?",
        params
    )
    conn.commit()

    return (
        f"Updated application for {company}: "
        f"{', '.join(changed_fields)}."
    )

@mcp.tool()
def mark_followed_up(company: str, draft_text: str):
    """
    Record that a follow-up message was sent for an existing application.

    company must be the exact company name stored in the database. Use
    get_application first if you need to confirm the exact name.

    draft_text is the follow-up message that was sent. The message is appended
    to the application's notes with today's date. The application's
    last_activity_date is refreshed, and any pending next_action and
    next_action_date are cleared because the follow-up has been completed.

    This tool assumes any required human approval has already happened before
    the tool is called.
    """

    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, notes FROM applications WHERE company = ?",
        (company,)
    )
    row = cursor.fetchone()

    if row is None:
        return (
            f"No application found for '{company}'. "
            f"Try get_application first to confirm the exact name."
        )

    app_id, existing_notes = row

    today = datetime.date.today().isoformat()
    new_note = f"[{today}] Followed up: {draft_text}"

    if existing_notes:
        updated_notes = existing_notes + "\n" + new_note
    else:
        updated_notes = new_note

    cursor.execute(
        "UPDATE applications SET last_activity_date = ?, "
        "next_action = NULL, next_action_date = NULL, notes = ? "
        "WHERE id = ?",
        (today, updated_notes, app_id)
    )
    conn.commit()

    return f"Marked follow-up as sent for {company} on {today}."

@mcp.resource("target-companies://{tier}")
def get_target_companies(tier: str):
    """
    Return the target companies configured for a specific company tier.

    tier should be one of the tier names defined in target_companies.json,
    such as tier1, tier2, tier3, or stretch. The resource returns the list
    of company names assigned to that tier.

    If the requested tier does not exist in the configuration file, an
    informative error message is returned instead.
    """

    data_path = os.path.join(
        parent_root,
        "data",
        "target_companies.json"
    )

    with open(data_path) as f:
        target_companies = json.load(f)

    if tier not in target_companies:
        return (
            f"Unknown tier '{tier}'. "
            f"Valid values are: {', '.join(target_companies.keys())}."
        )

    return target_companies[tier]

@mcp.prompt()
def weekly_review():
    """
    Generate a fixed weekly pipeline-review request for the agent.

    Invoking this prompt asks the model to summarize the application pipeline,
    identify stale applications with their days of inactivity, and suggest
    which stale applications should be prioritized for follow-up.
    """
    return (
        "Give me a full pipeline summary, then list all stale applications "
        "with how many days each has been inactive, and finally suggest "
        "which stale applications I should prioritize following up on first."
    )

if __name__ == "__main__":
    mcp.run()