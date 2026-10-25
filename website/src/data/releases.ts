import v1Results from './results.json';
import v1Tasks from './tasks.json';
import v2Results from './results-v2.json';
import v2Tasks from './tasks-v2.json';

export function releaseData(version: 'v1' | 'v2') {
  return version === 'v1'
    ? { results: v1Results, tasks: v1Tasks }
    : { results: v2Results, tasks: v2Tasks };
}
