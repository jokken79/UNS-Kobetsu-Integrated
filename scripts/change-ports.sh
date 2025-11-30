#!/bin/bash
# Cambiar puertos de UNS Kobetsu de forma interactiva

set -e

cd "$(dirname "$0")/.."

ENV_FILE=".env"

echo "================================================================"
echo "  Configurador de Puertos - UNS Kobetsu"
echo "================================================================"
echo ""

# Verificar que existe .env
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Archivo .env no encontrado"
    echo ""
    echo "Crear desde plantilla:"
    echo "  cp .env.example .env"
    echo ""
    exit 1
fi

# Función para validar puerto
validate_port() {
    local port=$1
    local service=$2

    # Validar formato numérico
    if [[ ! $port =~ ^[0-9]+$ ]]; then
        echo "❌ Puerto inválido: debe ser un número"
        return 1
    fi

    # Validar rango
    if [ $port -lt 1024 ] || [ $port -gt 65535 ]; then
        echo "❌ Puerto fuera de rango (debe ser 1024-65535)"
        return 1
    fi

    # Verificar si está ocupado
    if command -v lsof &> /dev/null; then
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo "⚠️  Puerto $port está OCUPADO:"
            lsof -Pi :$port -sTCP:LISTEN | tail -n +2 | awk '{printf "   Proceso: %s (PID: %s)\n", $1, $2}'
            read -p "   ¿Usar de todas formas? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                return 1
            fi
        fi
    fi

    return 0
}

# Función para actualizar puerto en .env
update_port() {
    local key=$1
    local value=$2

    if grep -q "^${key}=" "$ENV_FILE"; then
        # Actualizar valor existente
        sed -i.bak "s/^${key}=.*/${key}=${value}/" "$ENV_FILE"
    else
        # Agregar nuevo valor
        echo "${key}=${value}" >> "$ENV_FILE"
    fi
}

# Función para leer puerto actual
get_current_port() {
    local key=$1
    local default=$2

    local value=$(grep "^${key}=" "$ENV_FILE" 2>/dev/null | cut -d= -f2)
    echo "${value:-$default}"
}

echo "📝 Configuración actual:"
echo "-----------------------------------------------------------"
echo "  Frontend:   $(get_current_port KOBETSU_FRONTEND_PORT 3010)"
echo "  Backend:    $(get_current_port KOBETSU_BACKEND_PORT 8010)"
echo "  Adminer:    $(get_current_port KOBETSU_ADMINER_PORT 8090)"
echo "  PostgreSQL: $(get_current_port KOBETSU_DB_PORT 5442)"
echo "  Redis:      $(get_current_port KOBETSU_REDIS_PORT 6389)"
echo ""
echo "Presiona Enter para mantener el puerto actual"
echo "================================================================"
echo ""

# Configurar cada puerto
UPDATED=0

# Frontend
CURRENT_FRONTEND=$(get_current_port KOBETSU_FRONTEND_PORT 3010)
read -p "🌐 Frontend (actual: $CURRENT_FRONTEND): " NEW_FRONTEND
if [ -n "$NEW_FRONTEND" ] && [ "$NEW_FRONTEND" != "$CURRENT_FRONTEND" ]; then
    if validate_port "$NEW_FRONTEND" "Frontend"; then
        update_port "KOBETSU_FRONTEND_PORT" "$NEW_FRONTEND"
        update_port "FRONTEND_URL" "http://localhost:${NEW_FRONTEND}"
        # Actualizar ALLOWED_ORIGINS
        update_port "ALLOWED_ORIGINS" "http://localhost:${NEW_FRONTEND},http://127.0.0.1:${NEW_FRONTEND}"
        echo "   ✅ Frontend actualizado: $CURRENT_FRONTEND → $NEW_FRONTEND"
        UPDATED=$((UPDATED + 1))
    else
        echo "   ❌ Puerto no cambiado"
    fi
fi

# Backend
CURRENT_BACKEND=$(get_current_port KOBETSU_BACKEND_PORT 8010)
read -p "⚡ Backend (actual: $CURRENT_BACKEND): " NEW_BACKEND
if [ -n "$NEW_BACKEND" ] && [ "$NEW_BACKEND" != "$CURRENT_BACKEND" ]; then
    if validate_port "$NEW_BACKEND" "Backend"; then
        update_port "KOBETSU_BACKEND_PORT" "$NEW_BACKEND"
        update_port "NEXT_PUBLIC_API_URL" "http://localhost:${NEW_BACKEND}/api/v1"
        echo "   ✅ Backend actualizado: $CURRENT_BACKEND → $NEW_BACKEND"
        UPDATED=$((UPDATED + 1))
    else
        echo "   ❌ Puerto no cambiado"
    fi
fi

# Adminer
CURRENT_ADMINER=$(get_current_port KOBETSU_ADMINER_PORT 8090)
read -p "🗃️  Adminer (actual: $CURRENT_ADMINER): " NEW_ADMINER
if [ -n "$NEW_ADMINER" ] && [ "$NEW_ADMINER" != "$CURRENT_ADMINER" ]; then
    if validate_port "$NEW_ADMINER" "Adminer"; then
        update_port "KOBETSU_ADMINER_PORT" "$NEW_ADMINER"
        echo "   ✅ Adminer actualizado: $CURRENT_ADMINER → $NEW_ADMINER"
        UPDATED=$((UPDATED + 1))
    else
        echo "   ❌ Puerto no cambiado"
    fi
fi

# PostgreSQL
CURRENT_DB=$(get_current_port KOBETSU_DB_PORT 5442)
read -p "🐘 PostgreSQL (actual: $CURRENT_DB): " NEW_DB
if [ -n "$NEW_DB" ] && [ "$NEW_DB" != "$CURRENT_DB" ]; then
    if validate_port "$NEW_DB" "PostgreSQL"; then
        update_port "KOBETSU_DB_PORT" "$NEW_DB"
        echo "   ✅ PostgreSQL actualizado: $CURRENT_DB → $NEW_DB"
        UPDATED=$((UPDATED + 1))
    else
        echo "   ❌ Puerto no cambiado"
    fi
fi

# Redis
CURRENT_REDIS=$(get_current_port KOBETSU_REDIS_PORT 6389)
read -p "🔴 Redis (actual: $CURRENT_REDIS): " NEW_REDIS
if [ -n "$NEW_REDIS" ] && [ "$NEW_REDIS" != "$CURRENT_REDIS" ]; then
    if validate_port "$NEW_REDIS" "Redis"; then
        update_port "KOBETSU_REDIS_PORT" "$NEW_REDIS"
        echo "   ✅ Redis actualizado: $CURRENT_REDIS → $NEW_REDIS"
        UPDATED=$((UPDATED + 1))
    else
        echo "   ❌ Puerto no cambiado"
    fi
fi

echo ""
echo "================================================================"

if [ $UPDATED -eq 0 ]; then
    echo "ℹ️  No se realizaron cambios"
else
    echo "✅ Se actualizaron $UPDATED puerto(s)"
    echo "📦 Respaldo guardado en: ${ENV_FILE}.bak"
    echo ""
    echo "Nueva configuración:"
    echo "-----------------------------------------------------------"
    echo "  Frontend:   $(get_current_port KOBETSU_FRONTEND_PORT 3010)"
    echo "  Backend:    $(get_current_port KOBETSU_BACKEND_PORT 8010)"
    echo "  Adminer:    $(get_current_port KOBETSU_ADMINER_PORT 8090)"
    echo "  PostgreSQL: $(get_current_port KOBETSU_DB_PORT 5442)"
    echo "  Redis:      $(get_current_port KOBETSU_REDIS_PORT 6389)"
    echo ""
    echo "================================================================"
    echo ""
    echo "⚠️  IMPORTANTE: Reiniciar containers para aplicar cambios"
    echo ""
    read -p "¿Reiniciar ahora? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔄 Reiniciando containers..."
        docker-compose down
        sleep 2
        docker-compose up -d
        echo "✅ Containers reiniciados con nuevos puertos"
    else
        echo ""
        echo "Reiniciar manualmente con:"
        echo "  docker-compose down && docker-compose up -d"
    fi
fi

echo ""
