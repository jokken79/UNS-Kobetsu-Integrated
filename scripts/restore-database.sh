#!/bin/bash
# Restaurar backup de PostgreSQL para UNS Kobetsu

set -e

cd "$(dirname "$0")/.."

# Configuración
BACKUP_DIR="${BACKUP_DIR:-./backups}"
CONTAINER_NAME="uns-kobetsu-db"

# Cargar variables de entorno
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
fi

DB_NAME=${POSTGRES_DB:-kobetsu_db}
DB_USER=${POSTGRES_USER:-kobetsu_admin}

echo "================================================================"
echo "  Restaurar PostgreSQL - UNS Kobetsu"
echo "================================================================"
echo ""

# Verificar argumento
if [ -z "$1" ]; then
    echo "Uso: $0 <archivo-backup.sql.gz>"
    echo ""
    echo "Backups disponibles:"
    if [ -d "$BACKUP_DIR" ]; then
        ls -lht "$BACKUP_DIR"/kobetsu_db_*.sql.gz 2>/dev/null | head -10 | awk '{printf "  %s  %5s  %s\n", $6" "$7" "$8, $5, $9}' || echo "  (ninguno)"
        echo ""
        echo "Último backup:"
        if [ -L "$BACKUP_DIR/latest.sql.gz" ]; then
            LATEST=$(readlink "$BACKUP_DIR/latest.sql.gz")
            echo "  $BACKUP_DIR/latest.sql.gz → $LATEST"
        else
            echo "  (no existe enlace 'latest')"
        fi
    else
        echo "  (directorio de backups no existe)"
    fi
    echo ""
    echo "Ejemplo:"
    echo "  $0 backups/kobetsu_db_20250130_120000.sql.gz"
    echo "  $0 backups/latest.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"

# Verificar que el archivo existe
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Archivo no encontrado: $BACKUP_FILE"
    exit 1
fi

# Verificar que el container existe y está corriendo
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Container $CONTAINER_NAME no está corriendo"
    echo ""
    echo "Iniciar con: docker-compose up -d"
    exit 1
fi

echo "⚠️  ADVERTENCIA: Esta operación SOBREESCRIBIRÁ la base de datos actual"
echo ""
echo "  Base de datos: $DB_NAME"
echo "  Usuario:       $DB_USER"
echo "  Container:     $CONTAINER_NAME"
echo "  Backup:        $BACKUP_FILE"
echo ""
read -p "¿Continuar? (escribir 'yes' para confirmar): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Operación cancelada"
    exit 1
fi

echo ""
echo "================================================================"
echo ""

# Crear backup de seguridad antes de restaurar
SAFETY_BACKUP="kobetsu_db_before_restore_$(date +%Y%m%d_%H%M%S).sql.gz"
echo "📦 Creando backup de seguridad: $SAFETY_BACKUP"

docker exec "$CONTAINER_NAME" pg_dump \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-owner \
    --no-privileges \
    > "${BACKUP_DIR}/temp_restore.sql" 2>/dev/null

gzip -c "${BACKUP_DIR}/temp_restore.sql" > "${BACKUP_DIR}/${SAFETY_BACKUP}"
rm -f "${BACKUP_DIR}/temp_restore.sql"

echo "✅ Backup de seguridad creado"
echo ""

# Descomprimir si es necesario
TEMP_SQL="/tmp/restore_kobetsu_$(date +%s).sql"

if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo "📂 Descomprimiendo backup..."
    gunzip -c "$BACKUP_FILE" > "$TEMP_SQL"
else
    cp "$BACKUP_FILE" "$TEMP_SQL"
fi

# Restaurar
echo "🔄 Restaurando base de datos..."
echo ""

# Ejecutar restauración
if cat "$TEMP_SQL" | docker exec -i "$CONTAINER_NAME" psql \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --quiet \
    2>&1 | grep -v "NOTICE:"; then

    echo ""
    echo "✅ Base de datos restaurada exitosamente"

    # Limpiar archivo temporal
    rm -f "$TEMP_SQL"

    echo ""
    echo "================================================================"
    echo "  RESUMEN"
    echo "================================================================"
    echo ""
    echo "  ✅ Restauración completada"
    echo "  📦 Backup de seguridad: ${BACKUP_DIR}/${SAFETY_BACKUP}"
    echo ""
    echo "Si algo salió mal, restaurar con:"
    echo "  $0 ${BACKUP_DIR}/${SAFETY_BACKUP}"
    echo ""
else
    echo ""
    echo "❌ Error al restaurar base de datos"
    echo ""
    echo "El backup de seguridad NO fue afectado:"
    echo "  ${BACKUP_DIR}/${SAFETY_BACKUP}"
    echo ""

    # Limpiar archivo temporal
    rm -f "$TEMP_SQL"

    exit 1
fi
