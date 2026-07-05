'use client';

import { useParams } from 'next/navigation';
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/lib/hooks/useAuth';


// ─── TIPOS ───────────────────────────────────────────────────────────────────
type EstadoReserva = 'PENDIENTE' | 'EN_PROCESO' | 'COMPLETADO' | 'CANCELADO';
type EstadoPago = 'PENDIENTE' | 'PAGADO';

interface Reserva {
  id: string;
  folio_fisico: string | null;
  cliente_nombre: string;
  cliente_telefono: string | null;
  cliente_email: string;
  tour_nombre: string;
  fecha_servicio: string;
  hora_salida: string | null;
  ubicacion_pickup: string | null;
  pax_adultos: number;
  pax_menores: number;
  pax_infantes: number;
  estado: EstadoReserva;
  contador_escaneos: number;
  creado_en: string;
  monto_total: number | null;
  monto_deposito: number | null;
  monto_saldo: number | null;
  status_pago: EstadoPago | null;
}

// ─── CONSTANTES ───────────────────────────────────────────────────────────────
const API_BASE = 'http://localhost:8001/api/v1';
const HEADERS = { 'Content-Type': 'application/json', 'X-API-Key': 'SST_FRONT_ACCESS_SECRET_2026' };
const TOURS = ['Xcaret Plus', 'Chichén Itzá', 'Tulum & Cobá', 'Ruta de Cenotes', 'Catamarán Isla Mujeres', 'Cozumel Snorkel'];

// ─── HELPERS ─────────────────────────────────────────────────────────────────
const estadoBadge: Record<EstadoReserva, { label: string; cls: string }> = {
  PENDIENTE:   { label: 'Pendiente',   cls: 'bg-yellow-100 text-yellow-800 border border-yellow-200' },
  EN_PROCESO:  { label: 'En proceso',  cls: 'bg-blue-100 text-blue-800 border border-blue-200' },
  COMPLETADO:  { label: 'Completado',  cls: 'bg-green-100 text-green-800 border border-green-200' },
  CANCELADO:   { label: 'Cancelado',   cls: 'bg-red-100 text-red-800 border border-red-200' },
};
const pagoBadge: Record<EstadoPago, { label: string; cls: string }> = {
  PENDIENTE: { label: '⏳ Saldo pendiente', cls: 'bg-orange-100 text-orange-800 border border-orange-200' },
  PAGADO:    { label: '✅ Pagado',          cls: 'bg-emerald-100 text-emerald-800 border border-emerald-200' },
};
const fmt = (n: number | null | undefined) =>
  n != null ? `$${n.toLocaleString('es-MX', { minimumFractionDigits: 2 })}` : '—';

// ─── COMPONENTE PRINCIPAL ────────────────────────────────────────────────────
export default function DashboardPage() {
  const { id_empresa } = useParams<{ id_empresa: string }>();
  const { nombre, rol, signOut } = useAuth();

  const [reservas, setReservas]     = useState<Reserva[]>([]);
  const [loading, setLoading]       = useState(true);
  const [filtroEstado, setFiltroEstado] = useState<'TODAS' | EstadoReserva | 'SALDO'>('TODAS');
  const [busqueda, setBusqueda]     = useState('');

  // Modales
  const [modalEditar, setModalEditar]   = useState<Reserva | null>(null);
  const [modalPagar, setModalPagar]     = useState<Reserva | null>(null);
  const [montoPagar, setMontoPagar]     = useState('');
  const [toast, setToast]               = useState<{ msg: string; ok: boolean } | null>(null);
  const [guardando, setGuardando]       = useState(false);

  // ── FETCH ─────────────────────────────────────────────────────────────────
  const fetchReservas = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/reservas/?id_empresa=${id_empresa}`, { headers: HEADERS });
      if (res.ok) setReservas(await res.json());
    } finally {
      setLoading(false);
    }
  }, [id_empresa]);

  useEffect(() => { fetchReservas(); }, [fetchReservas]);

  const showToast = (msg: string, ok = true) => {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 3500);
  };

  // ── FILTROS ───────────────────────────────────────────────────────────────
  const reservasFiltradas = reservas.filter(r => {
    const matchEstado =
      filtroEstado === 'TODAS' ? true :
      filtroEstado === 'SALDO' ? r.status_pago === 'PENDIENTE' :
      r.estado === filtroEstado;
    const q = busqueda.toLowerCase();
    const matchBusq = !q || r.cliente_nombre.toLowerCase().includes(q) ||
      r.tour_nombre.toLowerCase().includes(q) ||
      (r.folio_fisico ?? '').toLowerCase().includes(q) ||
      (r.cliente_email ?? '').toLowerCase().includes(q);
    return matchEstado && matchBusq;
  });

  // ── KPIs ──────────────────────────────────────────────────────────────────
  const totalSaldo  = reservas.reduce((a, r) => a + (r.monto_saldo ?? 0), 0);
  const totalVentas = reservas.reduce((a, r) => a + (r.monto_total ?? 0), 0);
  const conSaldo    = reservas.filter(r => r.status_pago === 'PENDIENTE').length;
  const pagadas     = reservas.filter(r => r.status_pago === 'PAGADO').length;

  // ── ACCIONES ──────────────────────────────────────────────────────────────
  const reenviarQR = async (r: Reserva) => {
    setGuardando(true);
    try {
      const res = await fetch(`${API_BASE}/reservas/${r.id}/reenviar-qr?id_empresa=${id_empresa}`, {
        method: 'POST', headers: HEADERS
      });
      const data = await res.json();
      showToast(res.ok ? `📧 QR enviado a ${r.cliente_email}` : data.detail, res.ok);
    } finally { setGuardando(false); }
  };

  const cancelarReserva = async (r: Reserva) => {
    if (!confirm(`¿Cancelar la reserva de ${r.cliente_nombre}?`)) return;
    setGuardando(true);
    try {
      const res = await fetch(`${API_BASE}/reservas/${r.id}/cancelar`, { method: 'PATCH', headers: HEADERS });
      showToast(res.ok ? 'Reserva cancelada' : 'Error al cancelar', res.ok);
      if (res.ok) fetchReservas();
    } finally { setGuardando(false); }
  };

  const registrarPago = async () => {
    if (!modalPagar || !montoPagar) return;
    const monto = parseFloat(montoPagar);
    if (isNaN(monto) || monto <= 0) return showToast('Monto inválido', false);
    setGuardando(true);
    try {
      const res = await fetch(`${API_BASE}/reservas/${modalPagar.id}/registrar-abono?monto_abono=${monto}`, {
        method: 'PATCH', headers: HEADERS
      });
      const data = await res.json();
      if (res.ok) {
        showToast(`✅ Pago de ${fmt(monto)} registrado`);
        setModalPagar(null); setMontoPagar('');
        fetchReservas();
      } else { showToast(data.detail || 'Error', false); }
    } finally { setGuardando(false); }
  };

  // Edición
  const [editForm, setEditForm] = useState<Partial<Reserva>>({});
  const abrirEditar = (r: Reserva) => { setModalEditar(r); setEditForm({ ...r }); };

  const guardarEdicion = async () => {
    if (!modalEditar) return;
    setGuardando(true);
    const payload: Record<string, unknown> = {};
    const campos: (keyof Reserva)[] = ['cliente_nombre','cliente_email','cliente_telefono','tour_nombre','fecha_servicio','hora_salida','ubicacion_pickup','pax_adultos','pax_menores','pax_infantes','folio_fisico','monto_total'];
    campos.forEach(c => { if (editForm[c] !== modalEditar[c]) payload[c] = editForm[c]; });

    if (Object.keys(payload).length === 0) { setModalEditar(null); return; }
    try {
      const res = await fetch(`${API_BASE}/reservas/${modalEditar.id}/editar?id_empresa=${id_empresa}`, {
        method: 'PATCH', headers: HEADERS, body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) { showToast('✅ Reserva actualizada'); setModalEditar(null); fetchReservas(); }
      else { showToast(data.detail || 'Error al guardar', false); }
    } finally { setGuardando(false); }
  };

  // ── INPUT CLASS ───────────────────────────────────────────────────────────
  const inp = 'w-full p-3 border border-gray-200 rounded-xl bg-gray-50 focus:border-emerald-400 focus:bg-white outline-none text-[15px] text-gray-800';
  const lbl = 'block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1';

  // ── RENDER ────────────────────────────────────────────────────────────────
  return (
    <main className="min-h-screen bg-gray-50 font-sans">

      {/* TOAST */}
      {toast && (
        <div className={`fixed top-4 right-4 z-[999] px-5 py-3 rounded-2xl shadow-xl font-bold text-sm animate-in slide-in-from-top-2 duration-300 ${toast.ok ? 'bg-emerald-500 text-white' : 'bg-red-500 text-white'}`}>
          {toast.msg}
        </div>
      )}

      {/* HEADER */}
      <div className="bg-white border-b border-gray-100 shadow-sm px-4 py-5 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div>
            <p className="text-xs font-bold tracking-widest text-emerald-600 uppercase">{id_empresa}</p>
            <h1 className="text-2xl font-black text-gray-800">📋 Dashboard de Reservas</h1>
          </div>
          <div className="flex gap-2 items-center flex-wrap">
            {/* Chip del usuario activo */}
            {nombre && (
              <div className="flex items-center gap-2 bg-gray-100 px-3 py-2 rounded-xl">
                <div className="w-7 h-7 bg-emerald-500 rounded-full flex items-center justify-center text-white text-xs font-black">
                  {nombre.charAt(0).toUpperCase()}
                </div>
                <div className="text-xs leading-tight">
                  <div className="font-bold text-gray-800">{nombre}</div>
                  <div className="text-gray-400 capitalize">{rol}</div>
                </div>
              </div>
            )}
            <a href={`/${id_empresa}/nueva-reserva`}
               className="bg-emerald-500 hover:bg-emerald-600 text-white font-bold px-4 py-2.5 rounded-xl text-sm transition-all active:scale-95 shadow-sm">
              ＋ Nueva Venta
            </a>
            <button onClick={fetchReservas} className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold px-4 py-2.5 rounded-xl text-sm transition-all active:scale-95">
              🔄
            </button>
            <button onClick={signOut} className="bg-red-50 hover:bg-red-100 text-red-600 font-bold px-4 py-2.5 rounded-xl text-sm transition-all active:scale-95">
              Salir
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6 flex flex-col gap-6">

        {/* KPIs */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: 'Total Reservas', value: reservas.length, icon: '📋', color: 'border-blue-200 bg-blue-50' },
            { label: 'Total Vendido',  value: fmt(totalVentas), icon: '💰', color: 'border-emerald-200 bg-emerald-50' },
            { label: 'Con Saldo',      value: conSaldo, icon: '⏳', color: 'border-orange-200 bg-orange-50' },
            { label: 'Saldo Total',    value: fmt(totalSaldo), icon: '⚠️', color: 'border-red-200 bg-red-50' },
          ].map(k => (
            <div key={k.label} className={`rounded-2xl border p-4 ${k.color}`}>
              <div className="text-2xl mb-1">{k.icon}</div>
              <div className="text-xl font-black text-gray-800">{k.value}</div>
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{k.label}</div>
            </div>
          ))}
        </div>

        {/* FILTROS + BÚSQUEDA */}
        <div className="flex flex-col md:flex-row gap-3">
          <input
            value={busqueda} onChange={e => setBusqueda(e.target.value)}
            placeholder="🔍 Buscar por cliente, tour, folio..."
            className="flex-1 p-3 border border-gray-200 rounded-xl bg-white text-[15px] outline-none focus:border-emerald-400"
          />
          <div className="flex gap-2 flex-wrap">
            {(['TODAS','PENDIENTE','COMPLETADO','CANCELADO','SALDO'] as const).map(f => (
              <button key={f}
                onClick={() => setFiltroEstado(f)}
                className={`px-3 py-2 rounded-xl text-xs font-bold border transition-all ${filtroEstado === f ? 'bg-gray-800 text-white border-gray-800' : 'bg-white text-gray-600 border-gray-200 hover:border-gray-400'}`}>
                {f === 'SALDO' ? '⏳ Saldo Pendiente' : f === 'TODAS' ? '📋 Todas' : f === 'PENDIENTE' ? '🟡 Activas' : f === 'COMPLETADO' ? '✅ Completadas' : '🔴 Canceladas'}
              </button>
            ))}
          </div>
        </div>

        {/* LISTA */}
        {loading ? (
          <div className="text-center py-20 text-gray-400 font-semibold">Cargando reservas...</div>
        ) : reservasFiltradas.length === 0 ? (
          <div className="text-center py-20 text-gray-300 text-5xl">📭<p className="text-base text-gray-400 mt-3 font-semibold">No hay reservas con ese filtro</p></div>
        ) : (
          <div className="flex flex-col gap-3">
            {reservasFiltradas.map(r => (
              <div key={r.id} className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden hover:shadow-md transition-shadow">
                
                {/* Barra superior de color según pago */}
                <div className={`h-1.5 w-full ${r.status_pago === 'PAGADO' ? 'bg-emerald-400' : r.estado === 'CANCELADO' ? 'bg-red-400' : 'bg-orange-400'}`} />

                <div className="p-4 md:p-5">
                  <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
                    
                    {/* INFO PRINCIPAL */}
                    <div className="flex-1">
                      <div className="flex flex-wrap items-center gap-2 mb-2">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${estadoBadge[r.estado].cls}`}>
                          {estadoBadge[r.estado].label}
                        </span>
                        {r.status_pago && (
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${pagoBadge[r.status_pago].cls}`}>
                            {pagoBadge[r.status_pago].label}
                          </span>
                        )}
                        {r.folio_fisico && r.folio_fisico !== 'N/A' && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border border-gray-200">
                            📄 {r.folio_fisico}
                          </span>
                        )}
                      </div>

                      <h3 className="font-black text-gray-800 text-base md:text-lg">{r.cliente_nombre}</h3>
                      <p className="text-sm text-gray-500">{r.cliente_email} · {r.cliente_telefono}</p>
                      
                      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-sm text-gray-600">
                        <span>🌴 <b>{r.tour_nombre}</b></span>
                        <span>📅 {r.fecha_servicio}</span>
                        {r.hora_salida && <span>⏰ {r.hora_salida}</span>}
                        {r.ubicacion_pickup && r.ubicacion_pickup !== 'N/A' && <span>📍 {r.ubicacion_pickup}</span>}
                        <span>👥 {(r.pax_adultos ?? 0) + (r.pax_menores ?? 0) + (r.pax_infantes ?? 0)} pax</span>
                        <span>🔍 {r.contador_escaneos} escaneos</span>
                      </div>
                    </div>

                    {/* FINANZAS */}
                    <div className="flex flex-row md:flex-col gap-3 md:items-end text-right">
                      <div className="bg-gray-50 rounded-xl p-3 text-left md:text-right min-w-[140px]">
                        <div className="text-[10px] text-gray-400 uppercase font-bold">Total</div>
                        <div className="text-lg font-black text-gray-800">{fmt(r.monto_total)}</div>
                        <div className="text-xs text-gray-500">Anticipo: {fmt(r.monto_deposito)}</div>
                        {(r.monto_saldo ?? 0) > 0 && (
                          <div className="text-xs font-bold text-orange-600">Saldo: {fmt(r.monto_saldo)}</div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* ACCIONES */}
                  <div className="flex flex-wrap gap-2 mt-4 pt-3 border-t border-gray-50">
                    <button onClick={() => abrirEditar(r)}
                      className="flex-1 md:flex-none px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold rounded-xl text-xs transition-all active:scale-95">
                      ✏️ Editar
                    </button>
                    {(r.monto_saldo ?? 0) > 0 && r.estado !== 'CANCELADO' && (
                      <button onClick={() => { setModalPagar(r); setMontoPagar(String(r.monto_saldo ?? '')); }}
                        className="flex-1 md:flex-none px-3 py-2 bg-emerald-500 hover:bg-emerald-600 text-white font-bold rounded-xl text-xs transition-all active:scale-95 shadow-sm">
                        💵 Registrar Pago
                      </button>
                    )}
                    <button onClick={() => reenviarQR(r)} disabled={guardando}
                      className="flex-1 md:flex-none px-3 py-2 bg-blue-100 hover:bg-blue-200 text-blue-800 font-bold rounded-xl text-xs transition-all active:scale-95">
                      📧 Reenviar QR
                    </button>
                    {r.estado !== 'CANCELADO' && (
                      <button onClick={() => cancelarReserva(r)} disabled={guardando}
                        className="flex-1 md:flex-none px-3 py-2 bg-red-50 hover:bg-red-100 text-red-700 font-bold rounded-xl text-xs transition-all active:scale-95">
                        🗑️ Cancelar
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ─── MODAL: REGISTRAR PAGO ─────────────────────────────────────────── */}
      {modalPagar && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setModalPagar(null)}>
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-[420px] overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="bg-emerald-500 p-6 text-white">
              <h2 className="text-xl font-black">💵 Registrar Pago</h2>
              <p className="text-emerald-100 text-sm mt-1">{modalPagar.cliente_nombre}</p>
            </div>
            <div className="p-6 flex flex-col gap-4">
              <div className="bg-orange-50 border border-orange-200 rounded-2xl p-4 text-center">
                <div className="text-xs font-bold text-orange-600 uppercase tracking-wider">Saldo Pendiente</div>
                <div className="text-3xl font-black text-orange-700">{fmt(modalPagar.monto_saldo)}</div>
              </div>
              <div>
                <label className={lbl}>Monto a Registrar (MXN)</label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 font-bold text-lg">$</span>
                  <input type="number" step="0.01" value={montoPagar} onChange={e => setMontoPagar(e.target.value)}
                    className={`${inp} pl-9 text-2xl font-black`} placeholder="0.00" />
                </div>
              </div>
              <div className="flex gap-3">
                <button onClick={() => setModalPagar(null)} className="flex-1 p-3 bg-gray-100 text-gray-700 font-bold rounded-xl">Cancelar</button>
                <button onClick={registrarPago} disabled={guardando}
                  className="flex-1 p-3 bg-emerald-500 hover:bg-emerald-600 text-white font-black rounded-xl transition-all disabled:opacity-50">
                  {guardando ? 'Guardando...' : '✅ Confirmar Pago'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ─── MODAL: EDITAR RESERVA ─────────────────────────────────────────── */}
      {modalEditar && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 overflow-y-auto flex items-start justify-center p-4 pt-8" onClick={() => setModalEditar(null)}>
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-[540px] overflow-hidden mb-8" onClick={e => e.stopPropagation()}>
            <div className="bg-gray-800 p-6 text-white flex justify-between items-start">
              <div>
                <h2 className="text-xl font-black">✏️ Editar Reserva</h2>
                <p className="text-gray-400 text-sm mt-1">{modalEditar.folio_fisico ?? modalEditar.id.slice(0,8)}</p>
              </div>
              <button onClick={() => setModalEditar(null)} className="text-gray-400 hover:text-white bg-gray-700 rounded-full w-8 h-8 flex items-center justify-center font-bold">✕</button>
            </div>

            <div className="p-6 flex flex-col gap-5 overflow-y-auto max-h-[70vh]">

              {/* Sección: cliente */}
              <div className="bg-gray-50 rounded-2xl p-4 flex flex-col gap-3">
                <h3 className="text-xs font-black text-gray-500 uppercase tracking-widest">🧳 Datos del Cliente</h3>
                <div>
                  <label className={lbl}>Nombre</label>
                  <input className={inp} value={editForm.cliente_nombre ?? ''} onChange={e => setEditForm(f => ({...f, cliente_nombre: e.target.value}))} />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className={lbl}>Email</label>
                    <input type="email" className={inp} value={editForm.cliente_email ?? ''} onChange={e => setEditForm(f => ({...f, cliente_email: e.target.value}))} />
                  </div>
                  <div>
                    <label className={lbl}>Teléfono</label>
                    <input type="tel" className={inp} value={editForm.cliente_telefono ?? ''} onChange={e => setEditForm(f => ({...f, cliente_telefono: e.target.value}))} />
                  </div>
                </div>
              </div>

              {/* Sección: tour */}
              <div className="bg-gray-50 rounded-2xl p-4 flex flex-col gap-3">
                <h3 className="text-xs font-black text-gray-500 uppercase tracking-widest">🌴 Servicio</h3>
                <div>
                  <label className={lbl}>Tour</label>
                  <select className={inp} value={editForm.tour_nombre ?? ''} onChange={e => setEditForm(f => ({...f, tour_nombre: e.target.value}))}>
                    {TOURS.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className={lbl}>Fecha</label>
                    <input type="date" className={inp} value={editForm.fecha_servicio ?? ''} onChange={e => setEditForm(f => ({...f, fecha_servicio: e.target.value}))} />
                  </div>
                  <div>
                    <label className={lbl}>Hora</label>
                    <input className={inp} value={editForm.hora_salida ?? ''} onChange={e => setEditForm(f => ({...f, hora_salida: e.target.value}))} />
                  </div>
                </div>
                <div>
                  <label className={lbl}>Punto de encuentro</label>
                  <input className={inp} value={editForm.ubicacion_pickup ?? ''} onChange={e => setEditForm(f => ({...f, ubicacion_pickup: e.target.value}))} />
                </div>
                <div className="grid grid-cols-3 gap-3">
                  {(['pax_adultos','pax_menores','pax_infantes'] as const).map(k => (
                    <div key={k}>
                      <label className={lbl}>{k.replace('pax_','').toUpperCase()}</label>
                      <input type="number" min="0" className={`${inp} text-center font-bold`}
                        value={editForm[k] ?? 0} onChange={e => setEditForm(f => ({...f, [k]: Number(e.target.value)}))} />
                    </div>
                  ))}
                </div>
              </div>

              {/* Sección: finanzas */}
              <div className="bg-yellow-50 rounded-2xl p-4 flex flex-col gap-3 border border-yellow-100">
                <h3 className="text-xs font-black text-yellow-700 uppercase tracking-widest">💵 Finanzas</h3>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className={lbl}>Folio Físico</label>
                    <input className={inp} value={editForm.folio_fisico ?? ''} onChange={e => setEditForm(f => ({...f, folio_fisico: e.target.value}))} />
                  </div>
                  <div>
                    <label className={lbl}>Monto Total (MXN)</label>
                    <input type="number" step="0.01" className={`${inp} font-bold`}
                      value={editForm.monto_total ?? ''} onChange={e => setEditForm(f => ({...f, monto_total: Number(e.target.value)}))} />
                  </div>
                </div>
              </div>

              <div className="flex gap-3">
                <button onClick={() => setModalEditar(null)} className="flex-1 p-3 bg-gray-100 text-gray-700 font-bold rounded-xl">Cancelar</button>
                <button onClick={guardarEdicion} disabled={guardando}
                  className="flex-1 p-3 bg-gray-800 hover:bg-gray-900 text-white font-black rounded-xl transition-all disabled:opacity-50">
                  {guardando ? 'Guardando...' : '💾 Guardar Cambios'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

    </main>
  );
}
