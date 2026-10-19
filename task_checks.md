## Solvability
- The instruction should be minimal but contains the sufficient information for the agent to solve the task
- The instruction should include resource statement
- The agent should access sufficient data, environment with packages to solve the task
- The task labels are unambiguous and accurate

## Anti-Cheat
- Each task should be run with no internet except for api access.
  How the current setup enforces this: every `task.toml` sets `[agent] network_mode = "allowlist"`
  with `allowed_hosts` limited to the model API domains (chatgpt.com, openai.com, anthropic.com and
  their subdomains). Harbor attaches an egress-control sidecar to the agent container that resolves
  DNS and only forwards connections whose SNI/IP matches the allowlist; everything else is dropped,
  so `pip install`, `curl` and Python `urlopen` to any other host fail. Environment build stays
  `public` so the agent CLI can be installed, and each family's analysis packages are preinstalled
  in the agent image so nothing needs the network afterwards. The bootstrap service (data download
  with credentials) runs on the compose `default` network outside the sidecar and exits before the
  agent starts; no agent code runs in it. The verifier container is `network_mode = "no-network"`
  (the xray judge allowlists `api.openai.com` only). Codex's own web-search tool must also be turned
  off: pass `--agent-kwarg web_search=disabled` to Harbor's built-in Codex agent, which renders
  Codex's `-c web_search=disabled`. This flag alone is not an egress block
  (an earlier astra run fetched mimic-code SQL over plain HTTPS with it set); the allowlist is what
  stops the model from fetching pages, and the flag removes the hosted search tool on top of it.
  Verified with `research/agents/egress_probe.py` (only the allowlisted hosts are reachable from
  the agent container).
- test labels and bootstrap materials should be separate from the agent main container. The verifier should be in a separate container

## Trajectory Checks
- Check the model successes are reflecting model's genuine capabilities and not because of cheating or shortcuts
- Check model failures are reflecting model's genuine failures not because poor task design or environment issues.

