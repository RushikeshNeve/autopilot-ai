"""Capability registry."""

CORE_CAPABILITIES = {
    "retrieve_knowledge": {
        "description": "Fetch relevant grounded information from the system knowledge layer",
        "requires_approval": False,
    },
    "generate_content": {
        "description": "Generate notes, summaries, plans, drafts, or structured content",
        "requires_approval": False,
    },
    "store_data": {
        "description": "Store tasks, notes, or outputs in connected systems like Notion or database",
        "requires_approval": False,
    },
    "schedule": {
        "description": "Schedule reminders, tasks, or events",
        "requires_approval": False,
    },
    "notify": {
        "description": "Send messages, alerts, or notifications",
        "requires_approval": True,
    },
}