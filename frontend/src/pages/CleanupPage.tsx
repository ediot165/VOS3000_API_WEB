import { useState } from 'react';
import { scanCleanup, executeCleanup } from '../services/vosApi';

export default function CleanupPage() {
  const [numbers, setNumbers] = useState('');
  const [scope, setScope] = useState('Both');
  const [candidates, setCandidates] = useState<any[]>([]);
  const [msg, setMsg] = useState('');

  const scan = () => {
    scanCleanup(numbers, scope)
      .then((res) => setCandidates(res.data))
      .catch((e) => setMsg(e.message));
  };

  const execute = () => {
    executeCleanup(numbers, candidates)
      .then((res) => setMsg('Executed: ' + res.data.length + ' results'))
      .catch((e) => setMsg(e.message));
  };

  return (
    <div>
      <h2>Cleanup</h2>
      <textarea value={numbers} onChange={(e)=>setNumbers(e.target.value)} />
      <select value={scope} onChange={(e)=>setScope(e.target.value)}>
        <option value="MG">MG</option>
        <option value="RG">RG</option>
        <option value="Both">Both</option>
      </select>
      <button onClick={scan}>Scan</button>
      <button onClick={execute}>Execute</button>
      {msg && <p>{msg}</p>}
      <ul>
        {candidates.map((c, idx) => (
          <li key={idx}>{c.server_name} - {c.gateway_name} ({c.gateway_type})</li>
        ))}
      </ul>
    </div>
  );
}
