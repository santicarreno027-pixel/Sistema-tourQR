'use client';

import { useState } from 'react';

export default function Home() {
  const [statusBackend, setStatusBackend] = useState<string>('Sin conectar');

  const probarConexion = async () => {
    try {
      // Intentamos pegarle a la raíz de tu FastAPI (asegúrate de que el puerto sea el correcto)
      const response = await fetch('http://localhost:8001/');
      const data = await response.json();
      
      if (response.ok) {
        setStatusBackend(`🟢 Conectado con éxito: ${data.message}`);
      } else {
        setStatusBackend('🔴 Error en el servidor');
      }
    } catch (error) {
      setStatusBackend('🔴 No se pudo conectar al backend. ¿Está encendido Uvicorn en el puerto 8001?');
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-900 text-white">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm flex flex-col gap-6">
        <h1 className="text-4xl font-bold text-teal-400">Sistema Tour SaaS</h1>
        <p className="text-gray-400 text-lg">Validación del canal de comunicación Frontend ➔ Backend</p>
        
        <button 
          onClick={probarConexion}
          className="px-6 py-3 bg-teal-600 border border-teal-500 rounded-lg font-semibold hover:bg-teal-700 transition-colors text-white"
        >
          Probar Conexión con FastAPI
        </button>

        <div className="p-4 bg-gray-800 border border-gray-700 rounded-md w-full text-center text-xl">
          {statusBackend}
        </div>
      </div>
    </main>
  );
}