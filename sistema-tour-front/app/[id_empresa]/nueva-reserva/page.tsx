'use client';

import { useParams } from 'next/navigation';
import { useState } from 'react';
import { fetchAPI } from '@/lib/api';

export default function NuevaReservaPage() {
  const params = useParams();
  const idEmpresa = params.id_empresa as string;

  const hoy = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Cancun',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).format(new Date());

  // Estados del Formulario
  const [folioFisico, setFolioFisico] = useState('');
  const [vendedorNombre, setVendedorNombre] = useState('');
  const [clienteNombre, setClienteNombre] = useState('');
  const [clienteTelefono, setClienteTelefono] = useState('');
  const [clienteEmail, setClienteEmail] = useState('');
  const [tourNombre, setTourNombre] = useState('');
  const [montoTotal, setMontoTotal] = useState<number | ''>('');
  const [montoDeposito, setMontoDeposito] = useState<number | ''>(''); // <-- NUEVO ESTADO PARA EL ANTICIPO
  const [fechaServicio, setFechaServicio] = useState(hoy);
  const [horaSalida, setHoraSalida] = useState('OPEN');
  const [ubicacionPickup, setUbicacionPickup] = useState('');
  
  const [paxAdultos, setPaxAdultos] = useState(1);
  const [paxMenores, setPaxMenores] = useState(0);
  const [paxInfantes, setPaxInfantes] = useState(0);

  // Llave única para evitar cobros dobles si el usuario da múltiples clics rápidos
  const [idempotencyKey, setIdempotencyKey] = useState(() => crypto.randomUUID());

  // Estados del Conversor y Modal
  const [isConversorOpen, setIsConversorOpen] = useState(false);
  const [calcMonto, setCalcMonto] = useState<number | ''>('');
  const [calcTipoCambio, setCalcTipoCambio] = useState<number>(17.50);

  const [loading, setLoading] = useState(false);
  const [mensajeStatus, setMensajeStatus] = useState<{ tipo: 'exito' | 'error' | null, texto: string }>({ tipo: null, texto: '' });

  const handleEnviar = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMensajeStatus({ tipo: null, texto: '' });

    const payload = {
      id_empresa: idEmpresa,
      folio_fisico: folioFisico || "N/A",
      vendedor_nombre: vendedorNombre,
      monto_total: Number(montoTotal),
      monto_deposito: Number(montoDeposito), // <-- SE ENVÍA AL BACKEND
      cliente_nombre: clienteNombre,
      cliente_telefono: clienteTelefono || "N/A",
      cliente_email: clienteEmail,
      tour_nombre: tourNombre,
      fecha_servicio: fechaServicio,
      hora_salida: horaSalida,
      ubicacion_pickup: ubicacionPickup || "N/A",
      pax_adultos: Number(paxAdultos),
      pax_menores: Number(paxMenores),
      pax_infantes: Number(paxInfantes)
    };

    try {
      const response = await fetchAPI('/reservas/', {
        method: 'POST',
        headers: {
          'Idempotency-Key': idempotencyKey
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        setMensajeStatus({ tipo: 'exito', texto: `¡Venta de ${clienteNombre} registrada con éxito! 🌸` });
        setFolioFisico(''); setClienteNombre(''); setClienteTelefono(''); setClienteEmail(''); setUbicacionPickup(''); setMontoTotal(''); setMontoDeposito(''); setTourNombre(''); setHoraSalida('OPEN');
        setIdempotencyKey(crypto.randomUUID());
      } else {
        const data = await response.json();
        setMensajeStatus({ tipo: 'error', texto: `Error (${response.status}): ${JSON.stringify(data.detail)}` });
      }
    } catch (error) {
      setMensajeStatus({ tipo: 'error', texto: 'Error de conexión con el backend.' });
    } finally {
      setLoading(false);
    }
  };

  // Clases homologadas con diseño premium móvil
  const inputClass = "w-full p-3 md:p-4 border border-gray-200 rounded-xl bg-gray-50 focus:border-tropical-green focus:bg-white focus:ring-4 focus:ring-tropical-green/10 outline-none transition-all duration-300 text-tropical-text text-[16px]"; // text-[16px] evita el zoom automático en iOS
  const labelClass = "block mb-2 font-semibold text-sm uppercase tracking-wider text-gray-500";

  return (
    <main className="min-h-screen bg-tropical-bg p-4 md:p-8 flex justify-center font-sans w-full">
      <div className="w-full max-w-[600px] flex flex-col gap-6">
        
        {/* CARD FORMULARIO PRINCIPAL */}
        <div className="bg-white p-6 md:p-8 rounded-3xl shadow-[0_20px_50px_rgba(0,0,0,0.05)] border-t-[8px] border-tropical-green w-full">
          <div className="text-center mb-8">
            <span className="text-xs font-bold tracking-widest text-emerald-600 uppercase bg-emerald-50 px-4 py-1.5 rounded-full mb-3 inline-block shadow-sm">
              Empresa: {idEmpresa}
            </span>
            <h2 className="text-tropical-text text-2xl md:text-3xl font-black m-0">🌸 Nueva Venta</h2>
            <p className="text-gray-400 text-sm mt-2">Registra un nuevo pasajero al instante</p>
          </div>

          <form onSubmit={handleEnviar} className="flex flex-col gap-8">
            
            {/* SECCIÓN: VENDEDOR Y FOLIO */}
            <div className="bg-gray-50/50 p-5 rounded-2xl border border-gray-100">
              <h3 className="text-sm font-black text-tropical-green uppercase tracking-widest mb-4 flex items-center gap-2">
                <span className="text-xl">🧑‍💼</span> 1. Vendedor y Registro
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className={labelClass}>Vendedor</label>
                  <input type="text" required value={vendedorNombre} onChange={(e) => setVendedorNombre(e.target.value)} placeholder="Tu nombre" className={inputClass} />
                </div>
                <div>
                  <label className={labelClass}>Folio Físico</label>
                  <input type="text" value={folioFisico} onChange={(e) => setFolioFisico(e.target.value)} placeholder="Ej: A-4592 (opcional)" className={inputClass} />
                </div>
              </div>
            </div>

            {/* SECCIÓN: DATOS DEL CLIENTE */}
            <div className="bg-gray-50/50 p-5 rounded-2xl border border-gray-100">
              <h3 className="text-sm font-black text-tropical-green uppercase tracking-widest mb-4 flex items-center gap-2">
                <span className="text-xl">🧳</span> 2. Datos del Cliente
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className={labelClass}>Nombre Completo</label>
                  <input type="text" required value={clienteNombre} onChange={(e) => setClienteNombre(e.target.value)} placeholder="Nombre del turista" className={inputClass} />
                </div>
                <div>
                  <label className={labelClass}>Email</label>
                  <input type="email" required value={clienteEmail} onChange={(e) => setClienteEmail(e.target.value)} placeholder="cliente@correo.com" className={inputClass} />
                </div>
                <div>
                  <label className={labelClass}>Teléfono</label>
                  <input type="tel" value={clienteTelefono} onChange={(e) => setClienteTelefono(e.target.value)} placeholder="9841234567 (opcional)" className={inputClass} />
                </div>
              </div>
            </div>

            {/* SECCIÓN: DETALLES DEL TOUR */}
            <div className="bg-gray-50/50 p-5 rounded-2xl border border-gray-100">
              <h3 className="text-sm font-black text-tropical-green uppercase tracking-widest mb-4 flex items-center gap-2">
                <span className="text-xl">🌴</span> 3. Servicio Contratado
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className={labelClass}>Tour Seleccionado</label>
                  <select required value={tourNombre} onChange={(e) => setTourNombre(e.target.value)} className={`${inputClass} appearance-none`}>
                    <option value="" disabled>Selecciona tour...</option>
                    <option value="Xcaret Plus">Xcaret Plus</option>
                    <option value="Chichen Itza">Chichén Itzá</option>
                    <option value="Tulum Coba">Tulum & Cobá</option>
                    <option value="Cenotes Playa">Ruta de Cenotes</option>
                    <option value="Catamaran">Catamarán Isla Mujeres</option>
                    <option value="Cozumel Snorkel">Cozumel Snorkel</option>
                  </select>
                </div>
                <div>
                  <label className={labelClass}>Fecha de Servicio</label>
                  <input type="date" required value={fechaServicio} onChange={(e) => setFechaServicio(e.target.value)} className={inputClass} />
                </div>
                <div>
                  <label className={labelClass}>Hora de Salida</label>
                  <input type="text" required value={horaSalida} onChange={(e) => setHoraSalida(e.target.value)} placeholder="08:00 o OPEN" className={inputClass} />
                </div>
                <div className="md:col-span-2">
                  <label className={labelClass}>Punto de Encuentro</label>
                  <input type="text" value={ubicacionPickup} onChange={(e) => setUbicacionPickup(e.target.value)} placeholder="Hotel (opcional)" className={inputClass} />
                </div>
              </div>
            </div>

            {/* SECCIÓN: PAX */}
            <div className="bg-gradient-to-br from-gray-50 to-gray-100 p-5 rounded-2xl border border-gray-100 shadow-inner">
              <h3 className="text-sm font-black text-tropical-green uppercase tracking-widest mb-4 flex items-center gap-2 justify-center">
                <span className="text-xl">👨‍👩‍👧‍👦</span> 4. Pasajeros
              </h3>
              <div className="grid grid-cols-3 gap-3">
                <div className="flex flex-col items-center">
                  <label className="block text-[10px] md:text-xs font-bold text-gray-500 mb-1">ADULTOS</label>
                  <input type="number" min="1" required value={paxAdultos} onChange={(e) => setPaxAdultos(Number(e.target.value))} className={`${inputClass} text-center font-bold text-lg p-2`} />
                </div>
                <div className="flex flex-col items-center">
                  <label className="block text-[10px] md:text-xs font-bold text-gray-500 mb-1">MENORES</label>
                  <input type="number" min="0" required value={paxMenores} onChange={(e) => setPaxMenores(Number(e.target.value))} className={`${inputClass} text-center font-bold text-lg p-2`} />
                </div>
                <div className="flex flex-col items-center">
                  <label className="block text-[10px] md:text-xs font-bold text-gray-500 mb-1">INFANTES</label>
                  <input type="number" min="0" required value={paxInfantes} onChange={(e) => setPaxInfantes(Number(e.target.value))} className={`${inputClass} text-center font-bold text-lg p-2`} />
                </div>
              </div>
            </div>

            {/* SECCIÓN: COBRO */}
            <div className="bg-tropical-yellow/10 p-5 rounded-2xl border border-tropical-yellow/30 relative">
              <h3 className="text-sm font-black text-yellow-700 uppercase tracking-widest mb-4 flex items-center gap-2">
                <span className="text-xl">💵</span> 5. Cobro
              </h3>
              
              <div className="flex justify-between items-end mb-2">
                <label className="font-semibold text-sm uppercase tracking-wider text-yellow-800">Monto Total (MXN)</label>
                <button 
                  type="button" 
                  onClick={() => setIsConversorOpen(true)}
                  className="text-xs font-bold bg-tropical-yellow text-yellow-800 hover:bg-yellow-400 px-3 py-1.5 rounded-full transition-all flex items-center gap-1 shadow-sm active:scale-95"
                >
                  💱 Abrir Conversor
                </button>
              </div>
              <div className="relative mb-4">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 font-bold text-xl">$</span>
                <input type="number" step="0.01" required value={montoTotal} onChange={(e) => setMontoTotal(e.target.value !== '' ? Number(e.target.value) : '')} placeholder="0.00" className={`${inputClass} pl-10 text-2xl font-black border-yellow-200 focus:border-yellow-400 focus:ring-yellow-400/20`} />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="font-semibold text-[0.75rem] md:text-sm uppercase tracking-wider text-emerald-700 mb-2 block">Anticipo (Depositado)</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-emerald-600 font-bold">$</span>
                    <input type="number" step="0.01" value={montoDeposito} onChange={(e) => setMontoDeposito(e.target.value !== '' ? Number(e.target.value) : '')} placeholder="0.00" className={`${inputClass} pl-8 text-lg font-bold border-emerald-200 focus:border-emerald-400 bg-emerald-50 text-emerald-800`} />
                  </div>
                </div>
                <div className="bg-white/60 p-3 rounded-xl border border-rose-100 flex flex-col justify-center items-center">
                  <label className="font-semibold text-[0.75rem] uppercase tracking-wider text-rose-500 mb-1">Saldo Pendiente</label>
                  <span className="text-xl font-black text-rose-600">
                    ${Math.max(0, (Number(montoTotal) || 0) - (Number(montoDeposito) || 0)).toFixed(2)}
                  </span>
                </div>
              </div>
            </div>

            {/* BOTÓN Y ALERTAS */}
            {mensajeStatus.tipo && (
              <div className={`p-4 md:p-5 rounded-2xl text-center font-bold text-sm md:text-base animate-in fade-in slide-in-from-bottom-2 duration-300 ${
                mensajeStatus.tipo === 'exito' ? 'bg-emerald-50 border border-emerald-200 text-emerald-700 shadow-sm' : 'bg-rose-50 border border-rose-200 text-rose-700 shadow-sm'
              }`}>
                {mensajeStatus.texto}
              </div>
            )}

            <button 
              type="submit" 
              disabled={loading}
              className={`text-white p-4 md:p-5 rounded-2xl text-lg font-black w-full transition-all duration-300 active:scale-[0.98] mt-2 shadow-lg ${
                loading ? 'bg-gray-400 cursor-not-allowed shadow-none' : 'bg-tropical-coral hover:bg-[#ff8f87] hover:-translate-y-1 hover:shadow-xl hover:shadow-tropical-coral/30'
              }`}
            >
              {loading ? 'Procesando Venta...' : '💳 FINALIZAR REGISTRO'}
            </button>
          </form>
        </div>

        {/* MODAL DEL CONVERSOR */}
        {isConversorOpen && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
            <div className="bg-white p-6 md:p-8 rounded-3xl shadow-2xl border-t-[8px] border-tropical-yellow w-full max-w-[400px] relative animate-in zoom-in-95 duration-300">
              
              <button 
                onClick={() => setIsConversorOpen(false)}
                className="absolute top-4 right-4 text-gray-400 hover:text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-full w-8 h-8 flex items-center justify-center transition-colors font-bold"
              >
                ✕
              </button>

              <div className="text-center mb-6">
                <h3 className="text-tropical-text text-2xl font-black m-0">💱 Conversor</h3>
                <p className="text-gray-400 text-xs mt-1">Calcula el cobro exacto en Pesos</p>
              </div>
              
              <div className="mb-4">
                <label className={labelClass}>Divisa Recibida</label>
                <select className={inputClass}>
                  <option value="USD">Dólar Americano (USD)</option>
                  <option value="CAD">Dólar Canadiense (CAD)</option>
                </select>
              </div>

              <div className="mb-4">
                <label className={labelClass}>Monto Entregado</label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 font-bold">$</span>
                  <input type="number" value={calcMonto} onChange={(e) => setCalcMonto(e.target.value !== '' ? Number(e.target.value) : '')} placeholder="Ej: 100" className={`${inputClass} pl-9 font-bold`} />
                </div>
              </div>

              <div className="mb-6">
                <label className={labelClass}>Tipo de Cambio del Día</label>
                <input type="number" step="0.01" value={calcTipoCambio} onChange={(e) => setCalcTipoCambio(Number(e.target.value))} className={inputClass} />
              </div>

              <div className="bg-gradient-to-br from-tropical-yellow/20 to-tropical-yellow/40 p-5 rounded-2xl text-center border border-tropical-yellow/30 shadow-inner">
                <span className="block text-xs font-bold text-yellow-800 uppercase tracking-widest mb-1">Monto a Cobrar</span>
                <span className="block font-black text-4xl text-tropical-text">
                  ${calcMonto && calcTipoCambio ? (Number(calcMonto) * calcTipoCambio).toFixed(2) : '0.00'}
                </span>
                <span className="text-sm font-bold text-yellow-700">MXN</span>
              </div>
              
              <button 
                onClick={() => {
                  if (calcMonto && calcTipoCambio) {
                    setMontoTotal(Number((Number(calcMonto) * calcTipoCambio).toFixed(2)));
                  }
                  setIsConversorOpen(false);
                }}
                className="mt-6 w-full bg-tropical-text text-white font-bold p-4 rounded-xl hover:bg-gray-800 transition-colors active:scale-95"
              >
                Aplicar al Formulario
              </button>
            </div>
          </div>
        )}

      </div>
    </main>
  );
}