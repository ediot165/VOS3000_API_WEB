import { useState } from 'react';
import {
  searchCustomers,
  updateCustomerCreditLimit,
  updateCustomerLockStatus,
} from '../services/vosApi';

interface Customer {
  AccountID: string;
  CustomerName?: string;
  ServerName: string;
  BalanceRaw?: number;
  CreditLimitRaw?: number;
  Status?: string;
}

export default function CustomersPage() {
  const [filterType, setFilterType] = useState('account');
  const [filterText, setFilterText] = useState('');
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [msg, setMsg] = useState('');

  const handleSearch = () => {
    searchCustomers(filterType, filterText)
      .then((res) => setCustomers(res.data))
      .catch((err) => setMsg(err.message));
  };

  const handleCreditUpdate = (c: Customer, newLimit: string) => {
    updateCustomerCreditLimit(c.ServerName, c.AccountID, newLimit).then(() => {
      setMsg('Updated credit limit');
    }).catch((e)=>setMsg(e.message));
  };

  const handleLockUpdate = (c: Customer, lock: string) => {
    updateCustomerLockStatus(c.ServerName, c.AccountID, lock).then(()=>{
      setMsg('Updated lock status');
    }).catch((e)=>setMsg(e.message));
  };

  return (
    <div>
      <h2>Customer Search</h2>
      <div>
        <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
          <option value="account">Account</option>
          <option value="name">Name</option>
        </select>
        <input value={filterText} onChange={(e)=>setFilterText(e.target.value)} />
        <button onClick={handleSearch}>Search</button>
      </div>
      {msg && <p>{msg}</p>}
      <table>
        <thead>
          <tr>
            <th>Account</th>
            <th>Name</th>
            <th>Server</th>
            <th>Credit Limit</th>
            <th>Lock</th>
          </tr>
        </thead>
        <tbody>
          {customers.map((c) => (
            <tr key={c.ServerName + c.AccountID}>
              <td>{c.AccountID}</td>
              <td>{c.CustomerName}</td>
              <td>{c.ServerName}</td>
              <td>
                <input
                  type="text"
                  placeholder={String(c.CreditLimitRaw ?? '')}
                  onBlur={(e) => handleCreditUpdate(c, e.target.value)}
                />
              </td>
              <td>
                <select onChange={(e) => handleLockUpdate(c, e.target.value)} defaultValue={c.Status === 'Locked' ? '1' : '0'}>
                  <option value="0">Unlock</option>
                  <option value="1">Lock</option>
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
