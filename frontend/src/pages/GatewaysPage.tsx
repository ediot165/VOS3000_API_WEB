import { useState } from 'react';
import { listMappingGateways, listRoutingGateways } from '../services/vosApi';

export default function GatewaysPage() {
  const [serverName, setServerName] = useState('');
  const [mgs, setMgs] = useState<any[]>([]);
  const [rgs, setRgs] = useState<any[]>([]);
  const [msg, setMsg] = useState('');

  const load = () => {
    if (!serverName) return;
    listMappingGateways(serverName)
      .then((res) => setMgs(res.data))
      .catch((e) => setMsg(e.message));
    listRoutingGateways(serverName)
      .then((res) => setRgs(res.data))
      .catch((e) => setMsg(e.message));
  };

  return (
    <div>
      <h2>Gateways</h2>
      <div>
        <input value={serverName} onChange={(e)=>setServerName(e.target.value)} placeholder="Server name" />
        <button onClick={load}>Load</button>
      </div>
      {msg && <p>{msg}</p>}
      <h3>Mapping Gateways</h3>
      <ul>
        {mgs.map((mg) => (
          <li key={mg.name}>{mg.name}</li>
        ))}
      </ul>
      <h3>Routing Gateways</h3>
      <ul>
        {rgs.map((rg) => (
          <li key={rg.name}>{rg.name}</li>
        ))}
      </ul>
    </div>
  );
}
