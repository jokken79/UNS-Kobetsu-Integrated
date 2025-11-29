#!/bin/bash

# =================================================
# UNS Kobetsu - Script de Inicialización Local
# =================================================

set -e  # Exit on error

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}🚀 Inicializando UNS-Kobetsu para uso local...${NC}"
echo -e "${GREEN}==================================================${NC}"

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker no está instalado${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker daemon no está ejecutándose${NC}"
    exit 1
fi

# Construir e iniciar servicios
echo -e "${YELLOW}📦 Construyendo imágenes Docker...${NC}"
docker compose build

echo -e "${YELLOW}🚀 Iniciando servicios...${NC}"
docker compose up -d

# Esperar a que la base de datos esté lista
echo -e "${YELLOW}⏳ Esperando a que la base de datos esté lista...${NC}"

# Contador para timeout
counter=0
max_attempts=30

while [ $counter -lt $max_attempts ]; do
    if docker exec uns-kobetsu-db pg_isready -U kobetsu_admin &> /dev/null; then
        echo -e "${GREEN}✅ Base de datos lista${NC}"
        break
    fi
    counter=$((counter + 1))
    if [ $counter -eq $max_attempts ]; then
        echo -e "${RED}❌ Timeout esperando la base de datos${NC}"
        exit 1
    fi
    echo -n "."
    sleep 2
done
echo ""

# Esperar un poco más para asegurar que el backend esté listo
echo -e "${YELLOW}⏳ Esperando a que el backend esté listo...${NC}"
sleep 5

# Aplicar migraciones
echo -e "${YELLOW}📊 Aplicando migraciones de base de datos...${NC}"
if docker exec uns-kobetsu-backend alembic upgrade head; then
    echo -e "${GREEN}✅ Migraciones aplicadas exitosamente${NC}"
else
    echo -e "${RED}❌ Error aplicando migraciones${NC}"
    echo -e "${YELLOW}Intentando verificar el estado actual...${NC}"
    docker exec uns-kobetsu-backend alembic current
fi

# Crear usuario admin si no existe
echo -e "${YELLOW}👤 Creando usuario administrador...${NC}"
if docker exec uns-kobetsu-backend python scripts/create_admin.py 2>/dev/null; then
    echo -e "${GREEN}✅ Usuario admin creado${NC}"
else
    echo -e "${YELLOW}⚠️  Usuario admin ya existe o no se pudo crear${NC}"
fi

# Verificar estado de servicios
echo -e "${YELLOW}🔍 Verificando estado de servicios...${NC}"
docker compose ps

# Obtener URLs
BACKEND_URL="http://localhost:8010"
FRONTEND_URL="http://localhost:3010"
API_DOCS_URL="http://localhost:8010/docs"
ADMINER_URL="http://localhost:8090"

# Verificar que los servicios respondan
echo -e "${YELLOW}🔍 Verificando disponibilidad de servicios...${NC}"

# Backend health check
if curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health" | grep -q "200"; then
    echo -e "${GREEN}✅ Backend disponible${NC}"
else
    echo -e "${YELLOW}⚠️  Backend todavía iniciando...${NC}"
fi

# Mostrar información final
echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}✅ ¡Inicialización completada!${NC}"
echo -e "${GREEN}==================================================${NC}"
echo ""
echo -e "📋 ${GREEN}Credenciales de acceso:${NC}"
echo -e "   Usuario: ${YELLOW}admin${NC}"
echo -e "   Password: ${YELLOW}admin123${NC}"
echo ""
echo -e "🌐 ${GREEN}URLs de acceso:${NC}"
echo -e "   Frontend: ${YELLOW}$FRONTEND_URL${NC}"
echo -e "   Backend API Docs: ${YELLOW}$API_DOCS_URL${NC}"
echo -e "   Adminer (DB UI): ${YELLOW}$ADMINER_URL${NC}"
echo ""
echo -e "📊 ${GREEN}Base de datos:${NC}"
echo -e "   Host: ${YELLOW}localhost:5442${NC}"
echo -e "   Database: ${YELLOW}kobetsu_db${NC}"
echo -e "   User: ${YELLOW}kobetsu_admin${NC}"
echo -e "   Password: ${YELLOW}CHANGE_THIS_IN_PRODUCTION${NC}"
echo ""
echo -e "🔧 ${GREEN}Comandos útiles:${NC}"
echo -e "   Ver logs: ${YELLOW}docker compose logs -f${NC}"
echo -e "   Detener: ${YELLOW}docker compose down${NC}"
echo -e "   Reiniciar: ${YELLOW}docker compose restart${NC}"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANTE: Cambia las contraseñas antes de usar en producción${NC}"