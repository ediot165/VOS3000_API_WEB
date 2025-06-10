import { useState } from 'react';
import { searchNumbers } from '../services/vosApi';

export default function NumberLookupPage() {
  const [input, setInput] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [msg, setMsg] = useState('');

  const search = () => {
    searchNumbers(input)
      .then((res) => setResults(res.data))
      .catch((e) => setMsg(e.message));
  };

  return (
    <div>
      <h2>Number Lookup</h2>
      <textarea value={input} onChange={(e)=>setInput(e.target.value)} />
      <button onClick={search}>Search</button>
      {msg && <p>{msg}</p>}
      <ul>
        {results.map((r, idx) => (
          <li key={idx}>{r.Server} - {r.GatewayName} - {r.Field} - {r.FoundValues}</li>
        ))}
      </ul>
    </div>
  );
}
