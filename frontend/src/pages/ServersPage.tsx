import { useEffect, useState } from 'react';
import { getServers } from '../services/vosApi';

export default function ServersPage() {
  const [servers, setServers] = useState<any[]>([]);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    getServers()
      .then((res) => setServers(res.data.cac_server_da_cau_hinh || []))
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>Configured Servers</h2>
      <ul>
        {servers.map((srv, idx) => (
          <li key={idx}>{srv.name} - {srv.url}</li>
        ))}
      </ul>
    </div>
  );
}
