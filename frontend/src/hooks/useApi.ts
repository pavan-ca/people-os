import { useState, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface UseApiOptions {
  method?: string;
  body?: any;
}

export function useApi() {
  const { token, logout } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const request = useCallback(async (endpoint: string, options: UseApiOptions = {}) => {
    setLoading(true);
    setError(null);
    try {
      const headers: Record<string, string> = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      let bodyData = options.body;
      if (options.body && !(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
        bodyData = JSON.stringify(options.body);
      }

      const res = await fetch(`/api/v1${endpoint}`, {
        method: options.method || 'GET',
        headers,
        body: bodyData,
      });

      if (res.status === 401) {
        logout();
        throw new Error('Unauthorized');
      }

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'An error occurred');
      }
      
      return data;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [token, logout]);

  return { request, loading, error };
}
