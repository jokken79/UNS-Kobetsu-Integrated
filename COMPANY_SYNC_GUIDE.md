# 🏢 Guía de Sincronización de Empresas desde Base Madre

## 📋 Resumen

Esta guía explica cómo sincronizar empresas y plantas desde **Base Madre** a **Kobetsu** usando el nuevo esquema compatible.

---

## 🎯 Qué se Sincroniza

### **Base Madre → Kobetsu**

```
┌─────────────────────┐         ┌─────────────────────┐
│   Base Madre API    │         │  Kobetsu Database   │
│                     │         │                     │
│  companies          │────────▶│  companies          │
│  plants             │────────▶│  plants             │
│  jigyosho           │────────▶│  jigyosho           │
└─────────────────────┘         └─────────────────────┘
```

### **Tablas Creadas en Kobetsu**

**1. `companies` (派遣先企業)**
- company_id (PK)
- name, name_kana
- address, phone, fax, email, website
- responsible_department, responsible_name, responsible_phone
- contract_start, contract_end
- **base_madre_company_id** (referencia a Base Madre)
- **last_synced_at** (última sincronización)

**2. `plants` (工場)**
- plant_id (PK)
- company_id (FK → companies)
- jigyosho_id (FK → jigyosho)
- plant_name, plant_code
- plant_address, plant_phone
- manager_name, capacity
- **base_madre_plant_id** (referencia a Base Madre)
- **last_synced_at** (última sincronización)

**3. `jigyosho` (事業所 - Regional Offices)**
- jigyosho_id (PK)
- company_id (FK → companies)
- jigyosho_name, jigyosho_code
- jigyosho_address, jigyosho_phone, jigyosho_fax
- manager_name, manager_phone
- **base_madre_jigyosho_id** (referencia)

---

## 🚀 Paso 1: Aplicar Migración

Primero, aplica la migración para crear las nuevas tablas:

```bash
cd /home/user/UNS-Kobetsu-Integrated

# Verificar que backend esté corriendo
docker compose ps

# Aplicar migración
docker exec -it uns-kobetsu-backend alembic upgrade head
```

**Salida esperada:**
```
INFO  [alembic.runtime.migration] Running upgrade 001 -> 002, add companies and plants tables
```

---

## 🔌 Paso 2: Verificar Base Madre API

Asegúrate de que Base Madre esté corriendo:

```bash
# Verificar health endpoint
curl http://localhost:5000/api/v1/health

# Listar empresas
curl -H "X-API-Key: TU_API_KEY" \
  http://localhost:5000/api/v1/companies

# Listar plantas
curl -H "X-API-Key: TU_API_KEY" \
  http://localhost:5000/api/v1/plants
```

---

## 🔄 Paso 3: Ejecutar Sincronización

### **Opción A: Dry Run (Simulación)**

Ver qué se sincronizaría sin hacer cambios:

```bash
docker exec -it uns-kobetsu-backend python scripts/sync_companies_from_base_madre.py --dry-run
```

### **Opción B: Sincronización Real**

```bash
docker exec -it uns-kobetsu-backend python scripts/sync_companies_from_base_madre.py
```

### **Opción C: Con API Key personalizada**

```bash
docker exec -it uns-kobetsu-backend python scripts/sync_companies_from_base_madre.py \
  --api-key "TU_API_KEY_AQUI"
```

### **Opción D: Solo Empresas (sin plantas)**

```bash
docker exec -it uns-kobetsu-backend python scripts/sync_companies_from_base_madre.py \
  --companies-only
```

### **Opción E: Solo Plantas (sin empresas)**

```bash
docker exec -it uns-kobetsu-backend python scripts/sync_companies_from_base_madre.py \
  --plants-only
```

---

## 📊 Salida del Script

```
============================================================
SYNC COMPANIES & PLANTS FROM BASE MADRE
============================================================
API URL: http://localhost:5000/api/v1
Mode: LIVE
Time: 2024-11-29 12:00:00
============================================================

============================================================
FETCHING COMPANIES FROM BASE MADRE
============================================================
GET http://localhost:5000/api/v1/companies
✅ Fetched 5 companies from Base Madre

============================================================
SYNCING COMPANIES TO LOCAL DATABASE
Mode: LIVE
============================================================

✨ Created: Toyota Motor Corporation (Base Madre ID: 1)
✨ Created: Honda Motor Co. (Base Madre ID: 2)
📝 Updated: Nissan Motor Co. (Base Madre ID: 3)

✅ Changes committed to database

============================================================
FETCHING PLANTS FROM BASE MADRE
============================================================
GET http://localhost:5000/api/v1/plants
✅ Fetched 12 plants from Base Madre

============================================================
SYNCING PLANTS TO LOCAL DATABASE
Mode: LIVE
============================================================

✨ Created: 本社工場 @ Toyota Motor Corporation (Base Madre ID: 1)
✨ Created: 防府工場 @ Toyota Motor Corporation (Base Madre ID: 2)
✨ Created: 浜松工場 @ Honda Motor Co. (Base Madre ID: 3)

✅ Changes committed to database

============================================================
SYNC SUMMARY
============================================================

Companies:
  ✨ Created: 5
  📝 Updated: 0
  ⚠️  Skipped: 0
  ❌ Errors:  0

Plants:
  ✨ Created: 12
  📝 Updated: 0
  ⚠️  Skipped: 0
  ❌ Errors:  0

============================================================
✅ SYNC COMPLETE - All changes saved to database
```

---

## 🔍 Paso 4: Verificar Sincronización

### **API Endpoint: Sync Status**

```bash
curl http://localhost:8010/api/v1/sync/status
```

**Respuesta:**
```json
{
  "companies": {
    "total": 5,
    "synced_from_base_madre": 5,
    "last_sync": "2024-11-29T12:00:00"
  },
  "plants": {
    "total": 12,
    "synced_from_base_madre": 12,
    "last_sync": "2024-11-29T12:00:00"
  }
}
```

### **Listar Empresas**

```bash
curl http://localhost:8010/api/v1/companies
```

### **Listar Plantas de una Empresa**

```bash
curl http://localhost:8010/api/v1/companies/1/plants
```

### **Listar Todas las Plantas**

```bash
curl http://localhost:8010/api/v1/plants
```

### **Opciones para Dropdowns**

```bash
# Empresas (simplificado)
curl http://localhost:8010/api/v1/options/companies

# Plantas (simplificado)
curl http://localhost:8010/api/v1/options/plants?company_id=1
```

---

## 📅 Sincronización Periódica

### **Manualmente (Recomendado para empezar)**

Ejecutar el script cuando agregues nuevas empresas en Base Madre:

```bash
docker exec -it uns-kobetsu-backend python scripts/sync_companies_from_base_madre.py
```

### **Automática con Cron (Futuro)**

Agregar cron job para sincronizar diariamente:

```bash
# Cada día a las 2:00 AM
0 2 * * * cd /home/user/UNS-Kobetsu-Integrated && docker exec -it uns-kobetsu-backend python scripts/sync_companies_from_base_madre.py
```

---

## 🔧 Configuración

### **Variables de Entorno**

En `/home/user/UNS-Kobetsu-Integrated/backend/.env`:

```bash
# Base Madre API Configuration
BASE_MADRE_API_URL=http://localhost:5000/api/v1
BASE_MADRE_API_KEY=your_api_key_here
```

---

## ⚠️ Troubleshooting

### **Error: "No API key provided"**

**Solución:**
```bash
# Pasar API key manualmente
docker exec -it uns-kobetsu-backend python scripts/sync_companies_from_base_madre.py \
  --api-key "TU_API_KEY"
```

### **Error: "Connection refused"**

**Causa:** Base Madre no está corriendo

**Solución:**
```bash
cd /home/user/UNS-Shatak/postgres_app
python app.py
```

### **Error: "Company ID X not found in local DB"**

**Causa:** Intentaste sincronizar plantas antes que empresas

**Solución:**
```bash
# Primero sincroniza empresas
docker exec -it uns-kobetsu-backend python scripts/sync_companies_from_base_madre.py --companies-only

# Luego plantas
docker exec -it uns-kobetsu-backend python scripts/sync_companies_from_base_madre.py --plants-only
```

### **Error: Migration failed**

**Solución:**
```bash
# Ver estado de migraciones
docker exec -it uns-kobetsu-backend alembic current

# Ver historial
docker exec -it uns-kobetsu-backend alembic history

# Forzar upgrade
docker exec -it uns-kobetsu-backend alembic upgrade head
```

---

## 🗃️ Esquema Compatible

### **Kobetsu ahora usa el MISMO esquema que Base Madre:**

```sql
-- Kobetsu
CREATE TABLE companies (
  company_id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  name_kana VARCHAR(255),
  -- ... (igual que Base Madre)
  base_madre_company_id INTEGER UNIQUE,  -- ← Referencia
  last_synced_at TIMESTAMP               -- ← Tracking
);

CREATE TABLE plants (
  plant_id SERIAL PRIMARY KEY,
  company_id INTEGER REFERENCES companies(company_id),
  plant_name VARCHAR(255) NOT NULL,
  -- ... (igual que Base Madre)
  base_madre_plant_id INTEGER UNIQUE,    -- ← Referencia
  last_synced_at TIMESTAMP               -- ← Tracking
);
```

### **Referencia en Contratos:**

```sql
-- kobetsu_keiyakusho ahora puede referenciar companies/plants
ALTER TABLE kobetsu_keiyakusho
  ADD COLUMN company_id INTEGER REFERENCES companies(company_id),
  ADD COLUMN plant_id INTEGER REFERENCES plants(plant_id);
```

---

## 📈 Flujo de Datos Completo

```
┌─────────────────────────────────────────────────────────────┐
│                  FLUJO DE SINCRONIZACIÓN                    │
└─────────────────────────────────────────────────────────────┘

1. Base Madre (PostgreSQL)
   └─ companies, plants, jigyosho
      │
      │ (API REST)
      ▼
2. Base Madre API (Flask)
   └─ GET /api/v1/companies
   └─ GET /api/v1/plants
      │
      │ (HTTP Request)
      ▼
3. Sync Script (Python)
   └─ scripts/sync_companies_from_base_madre.py
   └─ Fetch, Transform, Upsert
      │
      │ (SQLAlchemy ORM)
      ▼
4. Kobetsu Database (PostgreSQL)
   └─ companies (con base_madre_company_id)
   └─ plants (con base_madre_plant_id)
      │
      │ (API REST)
      ▼
5. Kobetsu Frontend (React/Next.js)
   └─ KobetsuFormHybrid
   └─ Usa companies/plants locales
   └─ Usa employees desde Base Madre API (híbrido)
```

---

## ✅ Checklist de Implementación

- [x] Migración 002 creada (companies, plants, jigyosho)
- [x] Modelos SQLAlchemy (Company, Plant, Jigyosho)
- [x] Script de sync (sync_companies_from_base_madre.py)
- [x] API endpoints (/api/v1/companies, /api/v1/plants)
- [x] Sync status endpoint (/api/v1/sync/status)
- [ ] Botón de sync en frontend (/sync page)
- [ ] Actualizar KobetsuFormHybrid para usar companies/plants
- [ ] Documentación de usuario
- [ ] Testing completo

---

## 🎯 Próximos Pasos

1. **Ejecutar migración** en tu base de datos
2. **Ejecutar sync script** para copiar datos de Base Madre
3. **Verificar** que empresas y plantas se copiaron correctamente
4. **Actualizar frontend** para usar las nuevas tablas
5. **Probar** creación de contratos con el nuevo esquema

---

## 📞 Soporte

**Problemas con:**
- **Migración:** Ver logs de alembic
- **Sync Script:** Ejecutar con `--dry-run` primero
- **Base Madre API:** Ver `API_V1_TESTING_GUIDE.md`
- **Kobetsu:** Ver `INTEGRATION_README.md`

---

**¡El esquema de empresas ahora coincide con Base Madre!** 🎉

Las empresas se sincronizarán automáticamente desde Base Madre,
mientras que los contratos se guardan localmente en Kobetsu.

**Best of both worlds: Base Madre para maestros, Kobetsu para contratos.** 🚀
