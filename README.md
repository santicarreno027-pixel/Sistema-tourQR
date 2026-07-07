# 🏝️ Sistema-Tour

<div align="center">

**Plataforma SaaS de gestión de reservas para tours y excursiones**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16.0.0-000000?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![Supabase](https://img.shields.io/badge/Supabase-3.0.0-3ECF8E?style=for-the-badge&logo=supabase)](https://supabase.com/)
[![n8n](https://img.shields.io/badge/n8n-1.0.0-EA4B71?style=for-the-badge&logo=n8n)](https://n8n.io/)
[![License](https://img.shields.io/badge/License-MIT-1E90FF?style=for-the-badge)](LICENSE)

</div>

---

## 📋 Tabla de Contenidos

- [Descripción General](#-descripción-general)
- [Arquitectura](#-arquitectura)
- [Características Principales](#-características-principales)
- [Flujo de Trabajo](#-flujo-de-trabajo)
- [Stack Tecnológico](#-stack-tecnológico)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación Local](#-instalación-local)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [APIs Principales](#-apis-principales)
- [Despliegue a Producción](#-despliegue-a-producción)
- [Contribución](#-contribución)
- [Licencia](#-licencia)
- [Soporte](#-soporte)

---

## 🎯 Descripción General

**Sistema-Tour** es una plataforma SaaS diseñada para agencias de viajes y operadores turísticos que necesitan digitalizar su proceso de venta de excursiones. Permite a vendedores crear reservas, generar códigos QR únicos por cada ticket, y validarlos en tiempo real desde el dispositivo del guía turístico.

El sistema está construido con un enfoque **multi-tenant**, permitiendo que múltiples agencias operen desde la misma base de datos con aislamiento completo de datos.

### 🎥 Demo Rápida

| Característica | Estado |
|----------------|--------|
| ✅ Creación de reservas | Funcional |
| ✅ Generación de QR | Automática |
| ✅ Envío de vouchers | Por email |
| ✅ Escaneo QR | En tiempo real |
| ✅ Cobro en campo | En el punto de acceso |
| ✅ Gestión de vendedores | CRUD completo |
| ✅ PWA/Offline | En desarrollo |

---

## 🏗️ Arquitectura
┌─────────────────────────────────────────────────────────────────────┐
│ FRONTEND (Next.js) │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│ │ Login │ │ Nueva Reserva│ │ Dashboard │ │
│ └──────────────┘ └──────────────┘ └──────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────┐
│ BACKEND (FastAPI + Supabase) │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│ │ Reservas │ │ Tickets │ │ Vendedores │ │
│ └──────────────┘ └──────────────┘ └──────────────┘ │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│ │ Webhooks │ │ Auth JWT │ │ Multi-tenant │ │
│ └──────────────┘ └──────────────┘ └──────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
│
┌───────────────┼───────────────┐
▼ ▼ ▼
┌───────────┐ ┌───────────┐ ┌───────────┐
│ Supabase │ │ n8n │ │ SendGrid │
│ PostgreSQL│ │Workflows │ │ Email │
└───────────┘ └───────────┘ └───────────┘

---

## ✨ Características Principales

### Para Vendedores
- **Formulario intuitivo** de creación de reservas
- **Desglose de PAX** (adultos, menores, infantes)
- **Cálculo automático** de saldo pendiente
- **Conversor de divisa visual** en tiempo real

### Para Guías Turísticos
- **Escaneo QR** desde cualquier dispositivo móvil
- **Validación automática** de vigencia (ventana de 4 horas)
- **Pantallas de color** según estado:
  - 🟢 **Verde:** Acceso permitido
  - 🟠 **Naranja:** Saldo pendiente + formulario de cobro
  - 🟡 **Amarillo:** QR inactivo (fuera de ventana)
  - 🔴 **Rojo:** Acceso denegado (cancelado/vencido)

### Para Administradores
- **Dashboard** con visión global de reservas
- **CRUD completo** de vendedores
- **Reportes por vendedor** (ventas y comisiones)
- **Auditoría nocturna** de tours pasados

### Para Clientes
- **Voucher digital** con QR único por correo electrónico
- **Detalles del tour** (fecha, hora, punto de encuentro)
- **Estado de pago** actualizado en tiempo real

---

## 🔄 Flujo de Trabajo

<img width="694" height="260" alt="sistema QR" src="https://github.com/user-attachments/assets/744a4458-f6bb-43c9-8143-9cf71a5b3db0" />

El flujo se principal se activa con el disparo de una reserva pasando por los filtros para recolectar la informacion necesaria , luego por un sistema logico de compuerta que dirije la infomacion hacia la generacion de codigo qr pegandole al endpoint correspondiente si fue abonada en su totalidad y envia un HTML con su codigo QR y a disfrutar de su viaje. De lo contrario ,se notifica al cliente , que su reserva fue creada exitosamente y que debe abonar x para obtener su codigo QR
    V->>F: Crea reserva
    F->>B: POST /api/v1/reservas
    B->>B: Valida & guarda
    B->>N: Webhook (reserva creada)
    N->>N: Genera QR
    N->>E: Envía voucher
    E->>V: Email confirmación
    
    G->>B: Escanea QR
    B->>B: Valida ticket
    alt Pago completo
        B->>G: Pantalla 🟢 VERDE
    else Saldo pendiente
        B->>G: Pantalla 🟠 NARANJA + Cobro
    else Inactivo
        B->>G: Pantalla 🟡 AMARILLA
    else Cancelado
        B->>G: Pantalla 🔴 ROJA
    end
    🛠️ Stack Tecnológico
    
Backend:
Tecnología	Versión	Propósito
FastAPI	0.115.0	API RESTful
SQLAlchemy	2.0.0	ORM y migraciones
Supabase	3.0.0	Auth & PostgreSQL
PyJWT	2.8.0	Validación JWT (ES256)
httpx	0.27.0	Cliente HTTP asíncrono
SlowAPI	0.1.5	Rate limiting
Frontend
Tecnología	Versión	Propósito
Next.js	16.0.0	Framework React
Tailwind CSS	4.0.0	Estilos y diseño
Supabase SSR	3.0.0	Auth & sesiones
TypeScript	5.0.0	Tipado estático
Workflows & Notificaciones
Tecnología	Propósito
n8n	Orquestación de workflows (QR + Email)
SendGrid	Envío de emails transaccionales
QuickChart	Generación de códigos QR
Infraestructura
Tecnología	Propósito
Docker	Contenedores
Supabase	Base de datos serverless
GitHub	Control de versiones
Vercel	(Planeado) Hosting frontend

📋 Requisitos Previos
Python 3.12 o superior

Node.js 18.x o superior

npm o yarn instalado

Docker (opcional, para n8n)

Cuenta en Supabase (gratuita)

Cuenta en SendGrid (gratuita, 100 emails/día)

🔧 Instalación Local
Clonar el Repositorio
bash
git clone https://github.com/santicarreno027-pixel/Sistema-tourQR.git
cd Sistema-tourQR
Backend (FastAPI)
bash
# 1. Crear y activar entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# 4. Iniciar el servidor
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
Frontend (Next.js)
bash
# 1. Navegar al frontend
cd sistema-tour-front

# 2. Instalar dependencias
npm install

# 3. Configurar variables de entorno
cp .env.example .env.local
# Editar .env.local con tus valores

# 4. Iniciar en modo desarrollo
npm run dev
n8n (Workflows)
bash
# Opción 1: Docker (recomendado)
docker run -d --name n8n -p 5678:5678 \
  --add-host host.docker.internal:host-gateway \
  n8nio/n8n

# Opción 2: n8n.cloud (más fácil)
# 1. Crear cuenta en n8n.cloud (gratis)
# 2. Importar workflow desde el archivo
# 3. Copiar webhook URL
# 4. Actualizar .env del backend
⚙️ Configuración
Variables de Entorno (.env)
bash
# Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=tu_service_role_key

# Seguridad
FRONTEND_SECRET=tu_frontend_secret
API_KEY=tu_api_key_backend

# n8n
N8N_WEBHOOK_URL=http://localhost:5678/webhook/formulario
N8N_WEBHOOK_UPDATE_URL=http://localhost:5678/webhook/actualizacion
N8N_HEADER_NAME=asdf
N8N_HEADER_PASSWORD=1234

# SendGrid (opcional, para emails robustos)
SENDGRID_API_KEY=tu_api_key
Frontend (.env.local)
bash
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_SUPABASE_URL=https://tu-proyecto.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=tu_anon_key
NEXT_PUBLIC_API_KEY=SST_FRONT_ACCESS_SECRET
🚀 Uso
Crear una Reserva
bash
curl -X POST http://localhost:8001/api/v1/reservas \
  -H "X-API-Key: SST_FRONT_ACCESS_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "cliente_nombre": "Juan Pérez",
    "cliente_email": "juan@email.com",
    "cliente_telefono": "9841234567",
    "tour_nombre": "Cozumel Catamaran",
    "fecha_servicio": "2026-07-15",
    "hora_salida": "10:00 AM",
    "ubicacion_pickup": "El Ancla",
    "pax_adultos": 2,
    "pax_menores": 0,
    "pax_infantes": 0,
    "vendedor_nombre": "Gonzalo",
    "monto_total": 150.00,
    "monto_deposito": 150.00,
    "id_empresa": "tours-playa-aventura"
  }'
Escanear un QR
bash
# Desde el navegador o celular
http://localhost:8001/api/v1/tickets/scan/{ticket_id}

# Responde con una página HTML de color según el estado
Gestionar Vendedores (Admin)
bash
# Listar vendedores
curl -X GET http://localhost:8001/api/v1/vendedores/ \
  -H "Authorization: Bearer TOKEN_ADMIN"

# Crear vendedor
curl -X POST http://localhost:8001/api/v1/vendedores/ \
  -H "Authorization: Bearer TOKEN_ADMIN" \
  -d '{
    "email": "vendedor@email.com",
    "password": "Prueba123!",
    "nombre": "Vendedor Prueba",
    "id_empresa": "tours-playa-aventura"
  }'
📚 APIs Principales
Método	Endpoint	Descripción
POST	/api/v1/reservas	Crear reserva
GET	/api/v1/reservas	Listar reservas
GET	/api/v1/reservas/{id}	Obtener reserva
PATCH	/api/v1/reservas/{id}/editar	Editar reserva
PATCH	/api/v1/reservas/{id}/registrar-abono	Registrar pago
GET	/api/v1/tickets/scan/{id}	Escanear QR
GET	/api/v1/vendedores/	Listar vendedores
POST	/api/v1/vendedores/	Crear vendedor
Autenticación
Vendedor Frontend: API Key (X-API-Key)

Admin: JWT via Supabase Auth (ES256)

🚀 Despliegue a Producción
Backend (Render/Railway)
bash
# 1. Configurar variables de entorno
# 2. Instalar dependencias
# 3. Iniciar con gunicorn + uvicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
Frontend (Vercel)
bash
# 1. Conectar repositorio a Vercel
# 2. Configurar variables de entorno
# 3. Deploy automático desde main
n8n (Cloud)
bash
# 1. Crear cuenta en n8n.cloud
# 2. Importar workflow
# 3. Configurar webhooks
# 4. Actualizar .env del backend
🤝 Contribución
¡Las contribuciones son bienvenidas!

Fork el repositorio

Crea una rama (git checkout -b feature/nueva-funcionalidad)

Commit tus cambios (git commit -m '✨ Nueva funcionalidad')

Push a la rama (git push origin feature/nueva-funcionalidad)

Abre un Pull Request

Guía de Estilo
Backend: PEP 8 + type hints

Frontend: ESLint + Prettier

Commits: Mensajes convencionales (feat:, fix:, docs:)

📄 Licencia
Distribuido bajo la licencia MIT. Ver LICENSE para más información.

text
MIT License

Copyright (c) 2026 Sistema-Tour

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
📧 Soporte
Contacto	Canal
Issues	GitHub Issues
Discord	Próximamente
Email:santicarreno027@gmail.com
🙏 Agradecimientos:
FastAPI - Framework backend moderno y rápido

Next.js - React framework con SSR y SSG

Supabase - Auth y base de datos serverless

n8n - Orquestación de workflows

SendGrid - Email transaccional confiable

<div align="center">
⭐ ¡Si te gusta el proyecto, dale una estrella! ⭐

https://img.shields.io/github/stars/santicarreno027-pixel/Sistema-tourQR?style=social

</div> ```
