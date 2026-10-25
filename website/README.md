# Local website preview

The site is an Astro static site. It uses the same components and styles for
both benchmark releases. The default page shows v2; the navigation dropdown
switches between `/HealthAgentBench/v1/` and `/HealthAgentBench/v2/` and keeps
the selected version when opening detailed results.

Use a Node.js version supported by Astro (for example Node 22), with npm 9.6.5
or later:

```bash
cd website
npm ci
npm run dev -- --host 127.0.0.1 --port 4321
```

Open <http://localhost:4321/HealthAgentBench/>. For a remote development machine,
forward port 4321 to your local browser.

`npm run build` builds the site locally; it does not deploy anything. Publishing
is handled separately by `.github/workflows/deploy.yml` on a push to `main` or
an explicit workflow dispatch.

## Release data

- `src/data/results.json` and `tasks.json` are the frozen v1 release. Normal
  builds preserve them, even when a newer paper checkout is available.
- `src/data/results-v2.json` and `tasks-v2.json` describe 75 tasks, nine
  categories, and six agents. The results include one selected scored attempt
  per agent/task. Only public aggregates are exported to the site.
- To refresh the v2 snapshot from the paper's selected results:

  ```bash
  npm run gen:v2 -- --input ../../medcli-paper-latex/figures/results_v2/trial_metrics.json
  npm run build
  ```

The exporter checks task coverage and recomputes scores and costs from the
selected trials. It preserves the leaderboard's existing lower-cost tie break.
Builds use the exported snapshots and do not need the private paper or raw runs.
