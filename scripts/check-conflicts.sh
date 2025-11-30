#!/bin/bash
# Verificar conflictos antes de docker-compose up

set -e

cd "$(dirname "$0")/.."

echo "================================================================"
echo "  UNS Kobetsu - Verificacion de Conflictos Docker"
echo "================================================================"
echo ""

CONFLICTS=0
WARNINGS=0

# Cargar variables de entorno
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
fi

# Puertos a verificar (con valores por defecto)
FRONTEND_PORT=${KOBETSU_FRONTEND_PORT:-3010}
BACKEND_PORT=${KOBETSU_BACKEND_PORT:-8010}
ADMINER_PORT=${KOBETSU_ADMINER_PORT:-8090}
DB_PORT=${KOBETSU_DB_PORT:-5442}
REDIS_PORT=${KOBETSU_REDIS_PORT:-6389}

echo "🔍 1. Verificando conflictos de puertos..."
echo "-----------------------------------------------------------"

PORTS=($FRONTEND_PORT $BACKEND_PORT $ADMINER_PORT $DB_PORT $REDIS_PORT)
PORT_NAMES=("Frontend" "Backend" "Adminer" "PostgreSQL" "Redis")

for i in "${!PORTS[@]}"; do
    PORT="${PORTS[$i]}"
    NAME="${PORT_NAMES[$i]}"

    # Verificar si el puerto está en uso
    if command -v lsof &> /dev/null; then
        if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo "❌ Puerto $PORT ($NAME) OCUPADO:"
            lsof -Pi :$PORT -sTCP:LISTEN | tail -n +2 | awk '{printf "   → Proceso: %s (PID: %s)\n", $1, $2}'
            CONFLICTS=$((CONFLICTS + 1))
        else
            echo "✅ Puerto $PORT ($NAME) disponible"
        fi
    elif command -v netstat &> /dev/null; then
        if netstat -tuln 2>/dev/null | grep -q ":$PORT "; then
            echo "⚠️  Puerto $PORT ($NAME) posiblemente ocupado"
            WARNINGS=$((WARNINGS + 1))
        else
            echo "✅ Puerto $PORT ($NAME) disponible"
        fi
    else
        echo "⚠️  No se puede verificar puerto $PORT (lsof/netstat no disponible)"
        WARNINGS=$((WARNINGS + 1))
    fi
done

echo ""
echo "🐳 2. Verificando conflictos de containers..."
echo "-----------------------------------------------------------"

if command -v docker &> /dev/null; then
    CONTAINERS=("uns-kobetsu-backend" "uns-kobetsu-frontend" "uns-kobetsu-db" "uns-kobetsu-redis" "uns-kobetsu-adminer")

    for CONTAINER in "${CONTAINERS[@]}"; do
        if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "^${CONTAINER}$"; then
            STATUS=$(docker inspect --format='{{.State.Status}}' "$CONTAINER" 2>/dev/null)
            if [ "$STATUS" = "running" ]; then
                echo "⚠️  Container $CONTAINER ya existe y está RUNNING"
                echo "   → Ejecutar: docker stop $CONTAINER"
                WARNINGS=$((WARNINGS + 1))
            else
                echo "ℹ️  Container $CONTAINER existe pero está detenido (OK)"
            fi
        else
            echo "✅ Container $CONTAINER no existe"
        fi
    done
else
    echo "❌ Docker no está instalado o no está en PATH"
    CONFLICTS=$((CONFLICTS + 1))
fi

echo ""
echo "📦 3. Verificando volúmenes..."
echo "-----------------------------------------------------------"

if command -v docker &> /dev/null; then
    VOLUMES=("uns-kobetsu-keiyakusho-postgres-data" "uns-kobetsu-keiyakusho-redis-data" "uns-kobetsu-keiyakusho-outputs")

    for VOLUME in "${VOLUMES[@]}"; do
        if docker volume ls --format '{{.Name}}' 2>/dev/null | grep -q "^${VOLUME}$"; then
            SIZE=$(docker system df -v 2>/dev/null | grep "$VOLUME" | awk '{print $3}' || echo "unknown")
            echo "ℹ️  Volumen $VOLUME existe (tamaño: $SIZE)"
            echo "   → Normal si la app ya corrió antes"
        else
            echo "✅ Volumen $VOLUME no existe (se creará automáticamente)"
        fi
    done
fi

echo ""
echo "🌐 4. Verificando red..."
echo "-----------------------------------------------------------"

if command -v docker &> /dev/null; then
    if docker network ls --format '{{.Name}}' 2>/dev/null | grep -q "^uns-kobetsu-keiyakusho-network$"; then
        echo "ℹ️  Red uns-kobetsu-keiyakusho-network existe"
        echo "   → Se reutilizará"
    else
        echo "✅ Red no existe (se creará automáticamente)"
    fi
fi

echo ""
echo "💾 5. Verificando espacio en disco..."
echo "-----------------------------------------------------------"

if command -v df &> /dev/null; then
    DISK_USAGE=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')
    DISK_AVAILABLE=$(df -h . | tail -1 | awk '{print $4}')

    echo "   Disponible: $DISK_AVAILABLE"

    if [ "$DISK_USAGE" -gt 90 ]; then
        echo "❌ Disco casi lleno (${DISK_USAGE}% usado)"
        CONFLICTS=$((CONFLICTS + 1))
    elif [ "$DISK_USAGE" -gt 80 ]; then
        echo "⚠️  Espacio limitado (${DISK_USAGE}% usado)"
        WARNINGS=$((WARNINGS + 1))
    else
        echo "✅ Espacio suficiente (${DISK_USAGE}% usado)"
    fi
fi

echo ""
echo "🧠 6. Verificando memoria..."
echo "-----------------------------------------------------------"

if command -v free &> /dev/null; then
    MEM_AVAILABLE=$(free -m | awk 'NR==2{print $7}')
    MEM_TOTAL=$(free -m | awk 'NR==2{print $2}')
    MEM_USAGE=$(( 100 - (MEM_AVAILABLE * 100 / MEM_TOTAL) ))

    echo "   Disponible: ${MEM_AVAILABLE}MB / ${MEM_TOTAL}MB"

    if [ "$MEM_AVAILABLE" -lt 512 ]; then
        echo "❌ Memoria insuficiente (<512MB disponible)"
        CONFLICTS=$((CONFLICTS + 1))
    elif [ "$MEM_AVAILABLE" -lt 1024 ]; then
        echo "⚠️  Memoria limitada (<1GB disponible)"
        WARNINGS=$((WARNINGS + 1))
    else
        echo "✅ Memoria suficiente (${MEM_USAGE}% usado)"
    fi
elif command -v vm_stat &> /dev/null; then
    # macOS
    echo "ℹ️  Sistema macOS detectado"
    VM_FREE=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
    VM_TOTAL=$(sysctl -n hw.memsize)
    MEM_AVAILABLE=$(( VM_FREE * 4096 / 1024 / 1024 ))
    echo "   Disponible: ~${MEM_AVAILABLE}MB"

    if [ "$MEM_AVAILABLE" -lt 512 ]; then
        echo "⚠️  Memoria podría ser insuficiente"
        WARNINGS=$((WARNINGS + 1))
    else
        echo "✅ Memoria parece suficiente"
    fi
fi

echo ""
echo "================================================================"
echo "  RESUMEN"
echo "================================================================"
echo ""

if [ $CONFLICTS -gt 0 ]; then
    echo "🚨 CONFLICTOS CRÍTICOS: $CONFLICTS"
    echo ""
    echo "Acciones sugeridas:"
    echo "  1. Detener containers en conflicto: docker stop <container>"
    echo "  2. Liberar puertos ocupados: kill <PID>"
    echo "  3. Cambiar puertos en .env: ./scripts/change-ports.sh"
    echo "  4. Buscar puertos libres: ./scripts/find-free-ports.sh"
    echo ""
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo "⚠️  ADVERTENCIAS: $WARNINGS"
    echo ""
    echo "Se puede proceder pero revisa las advertencias."
    echo ""
    exit 0
else
    echo "✅ TODO OK - No hay conflictos detectados"
    echo ""
    echo "Seguro para iniciar con:"
    echo "  docker-compose up -d"
    echo ""
    exit 0
fi
