// Build-time data generation.
//
// Source of truth:
//   medcli-paper-latex/figures/baseline_metrics.json
//     flat per-(task category, harness, model) records
//   medcli-paper-latex/figures/coverage_data.tex
//     auto-generated task counts used by the paper's pooled leaderboard
//
// This script pivots the metrics into agents x task-categories, computes the
// paper-aligned pooled task-resolution score (weighted by the number of tasks
// in each category), ranks the agents, and writes src/data/results.json which
// the Astro pages import at build time. We never run the paper's Python here —
// the source files are committed in the submodule.
//
// The paper repo is PRIVATE, so the submodule is not checked out in CI. The
// generated src/data/results.json is therefore committed to this repo. This
// script only regenerates it when the private submodule IS present (local
// dev); in CI the source is absent and we keep the committed file. Run
// `npm run gen` locally after updating the submodule to refresh the numbers.

import { readFileSync, writeFileSync, mkdirSync, existsSync, unlinkSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { tmpdir } from 'node:os';
import { spawnSync } from 'node:child_process';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const SRC = resolve(ROOT, 'medcli-paper-latex/figures/baseline_metrics.json');
const COUNTS = resolve(ROOT, 'medcli-paper-latex/figures/coverage_data.tex');
const COLLECT = resolve(ROOT, 'medcli-paper-latex/scripts/collect_baseline_metrics.py');
const OUT = resolve(ROOT, 'src/data/results.json');
const LIVE_MEDCLI_CANDIDATES = [
  resolve(ROOT, '../medcli'),
  resolve(ROOT, '../MedCLI'),
];

const TASK_ORDER = [
  'xray_report_correction',
  'tumor_area_selection_pathology',
  'ct_abnormality',
  'ehr_data_quality',
  'ehr_to_meds_etl',
  'ehr_event_modelling',
  'clinical_trial_matching',
];

const TASK_COUNT_KEYS = {
  ehr_to_meds_etl: 'Meds',
  xray_report_correction: 'Xray',
  clinical_trial_matching: 'Ctm',
  ct_abnormality: 'Ct',
  tumor_area_selection_pathology: 'Tumor',
  ehr_event_modelling: 'Ehrshot',
  ehr_data_quality: 'Dq',
};

function collectLiveMetrics() {
  const medcliRoot = LIVE_MEDCLI_CANDIDATES.find((dir) => existsSync(resolve(dir, 'paper/baselines.md')));
  if (!medcliRoot || !existsSync(COLLECT)) return null;

  const outPath = resolve(tmpdir(), `medcli-live-baseline-metrics-${process.pid}.json`);
  for (const python of ['python3', 'python']) {
    const run = spawnSync(python, [COLLECT, medcliRoot, '--out', outPath], {
      cwd: ROOT,
      encoding: 'utf8',
    });
    if (run.status === 0 && existsSync(outPath)) {
      const records = JSON.parse(readFileSync(outPath, 'utf8'));
      unlinkSync(outPath);
      return {
        generatedFrom: `${medcliRoot}/paper/baselines.md`,
        records,
      };
    }
  }
  return null;
}

// Private-submodule guard: if no source metrics are available, fall back to the
// committed results.json (the normal case in CI) instead of crashing.
if (!existsSync(SRC) && !LIVE_MEDCLI_CANDIDATES.some((dir) => existsSync(resolve(dir, 'paper/baselines.md')))) {
  if (existsSync(OUT)) {
    console.log('build-results: paper submodule not present; using committed src/data/results.json');
    process.exit(0);
  }
  console.error(
    'build-results: medcli-paper-latex/figures/baseline_metrics.json not found and no committed ' +
      'src/data/results.json exists. Check out the submodule and re-run `npm run gen`.',
  );
  process.exit(1);
}

// Human-facing model label, agent label, vendor, and harness for each model id.
function describe(harness, model) {
  const is1m = model.endsWith('-1m');
  const base = is1m ? model.slice(0, -3) : model;
  const normalizedBase = base.toLowerCase().replace(/\./g, '-');
  const suffix = is1m ? ' (1M)' : '';

  const NAMES = {
    'gpt-5-5': 'GPT 5.5',
    'gpt-5-4': 'GPT 5.4',
    'gpt-5-4-mini': 'GPT 5.4 Mini',
    'gpt-5-3-codex': 'GPT 5.3',
    'claude-opus-4-8': 'Opus 4.8',
    'claude-opus-4-7': 'Opus 4.7',
    'claude-opus-4-6': 'Opus 4.6',
    'claude-sonnet-4-6': 'Sonnet 4.6',
  };
  const modelLabel = (NAMES[normalizedBase] ?? base) + suffix;
  const company = normalizedBase.startsWith('gpt') ? 'OpenAI' : 'Anthropic';
  const harnessLabel =
    {
      codex: 'Codex',
      'copilot-cli': 'Copilot',
      'claude-code': 'Claude Code',
    }[harness] ?? harness;
  const agentLabel = `${harnessLabel} (${modelLabel})`;
  return { modelLabel, agentLabel, company, harnessLabel };
}

const committedRecords = existsSync(SRC) ? JSON.parse(readFileSync(SRC, 'utf8')) : null;
const liveMetrics = collectLiveMetrics();
const liveByKey = new Map((liveMetrics?.records ?? []).map((r) => [`${r.harness}::${r.model}::${r.task}`, r]));
const committedByKey = new Map((committedRecords ?? []).map((r) => [`${r.harness}::${r.model}::${r.task}`, r]));
const mergedKeys = new Set([...liveByKey.keys(), ...committedByKey.keys()]);
const records = [...mergedKeys].map((key) => {
  const live = liveByKey.get(key);
  const committed = committedByKey.get(key);
  if (live && committed) {
    return {
      ...committed,
      ...live,
      avg_turns: live.avg_turns ?? committed.avg_turns,
      n_trials_with_turns: live.n_trials_with_turns ?? committed.n_trials_with_turns,
      run_dirs: live.run_dirs ?? committed.run_dirs,
    };
  }
  return live ?? committed;
});
const countsTex = readFileSync(COUNTS, 'utf8');

function loadTaskCounts() {
  return Object.fromEntries(
    Object.entries(TASK_COUNT_KEYS).map(([task, key]) => {
      const match = countsTex.match(new RegExp(`\\\\def\\\\count${key}\\{(\\d+)\\}`));
      if (!match) throw new Error(`Missing task-count macro for ${task} (count${key}) in coverage_data.tex`);
      return [task, Number(match[1])];
    }),
  );
}

const scoreMetric = records[0]?.score_metric ?? 'mean reward';
const taskCounts = loadTaskCounts();
const seenTasks = new Set(records.map((r) => r.task));
const tasks = TASK_ORDER.filter((task) => seenTasks.has(task));
const totalTaskCount = tasks.reduce((sum, task) => sum + (taskCounts[task] ?? 0), 0);

// Group records by agent (harness + model).
const byAgent = new Map();
for (const r of records) {
  const key = `${r.harness}::${r.model}`;
  if (!byAgent.has(key)) byAgent.set(key, { harness: r.harness, model: r.model, perTask: {} });
  byAgent.get(key).perTask[r.task] = {
    score: r.score,
    successes: r.successes ?? null,
    totalTrials: r.total_trials ?? null,
    costUsd: r.cost_usd,
    avgTurns: r.avg_turns,
    wallTimeS: r.wall_time_s,
  };
}

// Keep agents that cover every scored task-category, so the paper-aligned
// pooled score is computed over the same denominator for everyone. Partial
// coverage variants are reported separately.
const agents = [];
const partial = [];
for (const a of byAgent.values()) {
  const meta = describe(a.harness, a.model);
  const covered = tasks.filter((t) => a.perTask[t] !== undefined);
  const coveredTaskCount = covered.reduce((sum, task) => sum + (taskCounts[task] ?? 0), 0);
  const totalSuccesses = covered.reduce((sum, task) => sum + (a.perTask[task].successes ?? 0), 0);
  const totalTrials = covered.reduce((sum, task) => sum + (a.perTask[task].totalTrials ?? 0), 0);
  const pooled =
    totalTrials > 0
      ? totalSuccesses / totalTrials
      : coveredTaskCount === 0
        ? 0
        : covered.reduce((sum, task) => sum + a.perTask[task].score * taskCounts[task], 0) / coveredTaskCount;
  const totalCostUsd = covered.reduce((s, t) => s + (a.perTask[t].costUsd ?? 0), 0);
  const costTrialWeight = covered.reduce((s, t) => s + (a.perTask[t].totalTrials ?? 0), 0);
  const costPerTaskUsd =
    costTrialWeight > 0
      ? covered.reduce((s, t) => s + (a.perTask[t].costUsd ?? 0) * (a.perTask[t].totalTrials ?? 0), 0) / costTrialWeight
      : null;
  const entry = {
    ...meta,
    harnessId: a.harness,
    model: a.model,
    pooled,
    nTaskCategories: covered.length,
    nTasks: coveredTaskCount,
    totalCostUsd,
    costPerTaskUsd,
    perTask: a.perTask,
  };
  (covered.length === tasks.length ? agents : partial).push(entry);
}

// Rank by pooled score (desc), tie-break on lower sweep cost.
agents.sort((x, y) => y.pooled - x.pooled || x.totalCostUsd - y.totalCostUsd);
agents.forEach((a, i) => (a.rank = i + 1));

// Best score per task across the full-coverage agents (for the task grid).
const bestByTask = {};
for (const t of tasks) {
  bestByTask[t] = Math.max(...agents.map((a) => a.perTask[t]?.score ?? 0));
}

const out = {
  generatedFrom: liveMetrics?.generatedFrom ?? 'medcli-paper-latex/figures/baseline_metrics.json',
  scoreMetric,
  tasks,
  taskCounts,
  totalTaskCount,
  agents,
  partial,
  bestByTask,
};

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, JSON.stringify(out, null, 2) + '\n');
console.log(
  `build-results: ${agents.length} agents x ${tasks.length} tasks ` +
    `(+${partial.length} partial) -> src/data/results.json`,
);
