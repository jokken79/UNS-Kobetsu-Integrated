# 📥 Guía de Importación - UNS Kobetsu System

Esta guía te muestra cómo importar empleados y fábricas en el futuro usando la interfaz web.

---

## 🎯 Método Recomendado: Interfaz Web

### Acceso

1. Abre tu navegador y ve a: **http://localhost:3010/import**
2. Inicia sesión si es necesario (admin@local.dev / admin123)

---

## 👥 Importar Empleados

### Paso 1: Preparar el Archivo Excel

Tu archivo debe ser:
- **Formato**: `.xlsm` o `.xlsx`
- **Archivo recomendado**: `社員台帳(UNS)T　2022.04.05～.xlsm`
- **Hoja requerida**: `DBGenzaiX`

### Paso 2: Usar la Interfaz Web

1. Ve a http://localhost:3010/import
2. Clic en la pestaña **"📥 インポート"** (Importar)
3. Asegúrate de que **"👥 従業員マスタ"** (Empleados) esté seleccionado
4. Arrastra y suelta el archivo Excel O clic en **"ファイルを選択"** (Seleccionar archivo)
5. Espera a ver el **Preview** (Vista previa)
6. Revisa los datos y errores si los hay
7. Selecciona el modo:
   - **新規のみ作成** (Solo crear nuevos)
   - **既存のみ更新** (Solo actualizar existentes)
   - **同期** (Sincronizar - crear + actualizar) ← **RECOMENDADO**
8. Clic en **"インポート実行"** (Ejecutar importación)
9. ✅ ¡Listo!

### Vista Previa Incluye:

- **Total de filas** procesadas
- **Nuevos empleados** a crear (verde)
- **Empleados a actualizar** (azul)
- **Registros con error** (rojo)
- **Tabla con los primeros 100 registros** para revisar

### Datos Importados:

- ✅ Número de empleado (社員№)
- ✅ Nombre completo (氏名 + カナ)
- ✅ Fecha de nacimiento (生年月日) - **IMPORTANTE para clasificación de edad**
- ✅ Género, nacionalidad
- ✅ Empresa/fábrica asignada
- ✅ Departamento y línea (配属先 + ライン)
- ✅ Tarifas (時給 + 請求単価)
- ✅ Información de visa
- ✅ Dirección y contacto
- ✅ Estado (在籍/退社)

---

## 🏭 Importar Fábricas

### Paso 1: Preparar los Archivos JSON

Tus archivos deben estar en:
- **Carpeta**: `E:\config\factories\`
- **Formato**: `.json`
- **Estructura**: Tu formato completo con client_company, plant, lines, etc.

### Paso 2: Usar la Interfaz Web

#### ⭐ Opción A: Importar TODOS los JSON de una vez (NUEVO ✨)

1. Ve a http://localhost:3010/import
2. Clic en **"📥 インポート"**
3. Selecciona **"🏭 工場マスタ"** (Fábricas)
4. Clic en **"ファイルを選択"** (Seleccionar archivos)
5. **Selecciona MÚLTIPLES archivos JSON** (Ctrl+Click o Shift+Click)
6. Verás la lista de archivos seleccionados
7. Clic en **"🚀 XXファイルを一括インポート"** (Importación masiva)
8. ¡Espera y listo! Se importan todos automáticamente

**Ventajas:**
- ✅ No necesitas línea de comandos
- ✅ Seleccionas exactamente qué archivos quieres importar
- ✅ Ves el progreso en tiempo real
- ✅ Todo desde el navegador

#### Opción B: Importar UN archivo JSON individual

1. Ve a http://localhost:3010/import
2. Clic en **"📥 インポート"**
3. Selecciona **"🏭 工場マスタ"** (Fábricas)
4. Arrastra y suelta el archivo JSON O selecciona el archivo
5. Revisa el preview
6. Clic en **"インポート実行"**

#### Opción C: Importar TODOS los JSON (Línea de comandos)

Si prefieres usar script automático:

```bash
# En Windows (desde D:\UNS-Kobetsu-Integrated)
.\import_factories_windows.bat
```

Este script:
1. Copia todos los archivos de `E:\config\factories\` al contenedor
2. Los importa automáticamente
3. Muestra el resumen

### Datos Importados de Fábricas:

- ✅ Información del cliente (client_company)
- ✅ Información de la planta (plant)
- ✅ **Líneas de producción** con:
  - Departamento y nombre de línea
  - **Supervisor** (nombre, departamento, teléfono)
  - Descripción del trabajo
  - **Tarifa horaria** por línea
- ✅ Horarios y calendario
- ✅ Información de pago
- ✅ Fechas de抵触 (conflict_date) y acuerdos

---

## 📤 Exportar Datos

### Desde la Interfaz Web

1. Ve a http://localhost:3010/import
2. Clic en **"📤 エクスポート"** (Exportar)
3. Selecciona el tipo de datos:
   - 👥 Empleados
   - 🏭 Fábricas
   - 📄 Contratos (個別契約書)
4. Clic en **"📥 JSON エクスポート"**
5. El archivo se descargará automáticamente

### Formato de Exportación

- **Formato**: JSON
- **Cantidad**: Máximo 10,000 registros
- **Uso**: Puedes abrir en Excel usando "Datos → Desde JSON"

---

## 🔍 Verificar Datos Importados

### Opción 1: Ver en la Interfaz Web

**Empleados:**
- http://localhost:3010/employees
- Muestra todos los empleados con filtros
- Clasificación por edad visible

**Fábricas:**
- http://localhost:3010/factories
- Muestra todas las fábricas con líneas de producción

### Opción 2: Ver Estadísticas

- http://localhost:3010/import (pestaña "📊 データ概要")
- Muestra:
  - Total de empleados (activos + retirados)
  - Total de fábricas
  - Distribución de empleados por estado

### Opción 3: Base de Datos Directa (Avanzado)

- http://localhost:8090 (Adminer)
- **Server**: uns-kobetsu-db
- **Usuario**: kobetsu_admin
- **Password**: uns_kobetsu_local_2024
- **Base de datos**: kobetsu_db

---

## 📊 Clasificación de Edades (Importante)

El sistema calcula automáticamente la edad según la fecha de nacimiento:

| Clasificación | Requisitos Legales |
|---------------|-------------------|
| **< 18 años** | Prohibiciones especiales (no overtime, no trabajo nocturno) |
| **18-44 años** | Trabajadores regulares |
| **45-64 años** | Consideraciones especiales de seguridad |
| **65+ años** | Empleo continuo obligatorio (ley 2025) |

**Estado actual de tus empleados activos:**
- 18-44 años: **393 empleados**
- 45-64 años: **7 empleados**
- 65+ años: **0 empleados**

Esta información es **CRÍTICA** para generar correctamente la 派遣先通知書 (notificación al cliente).

---

## ⚠️ Errores Comunes

### Error: "No se detectó la hoja DBGenzaiX"

**Solución**: Asegúrate de que el archivo Excel tenga la hoja exactamente con el nombre `DBGenzaiX`.

### Error: "Fecha de nacimiento inválida"

**Solución**: Revisa que la columna de fecha de nacimiento tenga formato de fecha válido en Excel.

### Error: "Número de empleado duplicado"

**Solución**:
- Si quieres actualizar: Usa modo **"同期"** (Sincronizar)
- Si quieres ignorar duplicados: Revisa el preview y confirma

### Error: "Supervisor info no encontrado"

**Solución**: Para fábricas, asegúrate de que el JSON tenga la estructura completa con `lines.assignment.supervisor`.

---

## 🆘 Si Algo Sale Mal

1. **Revisa el Preview**: Siempre muestra errores antes de importar
2. **Verifica los logs**: En la interfaz se muestran errores específicos por fila
3. **Haz backup antes**: Usa el botón de Exportar para guardar tus datos actuales
4. **Borra si es necesario**: Ver sección "Borrar Datos" en IMPORTACION_FACIL.md

---

## 💡 Tips

✅ **Siempre usa modo "同期" (Sincronizar)** - Es el más seguro y actualiza todo
✅ **Revisa el Preview primero** - Identifica problemas antes de importar
✅ **Exporta antes de importar masivamente** - Ten un backup
✅ **La fecha de nacimiento es obligatoria** - Asegúrate de que todos los empleados la tengan
✅ **Para futuras actualizaciones** - Solo arrastra el archivo Excel actualizado y el sistema detectará automáticamente qué cambió

---

## 📞 Resumen Rápido

### Para Empleados:
```
1. Abre: http://localhost:3010/import
2. Selecciona: 👥 従業員マスタ
3. Arrastra: Tu archivo .xlsm
4. Revisa el preview
5. Clic: インポート実行
```

### Para Fábricas:
```
Opción 1 (UI):
1. Abre: http://localhost:3010/import
2. Selecciona: 🏭 工場マスタ
3. Arrastra: archivo .json individual
4. Clic: インポート実行

Opción 2 (Todos):
1. Ejecuta: .\import_factories_windows.bat
2. Espera el resumen
```

¡Eso es todo! 🎉
