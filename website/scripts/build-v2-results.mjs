// Export only public aggregate numbers from the paper's selected 450 trials.
// Normal builds use the committed snapshot and never need private run data.
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const out = resolve(root, 'src/data/results-v2.json');
const inputIndex = process.argv.indexOf('--input');
if (inputIndex < 0) {
  if (!existsSync(out)) throw new Error('Missing v2 snapshot; run npm run gen:v2 -- --input <trial_metrics.json>');
  console.log('build-v2-results: using committed v2 results-v2.json');
  process.exit(0);
}
if (!process.argv[inputIndex + 1]) throw new Error('--input requires a trial_metrics.json path');
const raw = readFileSync(resolve(process.argv[inputIndex + 1]));
const data = JSON.parse(raw);
const taskMeta = JSON.parse(readFileSync(resolve(root, 'src/data/tasks-v2.json'), 'utf8'));
const families = taskMeta.families;
const tasks = families.map((family) => family.metricsKey);
const taskCounts = Object.fromEntries(families.map((family) => [family.metricsKey, family.taskCount]));
const totalTaskCount = families.reduce((sum, family) => sum + family.taskCount, 0);
if (data.task_count !== totalTaskCount || totalTaskCount !== 75 || data.attempts_per_task !== 1) {
  throw new Error('Expected the selected 75-task, one-attempt v2 suite');
}
if (data.records.length !== data.models.length * totalTaskCount || data.models.length !== 6) {
  throw new Error('Expected 450 selected trials across six agents');
}
const modelNames = {
  'gpt-5.6-sol': 'GPT-5.6-sol', 'gpt-6-astra': 'GPT-6-astra', 'gpt-6-sol': 'GPT-6-sol',
  'claude-opus-5': 'Opus 5', 'claude-opus-5-5': 'Opus 5.5', 'claude-sonnet-5-5': 'Sonnet 5.5',
};
const agents = data.models.map((model) => {
  const rows = data.records.filter((row) => row.model === model.model);
  if (rows.length !== totalTaskCount || new Set(rows.map((row) => row.task)).size !== totalTaskCount) {
    throw new Error(`Incomplete or duplicate tasks for ${model.model}`);
  }
  const harnessId = rows[0].harness;
  const harnessLabel = harnessId === 'codex' ? 'Codex' : 'Claude Code';
  const perTask = Object.fromEntries(families.map((family) => {
    const selected = rows.filter((row) => row.category === family.category);
    if (selected.length !== family.taskCount) throw new Error(`Wrong task count for ${model.model}/${family.category}`);
    const sum = (key) => selected.reduce((total, row) => total + row[key], 0);
    const turns = selected.filter((row) => row.plot_turns !== null);
    return [family.metricsKey, {
      score: sum('reward') / selected.length, successes: sum('reward'), totalTrials: selected.length,
      costUsd: sum('cost_usd') / selected.length, wallTimeS: sum('trial_time_s') / selected.length,
      avgTurns: turns.length ? turns.reduce((total, row) => total + row.plot_turns, 0) / turns.length : null,
    }];
  }));
  const successes = rows.reduce((sum, row) => sum + row.reward, 0);
  const totalCostUsd = rows.reduce((sum, row) => sum + row.cost_usd, 0);
  if (successes !== model.passes || Math.abs(totalCostUsd - model.cost_usd) > 1e-7) {
    throw new Error(`Aggregate mismatch for ${model.model}`);
  }
  const modelLabel = modelNames[model.model];
  if (!modelLabel) throw new Error(`Unknown model ${model.model}`);
  return {
    modelLabel, agentLabel: `${harnessLabel} (${modelLabel})`, company: harnessId === 'codex' ? 'OpenAI' : 'Anthropic',
    harnessLabel, harnessId, model: model.model, pooled: successes / totalTaskCount,
    nTaskCategories: families.length, nTasks: totalTaskCount, totalCostUsd,
    costPerTaskUsd: totalCostUsd / totalTaskCount, perTask,
  };
});
// Keep the existing leaderboard's lower-cost tie break.
agents.sort((a, b) => b.pooled - a.pooled || a.totalCostUsd - b.totalCostUsd);
agents.forEach((agent, index) => { agent.rank = index + 1; });
const result = {
  version: 'v2', generatedFrom: 'medcli-paper-latex/figures/results_v2/trial_metrics.json',
  sourceSha256: createHash('sha256').update(raw).digest('hex'), scoreMetric: 'mean reward',
  attemptsPerTask: 1, selectedTrials: data.records.length,
  evaluationNote: 'One scored attempt per task; xhigh reasoning; model API access only; web tools disabled.',
  caveats: [],
  tasks, taskCounts, totalTaskCount, agents, partial: [],
  bestByTask: Object.fromEntries(tasks.map((task) => [task, Math.max(...agents.map((agent) => agent.perTask[task].score))])),
};
writeFileSync(out, JSON.stringify(result, null, 2) + '\n');
console.log(`build-v2-results: ${agents.length} agents × ${totalTaskCount} tasks -> src/data/results-v2.json`);
