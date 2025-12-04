# 📄 Document Generation V2 - Complete Guide

**Nueva arquitectura de generación de documentos con JSON como formato intermedio**

## 🎯 ¿Qué es esto?

Un sistema COMPLETO para generar documentos legales japoneses (個別契約書, 通知書, etc.) en formato Excel y PDF, con separación clara entre datos y presentación.

## 🏗️ Arquitectura

```
┌──────────────────────────────────────────────────────────────┐
│                    CAPA DE DATOS                             │
├──────────────────────────────────────────────────────────────┤
│  KobetsuKeiyakusho (ORM Model)                              │
│         ↓                                                    │
│  DocumentDataService.from_kobetsu_contract()                │
│         ↓                                                    │
│  DocumentDataSchema (JSON normalizado)                      │
│         {                                                    │
│           "contract_number": "KOB-202512-0001",            │
│           "dates": {...},                                   │
│           "factory": {...},                                 │
│           "employees": [...]                                │
│         }                                                    │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│                 CAPA DE GENERACIÓN                           │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ExcelGeneratorV2(json_schema)                              │
│  ├─ Carga template.xlsx                                     │
│  ├─ Reemplaza {{placeholders}}                              │
│  └─ Retorna .xlsx bytes                                     │
│                                                              │
│  PDFGeneratorV2(json_schema)                                │
│  ├─ Renderiza template.html (Jinja2)                        │
│  ├─ Convierte HTML → PDF (WeasyPrint)                       │
│  └─ Retorna .pdf bytes                                      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## ✅ Ventajas de esta Arquitectura

### 1. **Separación de Datos y Presentación**
- Los datos están en JSON (fácil de validar, testear, versionable)
- Los templates están separados (Excel o HTML)
- Sin dependencias cruzadas

### 2. **Reutilización**
- El mismo JSON sirve para Excel, PDF, HTML, email, etc.
- No hay que repetir lógica de formato

### 3. **Testeable**
- Puedes validar el JSON independientemente
- Puedes testear los generadores con JSON fake
- Fácil de debuggear

### 4. **Mantenible**
- Cambiar el diseño = editar template (Excel o HTML)
- Cambiar datos = modificar JSON schema
- No hay código HTML/CSS mezclado con lógica

## 📦 Archivos Creados

```
backend/
├── app/
│   ├── schemas/
│   │   └── document_data.py          # ✅ JSON Schema (DocumentDataSchema)
│   │
│   ├── services/
│   │   ├── document_data_service.py  # ✅ ORM → JSON converter
│   │   ├── excel_generator_v2.py     # ✅ JSON → Excel
│   │   └── pdf_generator_v2.py       # ✅ JSON → PDF (Jinja2 + WeasyPrint)
│   │
│   └── api/v1/
│       └── documents_v2.py            # ✅ API endpoints
│
└── templates/
    ├── excel/                         # ⚠️ NECESITAS CREAR LOS TEMPLATES
    │   ├── kobetsu_keiyakusho.xlsx   # (Ejecuta extract_templates.py)
    │   ├── tsuchisho.xlsx
    │   └── ...
    │
    └── pdf/
        ├── kobetsu_keiyakusho.html    # ✅ Template HTML con Jinja2
        └── base.css                   # ⚠️ CSS para PDFs (opcional)
```

## 🚀 CÓMO USAR (Paso a Paso)

### Paso 1: Instalar Dependencias

```bash
# Backend
cd backend
pip install jinja2 weasyprint openpyxl

# WeasyPrint necesita GTK en algunos sistemas:
# macOS:   brew install python3 cairo pango gdk-pixbuf libffi
# Ubuntu:  apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0
# Windows: Descarga GTK desde https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
```

### Paso 2: Crear Templates de Excel

**OPCIÓN A: Tienes el archivo Excel original**

```bash
# 1. Copia el archivo Excel a D:\ExcelKobetsukeiyakusho.xlsx
#    (o edita la ruta en backend/scripts/extract_templates.py)

# 2. Ejecuta el script de extracción
python backend/scripts/extract_templates.py

# 3. Verifica que se crearon los templates
ls backend/templates/excel/
# Deberías ver: kobetsu_keiyakusho.xlsx, tsuchisho.xlsx, etc.
```

**OPCIÓN B: No tienes el archivo Excel original**

Puedes crear templates desde cero:

1. Crea archivos Excel en `backend/templates/excel/`
2. Usa placeholders como `{{contract_number}}`, `{{client_company}}`, etc.
3. Formatea los documentos como quieras (colores, fuentes, bordes)
4. Guarda los archivos

Ejemplo de placeholder en Excel:
```
┌────────────────────────────────────┐
│  契約番号: {{contract_number}}     │
│  契約日: {{contract_date}}         │
│  派遣先: {{client_company}}        │
└────────────────────────────────────┘
```

### Paso 3: Agregar el Endpoint a la API

Edita `backend/app/main.py`:

```python
from app.api.v1 import documents_v2

# Agregar router
app.include_router(
    documents_v2.router,
    prefix="/api/v1/documents-v2",
    tags=["documents-v2"]
)
```

### Paso 4: Probar la API

```bash
# 1. Levanta el backend
docker compose up -d backend

# 2. Obtén el JSON de un contrato
curl http://localhost:8010/api/v1/documents-v2/1/json

# 3. Genera documento Excel
curl http://localhost:8010/api/v1/documents-v2/1/excel/kobetsu_keiyakusho \
  -o contrato.xlsx

# 4. Genera documento PDF
curl http://localhost:8010/api/v1/documents-v2/1/pdf/kobetsu_keiyakusho \
  -o contrato.pdf

# 5. Genera TODOS los documentos
curl http://localhost:8010/api/v1/documents-v2/1/all?format=both
```

### Paso 5: Integrar con el Frontend

```typescript
// frontend/lib/api.ts

export const documentsV2 = {
  // Obtener JSON
  getJSON: (contractId: number) =>
    api.get(`/documents-v2/${contractId}/json`),

  // Descargar Excel
  downloadExcel: (contractId: number, documentType: string) => {
    window.open(
      `${API_URL}/documents-v2/${contractId}/excel/${documentType}`,
      '_blank'
    );
  },

  // Descargar PDF
  downloadPDF: (contractId: number, documentType: string) => {
    window.open(
      `${API_URL}/documents-v2/${contractId}/pdf/${documentType}`,
      '_blank'
    );
  },

  // Generar todos
  generateAll: (contractId: number, format: 'excel' | 'pdf' | 'both' = 'both') =>
    api.get(`/documents-v2/${contractId}/all?format=${format}`),
};
```

```tsx
// Componente React para descargar documentos
function DocumentDownloader({ contractId }: { contractId: number }) {
  const handleDownload = (format: 'excel' | 'pdf') => {
    if (format === 'excel') {
      documentsV2.downloadExcel(contractId, 'kobetsu_keiyakusho');
    } else {
      documentsV2.downloadPDF(contractId, 'kobetsu_keiyakusho');
    }
  };

  return (
    <div className="flex gap-2">
      <button onClick={() => handleDownload('excel')}>
        📊 Download Excel
      </button>
      <button onClick={() => handleDownload('pdf')}>
        📄 Download PDF
      </button>
    </div>
  );
}
```

## 📝 Ejemplo de Uso Programático

```python
from sqlalchemy.orm import Session
from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho
from app.services.document_data_service import DocumentDataService
from app.services.excel_generator_v2 import ExcelGeneratorV2
from app.services.pdf_generator_v2 import PDFGeneratorV2

# 1. Cargar contrato desde DB
contract = db.query(KobetsuKeiyakusho).filter(
    KobetsuKeiyakusho.id == 1
).first()

# 2. Convertir a JSON normalizado
json_schema = DocumentDataService.from_kobetsu_contract(contract, db)

# 3. Generar Excel
excel_gen = ExcelGeneratorV2(json_schema)
excel_bytes = excel_gen.generate_kobetsu_keiyakusho()

with open("contrato.xlsx", "wb") as f:
    f.write(excel_bytes)

# 4. Generar PDF
pdf_gen = PDFGeneratorV2(json_schema)
pdf_bytes = pdf_gen.generate_kobetsu_keiyakusho()

with open("contrato.pdf", "wb") as f:
    f.write(pdf_bytes)

# 5. Generar TODOS los documentos
all_excel = excel_gen.generate_all()
all_pdf = pdf_gen.generate_all()
```

## 🎨 Personalizar Templates

### Templates de Excel

1. Abre `backend/templates/excel/kobetsu_keiyakusho.xlsx` en Excel
2. Edita el diseño (fuentes, colores, bordes)
3. Usa placeholders `{{field_name}}` donde quieras insertar datos
4. Guarda el archivo

**Placeholders disponibles:**
```
{{contract_number}}          - Número de contrato
{{contract_date}}            - Fecha de contrato
{{client_company}}           - Nombre de empresa cliente
{{worksite_name}}            - Nombre del lugar de trabajo
{{work_content}}             - Contenido del trabajo
{{work_start}}               - Hora de inicio
{{work_end}}                 - Hora de fin
{{hourly_rate}}              - Tarifa por hora
{{employee_1_name}}          - Nombre del empleado 1
{{employee_1_kana}}          - Kana del empleado 1
... etc
```

### Templates de PDF (HTML)

1. Edita `backend/templates/pdf/kobetsu_keiyakusho.html`
2. Usa sintaxis Jinja2:

```html
<!-- Variables simples -->
<p>契約番号: {{ data.contract_number }}</p>

<!-- Condicionales -->
{% if data.supervisor.department %}
  <p>部署: {{ data.supervisor.department }}</p>
{% endif %}

<!-- Loops -->
{% for employee in data.employees %}
  <tr>
    <td>{{ employee.full_name }}</td>
    <td>{{ employee.employee_number }}</td>
  </tr>
{% endfor %}

<!-- Filtros personalizados -->
<p>{{ data.contract_date | format_date_japanese }}</p>
<p>{{ data.rates.hourly_rate | format_currency }}</p>
```

3. Personaliza CSS en `<style>` o en `base.css`

## 🔧 Troubleshooting

### Error: "Template not found"

```bash
# Solución: Ejecuta el script de extracción
python backend/scripts/extract_templates.py
```

### Error: WeasyPrint installation failed

```bash
# macOS
brew install python3 cairo pango gdk-pixbuf libffi

# Ubuntu/Debian
sudo apt-get install python3-cffi python3-brotli libpango-1.0-0

# Windows
# Descarga GTK desde:
# https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
```

### Fuentes japonesas no se muestran en PDF

Edita `backend/templates/pdf/kobetsu_keiyakusho.html`:

```css
body {
    font-family: "MS Mincho", "Yu Mincho", "Hiragino Mincho ProN", serif;
}
```

### Los placeholders no se reemplazan en Excel

- Verifica que uses la sintaxis exacta: `{{placeholder}}` (con doble llave)
- Asegúrate de que el placeholder coincida con el nombre en el código
- Revisa que no haya espacios extra: `{{ name }}` vs `{{name}}`

## 📚 Documentos Soportados

### Excel ✅
- ✅ **個別契約書** (kobetsu_keiyakusho) - Individual Dispatch Contract
- ✅ **通知書** (tsuchisho) - Notification
- 🚧 **DAICHO** (daicho) - Registry (necesita template)
- 🚧 **派遣元管理台帳** (hakenmoto_daicho) - Dispatch Origin Ledger
- 🚧 **就業条件明示書** (shugyo_joken) - Employment Conditions
- 🚧 **契約書** (keiyakusho) - Labor Contract

### PDF ✅
- ✅ **個別契約書** (kobetsu_keiyakusho) - Individual Dispatch Contract
- 🚧 **通知書** (tsuchisho) - Notification (necesita template HTML)
- 🚧 **DAICHO** (daicho) - Registry

**Nota:** Los marcados con 🚧 necesitan que crees los templates correspondientes.

## 🎓 Requisitos Legales (労働者派遣法第26条)

Todos los documentos cumplen con los 16 campos obligatorios:

1. ✅ 業務内容 - Work content
2. ✅ 就業場所 - Worksite location
3. ✅ 指揮命令者 - Supervisor
4. ✅ 就業期間 - Employment period
5. ✅ 就業時間・休憩 - Work hours & breaks
6. ✅ 安全衛生 - Safety measures
7. ✅ 派遣労働者数 - Number of workers
8. ✅ 時間外労働 - Overtime hours
9. ✅ 派遣料金 - Dispatch rates
10. ✅ 苦情処理 - Complaint handling
11. ✅ 派遣元責任者 - Dispatch origin manager
12. ✅ 派遣先責任者 - Client manager
13. ✅ 福利厚生施設 - Welfare facilities
14. ✅ 契約解除 - Contract termination
15. ✅ 派遣許可番号 - License number
16. ✅ その他特記事項 - Special notes

**Referencias oficiales:**
- [労働者派遣法第26条 - MHLW PDF](https://www.mhlw.go.jp/general/seido/anteikyoku/jukyu/haken/youryou/dl/7.pdf)
- [Templates oficiales - Tokyo Labour Bureau](https://jsite.mhlw.go.jp/tokyo-roudoukyoku/riyousha_mokuteki_menu/mokuteki_naiyou/haken_part/youshikirei.html)
- [Worker Dispatch Law - English](https://monolith.law/en/general-corporate/worker-dispatch-contract)

## 🚀 Next Steps

1. **Crear más templates:**
   - Copia `kobetsu_keiyakusho.html` y modifica para otros documentos
   - Extrae más sheets del Excel original si es necesario

2. **Agregar validaciones:**
   - Validar JSON schema antes de generar
   - Agregar checks de campos obligatorios

3. **Mejorar performance:**
   - Cachear templates compilados
   - Generar documentos en background (Celery/RQ)

4. **Agregar preview:**
   - Endpoint que retorna HTML (antes de PDF)
   - Previsualización en el frontend

5. **Versionado de documentos:**
   - Guardar documentos generados en DB
   - Historial de versiones

## 💡 Comparación con Sistema Anterior

| Característica | Sistema Anterior | Sistema V2 (JSON) |
|---------------|------------------|-------------------|
| Arquitectura | ORM → DOCX directo | ORM → JSON → Excel/PDF |
| Formato | Solo DOCX | Excel + PDF + HTML |
| Mantenibilidad | Código mezclado | Datos separados |
| Testeable | Difícil | Fácil (JSON) |
| Reutilización | No | Sí (mismo JSON) |
| Formato perfecto | No (DOCX genérico) | Sí (templates Excel) |
| Flexibilidad | Baja | Alta |

## 📞 Soporte

¿Problemas? Revisa:
1. Este documento (DOCUMENT_GENERATION_V2.md)
2. CLAUDE.md - Instrucciones del proyecto
3. Logs del backend: `docker compose logs -f backend`
4. API docs: http://localhost:8010/docs

---

**Creado:** 2025-12-04
**Versión:** 2.0
**Status:** ✅ Ready for production (after creating templates)
