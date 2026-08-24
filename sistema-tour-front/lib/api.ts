import { createClient } from '@/lib/supabase/client';

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1';
export const FRONTEND_SECRET = process.env.NEXT_PUBLIC_FRONTEND_SECRET || 'SST_FRONT_ACCESS_SECRET_2026';

export async function getAuthHeaders(): Promise<HeadersInit> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-API-Key': FRONTEND_SECRET,
  };

  try {
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) {
      headers['Authorization'] = `Bearer ${session.access_token}`;
    }
  } catch {
    // Si falla la obtención de sesión en contexto sin cliente, continúa solo con X-API-Key
  }

  return headers;
}

export async function fetchAPI(endpoint: string, options: RequestInit = {}): Promise<Response> {
  const authHeaders = await getAuthHeaders();
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${API_BASE_URL}${cleanEndpoint}`;

  const mergedHeaders: HeadersInit = {
    ...authHeaders,
    ...(options.headers || {}),
  };

  return fetch(url, {
    ...options,
    headers: mergedHeaders,
  });
}
