import argparse
from .main import check

def main():
    parser = argparse.ArgumentParser(prog = "ismycomputeronfire")

    parser.add_argument("--chrome_tabs", type=int)
    parser.add_argument("--slack_messages", type=int)
    parser.add_argument("--docker_containers", type=int)
    parser.add_argument("--days_to_release", type=int)
    parser.add_argument("--jira_tickets_assigned", type=int)
    parser.add_argument("--npm_packages", type=int)
    parser.add_argument("--git_conflicts", type=int)
    parser.add_argument("--servers_running", type=int)

    args = parser.parse_args()

    stats = {
        "chrome_tabs": args.chrome_tabs,
        "slack_messages": args.slack_messages,
        "docker_containers": args.docker_containers,
        "jira_tickets_assigned": args.jira_tickets_assigned,
        "docker_containers": args.docker_containers,
        "npm_packages": args.npm_packages,
        "git_conflicts": args.git_conflicts,
        "servers_running": args.servers_running,
    }

    check(**stats)

