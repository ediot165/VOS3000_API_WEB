import axios from 'axios';

const baseURL = import.meta.env.VOS_API_BASE_URL || '';

const api = axios.create({ baseURL });

export const getServers = () => api.get('/servers/');

export const searchCustomers = (filterType: string, filterText: string) =>
  api.get('/customers/search/', { params: { filter_type: filterType, filter_text: filterText } });

export const getCustomerDetails = (server: string, accountId: string) =>
  api.get(`/customers/${server}/${accountId}/details/`);

export const updateCustomerCreditLimit = (
  server: string,
  accountId: string,
  newLimit: string
) => api.put(`/customers/${server}/${accountId}/credit-limit/`, { new_credit_limit: newLimit });

export const updateCustomerLockStatus = (
  server: string,
  accountId: string,
  lockStatus: string
) => api.put(`/customers/${server}/${accountId}/lock-status/`, { lock_status: lockStatus });

// Gateways
export const listMappingGateways = (server: string) =>
  api.get(`/gateways/${server}/mapping-gateways/`);
export const listRoutingGateways = (server: string) =>
  api.get(`/gateways/${server}/routing-gateways/`);

// Number Info
export const searchNumbers = (search_terms_raw: string) =>
  api.post('/number-info/search/', { search_terms_raw });

// Cleanup
export const scanCleanup = (numbers_raw: string, scope: string) =>
  api.post('/cleanup/scan/', { numbers_raw, scope });
export const executeCleanup = (original_numbers_to_remove_raw: string, items_to_clean: any[]) =>
  api.post('/cleanup/execute/', { original_numbers_to_remove_raw, items_to_clean });

export default api;
