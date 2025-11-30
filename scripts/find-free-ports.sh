#!/bin/bash
# Encuentra puertos libres alternativos para UNS Kobetsu

set -e

echo "================================================================"
echo "  Buscador de Puertos Libres - UNS Kobetsu"
echo "================================================================"
echo ""

# Función para encontrar puerto libre en un rango
find_free_port() {
    local START=$1
    local END=$2
    local SERVICE=$3

    for PORT in $(seq $START $END); do
        if command -v lsof &> /dev/null; then
            if ! lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
                echo "$PORT"
                return 0
            fi
        elif command -v netstat &> /dev/null; then
            if ! netstat -tuln 2>/dev/null | grep -q ":$PORT "; then
                echo "$PORT"
                return 0
            fi
        else
            # Fallback: intentar conectar al puerto
            if ! timeout 0.1 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/$PORT" 2>/dev/null; then
                echo "$PORT"
                return 0
            fi
        fi
    done

    echo ""
    return 1
}

echo "🔍 Buscando puertos disponibles en rangos óptimos..."
echo ""

# Frontend (rango 3000-3099)
echo -n "Frontend (Next.js)............ "
FRONTEND=$(find_free_port 3010 3099 "Frontend")
if [ -n "$FRONTEND" ]; then
    echo "✅ Puerto $FRONTEND disponible"
else
    echo "❌ No hay puertos libres en rango 3010-3099"
    FRONTEND="3010"
fi

# Backend (rango 8000-8099)
echo -n "Backend (FastAPI)............. "
BACKEND=$(find_free_port 8010 8099 "Backend")
if [ -n "$BACKEND" ]; then
    echo "✅ Puerto $BACKEND disponible"
else
    echo "❌ No hay puertos libres en rango 8010-8099"
    BACKEND="8010"
fi

# Adminer (rango 8080-8199)
echo -n "Adminer (DB UI)............... "
ADMINER=$(find_free_port 8090 8199 "Adminer")
if [ -n "$ADMINER" ]; then
    echo "✅ Puerto $ADMINER disponible"
else
    echo "❌ No hay puertos libres en rango 8090-8199"
    ADMINER="8090"
fi

# PostgreSQL (rango 5400-5499)
echo -n "PostgreSQL (Database)......... "
POSTGRES=$(find_free_port 5442 5499 "PostgreSQL")
if [ -n "$POSTGRES" ]; then
    echo "✅ Puerto $POSTGRES disponible"
else
    echo "❌ No hay puertos libres en rango 5442-5499"
    POSTGRES="5442"
fi

# Redis (rango 6300-6399)
echo -n "Redis (Cache)................. "
REDIS=$(find_free_port 6389 6399 "Redis")
if [ -n "$REDIS" ]; then
    echo "✅ Puerto $REDIS disponible"
else
    echo "❌ No hay puertos libres en rango 6389-6399"
    REDIS="6389"
fi

echo ""
echo "================================================================"
echo "  CONFIGURACIÓN SUGERIDA PARA .env"
echo "================================================================"
echo ""

cat << EOF
# Puertos (puertos libres encontrados)
KOBETSU_FRONTEND_PORT=$FRONTEND
KOBETSU_BACKEND_PORT=$BACKEND
KOBETSU_ADMINER_PORT=$ADMINER
KOBETSU_DB_PORT=$POSTGRES
KOBETSU_REDIS_PORT=$REDIS

# URLs (actualizar según puertos)
FRONTEND_URL=http://localhost:$FRONTEND
NEXT_PUBLIC_API_URL=http://localhost:$BACKEND/api/v1
ALLOWED_ORIGINS=http://localhost:$FRONTEND,http://127.0.0.1:$FRONTEND
EOF

echo ""
echo "================================================================"
echo ""
echo "💡 Opciones:"
echo "  1. Copiar las líneas de arriba a tu archivo .env"
echo "  2. Usar el script interactivo: ./scripts/change-ports.sh"
echo "  3. Editar .env manualmente"
echo ""
echo "Después de actualizar .env:"
echo "  docker-compose down"
echo "  docker-compose up -d"
echo ""
