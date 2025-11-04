rules = [
        ("chrome_tabs", lambda v: v > 3),
        ("slack_messages", lambda v: v > 15),
        ("docker_containers", lambda v: v > 10),
        ("days_to_release", lambda v: v < 3),
        ("jira_tickets_assigned", lambda v: v > 12),
        ("npm_packages", lambda v: v > 0),
        ("git_conflicts", lambda v: v > 10),
        ("servers_running", lambda v: v > 4)
]

