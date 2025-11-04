# Is My Computer On Fire?                                                                                                                            
A command-line tool to check if your computer is on fire.

## Installation
```
pip install ismycomputeronfire
```
## Usage

### Command-Line Tool
```
ismycomputeronfire --chrome_tabs=30
```

If your computer is on fire, it will print a nice ASCII art fire. Otherwise, it will print "No.".

### Library
You can also use this package in your own Python code:
```python
from ismycomputeronfire import check

stats = {
    "npm_modules" = 10,
    "git_conflicts" = 21
}

check(**stats)
```
## Rules
Tuses a set of rules to determine if your computer is on fire. The following arguments are available:
 * `--chrome_tabs`                                                                                   
 * `--npm_packages`                                                                                  
 * `--slack_messages`                                                                                
 * `--docker_containers`                                                                             
 * `--days_to_release`                                                                               
 * `--jira_tickets_assigned`                                                                         
 * `--git_conflicts`                                                                                 
 * `--servers_running`
