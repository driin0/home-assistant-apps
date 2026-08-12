from tools._base import mcp


@mcp.prompt()
def automation_health_audit() -> str:
    """
    Comprehensive audit of all automations: conflicts, redundancies, disabled automations.
    """
    return """Perform a complete automation health audit on this Home Assistant instance.

Steps:
1. Call list_automations() to get all automations with their state and last_triggered.
2. Identify and group:
   - Disabled automations (state == 'off') — might have been forgotten
   - Automations that have never triggered (last_triggered is null)
   - Automations with very similar names — possible duplicates
3. For any suspicious ones, call get_automation(entity_id) to inspect their config.
4. Check list_repairs() for any active HA repair issues.

Report format:
- Summary counts (total, enabled, disabled, never triggered)
- Table of disabled automations with how long they've been disabled
- Suspected duplicates with explanation
- Specific recommended actions (delete, merge, re-enable, fix)

Be concise and actionable. Focus on real problems, not hypothetical ones."""


@mcp.prompt()
def energy_analysis() -> str:
    """
    Analyze current power consumption and identify savings opportunities.
    """
    return """Perform an energy consumption analysis for this Home Assistant instance.

Steps:
1. Call get_energy_summary() for a grouped overview by area and remote instance.
2. Call get_energy() to see individual devices sorted by current wattage.
3. Call get_live_context() to see who's home and which media players are active.
4. Cross-reference: are high-consumption devices running when nobody is home?

Report format:
- Total current consumption in W and estimated kWh/day
- Top 5 consumers by wattage
- Any obvious waste (high-draw devices running with nobody home, lights left on)
- Specific actionable suggestions (create automations, check devices)

Note: solar production sensors show negative or very large positive values — factor them out of consumption totals."""


@mcp.prompt()
def naming_convention_audit() -> str:
    """
    Scan entity and automation names for inconsistencies and suggest standardization.
    """
    return """Perform a naming convention audit on this Home Assistant instance.

Steps:
1. Call list_areas() to understand the current area/room structure.
2. Call list_automations() and list_scripts() to review automation/script names.
3. Call list_lights(), list_sensors(), list_switches() for a sample of entity names.
4. Call list_labels() to review label naming.

Look for:
- Mixed languages (names in different languages on similar entities)
- Inconsistent prefixes (some rooms have a "Living Room -" prefix, others don't)
- Automation names that don't follow a clear verb-object pattern
- Entities with generic names like "Switch 1", "Sensor", "Light"

Report:
- Examples of each inconsistency type found
- Proposed naming convention rules (keep them simple and practical)
- Priority list of entities/automations to rename (worst offenders first)
- use rename_entity() to fix them if the user agrees"""


@mcp.prompt()
def security_overview() -> str:
    """
    Check the security posture: locks, alarm, cameras, open doors/windows.
    """
    return """Perform a security overview of this Home Assistant instance.

Steps:
1. Call get_live_context() for a quick snapshot (alarm state, active alerts, covers open).
2. Call get_alarm_state() for full alarm panel details.
3. Call list_locks() to check the state of all locks.
4. Call list_covers() to find open doors, garage doors, or windows.
5. Call list_cameras() to verify cameras are available (don't fetch snapshots unless asked).
6. Call list_automations(search='lock') and list_automations(search='alarm') to review security automations.

Report:
- Current overall security status (armed/disarmed, locks open/closed, doors/windows)
- Any immediate concerns (unlocked doors, open garage, disarmed alarm)
- Security automations in place and any obvious gaps
- Specific recommendations

Keep the tone matter-of-fact. Only flag real issues, not hypothetical risks."""


@mcp.prompt()
def routine_optimizer() -> str:
    """
    Analyze usage patterns and suggest new automations to improve daily comfort.
    """
    return """Analyze this Home Assistant setup and suggest practical automation improvements.

Steps:
1. Call get_live_context() for current state.
2. Call list_automations() to understand what's already automated.
3. Call list_persons() to understand household composition.
4. Call list_climate() to see heating/cooling setup.
5. Call list_lights() to see the lighting setup.
6. Call get_logbook(hours=48) to see recent activity patterns (look for repeated manual actions).

Look for:
- Manual actions that happen repeatedly at the same time → suggest time-based automation
- Lights/devices left on when nobody is home → suggest presence-based automation
- Climate not adjusting for presence or time → suggest smart thermostat rules
- Missing "goodnight" / "leaving home" / "arriving home" scenes

Report:
- Top 3-5 automation suggestions ranked by impact on daily comfort
- For each: what it does, what trigger/condition/action to use
- Offer to create the automation if the user agrees (use create_automation())"""
