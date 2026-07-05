'use client';

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get('redirectTo') || null;

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const supabase = createClient();
    const { data, error: authError } = await supabase.auth.signInWithPassword({ email, password });

    if (authError) {
      setError('Correo o contraseña incorrectos. Verificá tus datos.');
      setLoading(false);
      return;
    }

    // Obtenemos el id_empresa del metadata del usuario (lo cargamos al crear el user en Supabase)
    const idEmpresa = data.user?.user_metadata?.id_empresa ?? 'default';
    const rol = data.user?.user_metadata?.rol ?? 'vendedor';

    // Redirigir según rol o la URL de destino guardada
    if (redirectTo) {
      router.push(redirectTo);
    } else if (rol === 'guia') {
      // Los guías solo tienen acceso al escáner
      router.push(`/${idEmpresa}/scanner`);
    } else {
      router.push(`/${idEmpresa}/dashboard`);
    }

    router.refresh();
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-900 via-emerald-950 to-gray-900 flex items-center justify-center p-4 font-sans">
      <div className="w-full max-w-[400px]">

        {/* Logo / Cabecera */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-emerald-500 rounded-2xl mb-4 shadow-lg shadow-emerald-500/30">
            <span className="text-3xl">🌴</span>
          </div>
          <h1 className="text-3xl font-black text-white">Tour OS</h1>
          <p className="text-emerald-400 text-sm mt-1 font-semibold">Sistema de Control de Tours</p>
        </div>

        {/* Card de Login */}
        <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-3xl p-8 shadow-2xl">
          <h2 className="text-xl font-black text-white mb-6 text-center">Iniciar Sesión</h2>

          <form onSubmit={handleLogin} className="flex flex-col gap-4">
            <div>
              <label className="block text-xs font-bold text-emerald-400 uppercase tracking-widest mb-2">
                Correo Electrónico
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="admin@tuagencia.com"
                className="w-full p-3.5 rounded-xl bg-white/10 border border-white/20 text-white placeholder:text-white/30 focus:border-emerald-400 focus:bg-white/15 outline-none transition-all text-[16px]"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-emerald-400 uppercase tracking-widest mb-2">
                Contraseña
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full p-3.5 rounded-xl bg-white/10 border border-white/20 text-white placeholder:text-white/30 focus:border-emerald-400 focus:bg-white/15 outline-none transition-all text-[16px]"
              />
            </div>

            {error && (
              <div className="bg-red-500/20 border border-red-500/40 text-red-300 text-sm font-semibold p-3 rounded-xl text-center">
                ⚠️ {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className={`mt-2 p-4 rounded-xl font-black text-base transition-all active:scale-[0.98] ${
                loading
                  ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  : 'bg-emerald-500 hover:bg-emerald-400 text-white shadow-lg shadow-emerald-500/30 hover:-translate-y-0.5'
              }`}
            >
              {loading ? '⏳ Ingresando...' : '🚀 Ingresar al Sistema'}
            </button>
          </form>

          <p className="text-center text-white/30 text-xs mt-6">
            ¿Olvidaste tu contraseña? Contactá a tu administrador.
          </p>
        </div>

        <p className="text-center text-white/20 text-xs mt-6">
          Tour OS © 2026 · Todos los derechos reservados
        </p>
      </div>
    </main>
  );
}
