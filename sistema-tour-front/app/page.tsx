'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/hooks/useAuth';

export default function Home() {
  const router = useRouter();
  const { user, loading, idEmpresa } = useAuth();

  useEffect(() => {
    if (!loading) {
      if (user) {
        const empresa = idEmpresa || 'default';
        router.replace(`/${empresa}/dashboard`);
      } else {
        router.replace('/login');
      }
    }
  }, [user, loading, idEmpresa, router]);

  return (
    <main className="min-h-screen bg-gray-900 flex flex-col items-center justify-center p-4 text-white">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 border-4 border-emerald-400 border-t-transparent rounded-full animate-spin" />
        <p className="text-gray-400 font-medium">Cargando Tour OS...</p>
      </div>
    </main>
  );
}