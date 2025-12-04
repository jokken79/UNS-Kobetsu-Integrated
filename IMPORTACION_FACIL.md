# 📥 Guía Rápida de Importación

## 🎯 Resumen Rápido

### Empleados ✅ - FUNCIONA
- **Archivo**: `D:\【新】社員台帳(UNS)T 2022.04.05～.xlsm`
- **Hoja**: `DBGenzaiX`
- **Estado**: ✅ **99 empleados importados** (10 activos, 89 retirados)

### Fábricas ⚠️ - REQUIERE AJUSTES
- **Archivos**: 25 archivos JSON en `E:\config\factories\`
- **Estado**: ⚠️ Requiere adaptar formato JSON al modelo de la DB

---

## 📊 Importación de Empleados (LISTO)

### Método 1: Usar la interfaz web

1. Abre http://localhost:3010/import
2. Sube el archivo Excel: `D:\【新】社員台帳(UNS)T 2022.04.05～.xlsm`
3. Selecciona hoja: `DBGenzaiX`
4. Click en "Importar"

### Método 2: Línea de comandos (más rápido)

```bash
# Copiar Excel al contenedor
docker cp "D:\【新】社員台帳(UNS)T  2022.04.05～.xlsm" uns-kobetsu-backend:/tmp/employees.xlsm

# Ejecutar importación
docker exec uns-kobetsu-backend python scripts/import_employees_excel.py --file /tmp/employees.xlsm --sheet DBGenzaiX
```

---

## 🏭 Importación de Fábricas (PENDIENTE)

### Estado Actual

Tienes **25 archivos JSON** en `E:\config\factories\`, pero el formato de estos JSON no coincide con el modelo actual de la base de datos.

### Formato de JSON Actual (E:\config\factories\)

```json
{
  "factory_id": "三幸技研株式会社_本社工場",
  "client_company": {
    "name": "三幸技研株式会社",
    "address": "愛知県大府市...",
    "phone": "0562-47-5533"
  },
  "plant": {
    "name": "本社工場",
    "address": "..."
  },
  "lines": [...]
}
```

### Formato Esperado por la DB

```json
{
  "company_name": "三幸技研株式会社",
  "plant_name": "本社工場",
  "company_address": "...",
  "company_phone": "...",
  "contact_person": "...",
  "contact_department": "...",
  ...
}
```

### Opciones

**Opción 1: Importar manualmente** (más simple)
- Usa la interfaz web en http://localhost:3010/factories/create
- Crea cada fábrica una por una

**Opción 2: Adaptar los JSON** (requiere desarrollo)
- Crear un script que convierta el formato de `E:\config\factories\` al formato de la DB
- Requiere aproximadamente 1-2 horas de desarrollo

**Opción 3: Importar desde Excel original** (más fácil)
- Si tienes los datos de fábricas en Excel, usa la interfaz de importación

---

## ✅ Verificar Importaciones

### Ver Empleados

```bash
# En la base de datos
docker exec uns-kobetsu-backend bash -c "PGPASSWORD=\$POSTGRES_PASSWORD psql -h uns-kobetsu-db -U kobetsu_admin -d kobetsu_db -c 'SELECT COUNT(*) FROM employees;'"

# En la web
# http://localhost:3010/employees
```

### Ver Fábricas

```bash
# En la base de datos
docker exec uns-kobetsu-backend bash -c "PGPASSWORD=\$POSTGRES_PASSWORD psql -h uns-kobetsu-db -U kobetsu_admin -d kobetsu_db -c 'SELECT COUNT(*) FROM factories;'"

# En la web
# http://localhost:3010/factories
```

---

## 🔧 Scripts Útiles

### Re-importar Empleados

Si necesitas actualizar datos de empleados:

```bash
# Modo dry-run (solo muestra cambios)
docker exec uns-kobetsu-backend python scripts/import_employees_excel.py --file /tmp/employees.xlsm --dry-run

# Importación real
docker exec uns-kobetsu-backend python scripts/import_employees_excel.py --file /tmp/employees.xlsm
```

### Limpiar Base de Datos (CUIDADO!)

```bash
# Borrar TODOS los empleados
docker exec uns-kobetsu-backend bash -c "PGPASSWORD=\$POSTGRES_PASSWORD psql -h uns-kobetsu-db -U kobetsu_admin -d kobetsu_db -c 'DELETE FROM employees;'"

# Borrar TODAS las fábricas
docker exec uns-kobetsu-backend bash -c "PGPASSWORD=\$POSTGRES_PASSWORD psql -h uns-kobetsu-db -U kobetsu_admin -d kobetsu_db -c 'DELETE FROM factories;'"
```

---

## 📝 Notas Finales

### ✅ Importación Completada

- **1,051 empleados** importados desde Excel DBGenzaiX
  - **400 empleados activos**
  - **557 empleados retirados**
  - **TODOS con fecha de nacimiento** (100% completo)

- **24 fábricas** importadas con éxito
  - **96 líneas de producción** con información detallada de supervisores y tarifas

### 📊 Distribución de Edades (Empleados Activos)

Según las normativas de 労働者派遣法 (Ley de Dispatch Laboral):

| Rango de Edad | Cantidad | Categoría Legal |
|---------------|----------|-----------------|
| **18-44 años** | 393 | Trabajadores regulares |
| **45-64 años** | 7 | Mediana edad (consideraciones especiales) |
| **65+ años** | 0 | Edad avanzada (empleo continuo) |
| **< 18 años** | 0 | Menores (restricciones especiales) |

**Importancia de la Edad en 個別契約書:**
- La 派遣先通知書 (notificación al cliente) DEBE incluir clasificación de edad
- Trabajadores < 18: Prohibiciones de horas extras, trabajo nocturno, trabajo peligroso
- Trabajadores 45+: Requieren consideraciones especiales de seguridad laboral
- Trabajadores 65+: Sujetos a medidas de empleo continuo obligatorias
