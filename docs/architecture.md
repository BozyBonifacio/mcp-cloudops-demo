# Architecture

```mermaid
flowchart LR
    U[User] --> C[MCP-compatible AI client]
    C <-->|MCP over stdio| S[MCP CloudOps Demo Server]

    S --> T[Tools]
    S --> R[Resources]
    S --> P[Prompts]

    T --> D[(Fake JSON data)]
    R --> D
    P --> C

    T1[list_servers] --> T
    T2[get_server_health] --> T
    T3[get_recent_deployments] --> T
    T4[get_open_incidents] --> T
    T5[search_logs] --> T
    T6[restart_demo_service] --> T

    R1[infra://inventory/all] --> R
    R2[infra://inventory/production] --> R
    R3[ops://incidents/open] --> R

    P1[investigate_incident] --> P
    P2[daily_cloudops_summary] --> P
```

## Design goals

- Free to run locally.
- Safe for a public GitHub repository.
- No Azure subscription or API keys required.
- Deterministic data makes demos and tests repeatable.
- Separation between MCP interface and data source makes future Azure integration straightforward.
