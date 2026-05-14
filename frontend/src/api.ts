import AsyncStorage from '@react-native-async-storage/async-storage';

const BASE = process.env.EXPO_PUBLIC_BACKEND_URL;

async function getToken() {
  return AsyncStorage.getItem('auth_token');
}

export async function apiRequest(path: string, options: RequestInit = {}) {
  const token = await getToken();
  const headers: any = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE}/api${path}`, { ...options, headers });
  const text = await res.text();
  let data: any = {};
  try { data = text ? JSON.parse(text) : {}; } catch { data = { detail: text }; }
  if (!res.ok) {
    throw new Error(data.detail || `Erro ${res.status}`);
  }
  return data;
}

export const api = {
  get: (p: string) => apiRequest(p),
  post: (p: string, body: any) => apiRequest(p, { method: 'POST', body: JSON.stringify(body) }),
  put: (p: string, body: any) => apiRequest(p, { method: 'PUT', body: JSON.stringify(body) }),
  del: (p: string) => apiRequest(p, { method: 'DELETE' }),
};

export function formatBRL(value: number): string {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

export function formatDate(iso: string): string {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    return d.toLocaleDateString('pt-BR');
  } catch { return iso; }
}
