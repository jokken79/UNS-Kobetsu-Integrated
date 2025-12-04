# Configuración de Sincronización de Datos

## Problema Actual

El contenedor Docker no puede acceder directamente a rutas UNC de Windows (`\\UNS-Kikaku\共有フォルダ\...`).

## Soluciones Disponibles

### ✅ Opción 1: Usar Carpeta Local (Para Testing)

Si tienes una copia local de los archivos de red:

1. Copia los archivos a una carpeta local, por ejemplo:
   ```
   D:\SCTDataBase\
   ├── 【新】社員台帳(UNS)T　2022.04.05～.xlsm
   ├── factories_index.json
   └── factories\
       └── *.json
   ```

2. Modifica `docker-compose.yml` para montar esa carpeta:

```yaml
services:
  uns-kobetsu-backend:
    # ... (existing config)
    environment:
      # ... (existing env vars)
      SYNC_DATA_PATH: /network_data  # <-- Agregar esta línea
    volumes:
      - ./backend:/app
      - uns_kobetsu_outputs:/app/outputs
      - D:/SCTDataBase:/network_data  # <-- Agregar esta línea
```

3. Reinicia el contenedor:
   ```bash
   docker compose restart uns-kobetsu-backend
   ```

### ✅ Opción 2: Mapear Unidad de Red en Windows

Si la red está accesible desde tu máquina Windows:

1. Abre PowerShell como Administrador y ejecuta:
   ```powershell
   net use Z: "\\UNS-Kikaku\共有フォルダ" /persistent:yes
   ```

2. Modifica `docker-compose.yml`:

```yaml
services:
  uns-kobetsu-backend:
    # ... (existing config)
    environment:
      SYNC_DATA_PATH: /network_data
    volumes:
      - ./backend:/app
      - uns_kobetsu_outputs:/app/outputs
      - Z:/SCTDateBase:/network_data
```

3. Reinicia:
   ```bash
   docker compose restart uns-kobetsu-backend
   ```

### ✅ Opción 3: Ejecutar Backend Fuera de Docker (Acceso Directo a Red)

Si necesitas acceso directo a la red UNC sin mapear unidades:

1. Para el contenedor del backend:
   ```bash
   docker compose stop uns-kobetsu-backend
   ```

2. Instala dependencias Python localmente:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Ejecuta el backend directamente:
   ```bash
   # En PowerShell o CMD (no Git Bash)
   cd backend
   set DATABASE_URL=postgresql://kobetsu_admin:CHANGE_THIS_IN_PRODUCTION@localhost:5442/kobetsu_db
   set REDIS_URL=redis://localhost:6389/0
   uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload
   ```

   El backend corriendo en Windows tendrá acceso directo a `\\UNS-Kikaku\...`

### ✅ Opción 4: Conectar a Red Corporativa

Si necesitas acceso a la red corporativa:

1. Conecta a la VPN de UNS (si aplica)
2. Verifica acceso:
   ```powershell
   Test-Path "\\UNS-Kikaku\共有フォルダ\SCTDateBase"
   ```
3. Si retorna `True`, usa Opción 2 o 3

## Verificar que Funciona

Después de configurar cualquier opción:

1. Navega a: http://localhost:3010/sync
2. Click en "すべて同期" (Sincronizar Todo)
3. Deberías ver estadísticas exitosas en lugar de "Network Error"

## Estado Actual

- ❌ Ruta de red UNC no accesible desde Docker
- ✅ Backend funcionando correctamente
- ✅ Frontend funcionando correctamente
- ✅ Datos locales importados (fábricas y empleados)
- ⏳ Sincronización con Base Madre deshabilitada temporalmente (se usan datos locales)

## ¿Cuál opción usar?

- **Development/Testing:** Opción 1 (carpeta local)
- **Producción con VPN:** Opción 2 o 4 (unidad mapeada)
- **Máximo acceso:** Opción 3 (backend fuera de Docker)

## Siguiente Paso

¿Cuál opción prefieres? Puedo ayudarte a configurar cualquiera de ellas.
