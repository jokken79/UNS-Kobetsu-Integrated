#!/bin/bash
# Backup automático de PostgreSQL para UNS Kobetsu

set -e

cd "$(dirname "$0")/.."

# Configuración
BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_ONLY=$(date +%Y%m%d)
BACKUP_FILE="kobetsu_db_${TIMESTAMP}.sql"
CONTAINER_NAME="uns-kobetsu-db"
RETENTION_DAYS=30

# Cargar variables de entorno
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
fi

DB_NAME=${POSTGRES_DB:-kobetsu_db}
DB_USER=${POSTGRES_USER:-kobetsu_admin}

echo "================================================================"
echo "  Backup PostgreSQL - UNS Kobetsu"
echo "================================================================"
echo ""
echo "  Base de datos: $DB_NAME"
echo "  Usuario:       $DB_USER"
echo "  Container:     $CONTAINER_NAME"
echo "  Destino:       $BACKUP_DIR"
echo ""
echo "================================================================"
echo ""

# Verificar que el container existe y está corriendo
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Container $CONTAINER_NAME no está corriendo"
    echo ""
    echo "Iniciar con: docker-compose up -d"
    exit 1
fi

# Crear directorio de backups si no existe
mkdir -p "$BACKUP_DIR"

echo "📦 Creando backup..."

# Realizar backup con pg_dump
if docker exec "$CONTAINER_NAME" pg_dump \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-owner \
    --no-privileges \
    --clean \
    --if-exists \
    > "${BACKUP_DIR}/${BACKUP_FILE}"; then

    # Verificar que el archivo no está vacío
    if [ ! -s "${BACKUP_DIR}/${BACKUP_FILE}" ]; then
        echo "❌ El backup está vacío"
        rm -f "${BACKUP_DIR}/${BACKUP_FILE}"
        exit 1
    fi

    # Comprimir
    echo "🗜️  Comprimiendo backup..."
    gzip -f "${BACKUP_DIR}/${BACKUP_FILE}"

    BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_FILE}.gz" | cut -f1)

    echo "✅ Backup creado: ${BACKUP_FILE}.gz (${BACKUP_SIZE})"
else
    echo "❌ Error al crear backup"
    exit 1
fi

# Crear symlink al backup más reciente
echo "🔗 Creando enlace simbólico..."
ln -sf "${BACKUP_FILE}.gz" "${BACKUP_DIR}/latest.sql.gz"

# Limpiar backups antiguos
echo "🧹 Limpiando backups antiguos (> ${RETENTION_DAYS} días)..."
DELETED=$(find "$BACKUP_DIR" -name "kobetsu_db_*.sql.gz" -mtime +${RETENTION_DAYS} -delete -print | wc -l)

if [ "$DELETED" -gt 0 ]; then
    echo "   Eliminados: $DELETED backup(s)"
else
    echo "   No hay backups antiguos para eliminar"
fi

# Estadísticas
echo ""
echo "================================================================"
echo "  RESUMEN"
echo "================================================================"
echo ""
echo "  Archivo:   ${BACKUP_FILE}.gz"
echo "  Tamaño:    ${BACKUP_SIZE}"
echo "  Ubicación: ${BACKUP_DIR}/"
echo ""

# Listar últimos 5 backups
echo "Últimos backups:"
ls -lht "$BACKUP_DIR"/kobetsu_db_*.sql.gz 2>/dev/null | head -5 | awk '{printf "  %s  %5s  %s\n", $6" "$7" "$8, $5, $9}' || echo "  (ninguno)"

echo ""
echo "================================================================"
echo ""
echo "💡 Para restaurar este backup:"
echo "  ./scripts/restore-database.sh ${BACKUP_FILE}.gz"
echo ""
