#!/bin/bash
# Wrapper seguro para docker-compose de UNS Kobetsu

set -e

cd "$(dirname "$0")/.."

COMPOSE_FILE="docker-compose.yml"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar uso
show_usage() {
    cat << EOF
Uso: $0 {comando} [opciones]

COMANDOS:
  up, start       Iniciar todos los servicios (con verificación de conflictos)
  down, stop      Detener todos los servicios
  restart         Reiniciar todos los servicios
  logs [servicio] Ver logs (todos o de un servicio específico)
  status, ps      Ver estado de containers
  build           Reconstruir imágenes
  clean           Limpiar containers, volúmenes e imágenes
  backup          Crear backup de la base de datos
  restore <file>  Restaurar backup de la base de datos
  check           Verificar conflictos sin iniciar
  ports           Mostrar puertos configurados
  shell <service> Abrir shell en un container

EJEMPLOS:
  $0 up              # Iniciar con verificación
  $0 logs backend    # Ver logs del backend
  $0 restart         # Reiniciar todo
  $0 shell backend   # Bash en backend container
  $0 backup          # Backup de PostgreSQL

EOF
}

# Función para verificar que Docker está disponible
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker no está instalado${NC}"
        exit 1
    fi

    if ! docker ps &> /dev/null; then
        echo -e "${RED}❌ Docker daemon no está corriendo${NC}"
        exit 1
    fi
}

# Función para mostrar configuración de puertos
show_ports() {
    if [ -f .env ]; then
        export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
    fi

    cat << EOF
================================================================
  CONFIGURACIÓN DE PUERTOS - UNS Kobetsu
================================================================

  🌐 Frontend (Next.js):    http://localhost:${KOBETSU_FRONTEND_PORT:-3010}
  ⚡ Backend (FastAPI):     http://localhost:${KOBETSU_BACKEND_PORT:-8010}
  📚 API Docs:              http://localhost:${KOBETSU_BACKEND_PORT:-8010}/docs
  🗃️  Adminer (DB UI):      http://localhost:${KOBETSU_ADMINER_PORT:-8090}
  🐘 PostgreSQL:            localhost:${KOBETSU_DB_PORT:-5442}
  🔴 Redis:                 localhost:${KOBETSU_REDIS_PORT:-6389}

================================================================
EOF
}

# Verificar Docker
check_docker

# Procesar comando
case "$1" in
    up|start)
        echo -e "${BLUE}🔍 Verificando conflictos...${NC}"
        if bash scripts/check-conflicts.sh; then
            echo ""
            echo -e "${GREEN}🚀 Iniciando UNS Kobetsu...${NC}"
            docker-compose up -d "${@:2}"
            echo ""
            echo -e "${GREEN}✅ Servicios iniciados${NC}"
            echo ""
            show_ports
        else
            echo ""
            echo -e "${RED}🚨 Se encontraron conflictos${NC}"
            echo ""
            echo -e "${YELLOW}💡 Sugerencias:${NC}"
            echo "   1. Detener otros containers: docker stop <container>"
            echo "   2. Cambiar puertos: ./scripts/change-ports.sh"
            echo "   3. Buscar puertos libres: ./scripts/find-free-ports.sh"
            echo "   4. Forzar inicio: docker-compose up -d"
            exit 1
        fi
        ;;

    down|stop)
        echo -e "${YELLOW}🛑 Deteniendo UNS Kobetsu...${NC}"
        docker-compose down
        echo -e "${GREEN}✅ Servicios detenidos${NC}"
        ;;

    restart)
        echo -e "${YELLOW}🔄 Reiniciando UNS Kobetsu...${NC}"
        docker-compose down
        sleep 2
        bash scripts/check-conflicts.sh && docker-compose up -d
        echo -e "${GREEN}✅ Servicios reiniciados${NC}"
        echo ""
        show_ports
        ;;

    logs)
        if [ -n "$2" ]; then
            echo -e "${BLUE}📋 Logs de $2...${NC}"
            docker-compose logs -f "$2"
        else
            echo -e "${BLUE}📋 Logs de todos los servicios...${NC}"
            docker-compose logs -f
        fi
        ;;

    status|ps)
        echo -e "${BLUE}📊 Estado de containers:${NC}"
        echo ""
        docker-compose ps
        ;;

    build)
        echo -e "${BLUE}🔨 Reconstruyendo imágenes...${NC}"
        docker-compose build "${@:2}"
        echo -e "${GREEN}✅ Imágenes reconstruidas${NC}"
        ;;

    clean)
        echo -e "${YELLOW}⚠️  ADVERTENCIA: Esto eliminará containers, volúmenes e imágenes${NC}"
        read -p "¿Continuar? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}🧹 Limpiando...${NC}"
            docker-compose down -v
            docker images | grep uns-kobetsu-keiyakusho | awk '{print $3}' | xargs -r docker rmi
            echo -e "${GREEN}✅ Limpieza completada${NC}"
        else
            echo "Operación cancelada"
        fi
        ;;

    backup)
        echo -e "${BLUE}📦 Creando backup...${NC}"
        bash scripts/backup-database.sh
        ;;

    restore)
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Especifica el archivo de backup${NC}"
            echo "Uso: $0 restore <archivo.sql.gz>"
            exit 1
        fi
        echo -e "${BLUE}🔄 Restaurando backup...${NC}"
        bash scripts/restore-database.sh "$2"
        ;;

    check)
        bash scripts/check-conflicts.sh
        ;;

    ports)
        show_ports
        ;;

    shell)
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Especifica el servicio${NC}"
            echo "Servicios disponibles: backend, frontend, db, redis"
            exit 1
        fi

        CONTAINER="uns-kobetsu-$2"
        SHELL_CMD="bash"

        # Usar sh para frontend (Alpine)
        if [ "$2" = "frontend" ] || [ "$2" = "db" ] || [ "$2" = "redis" ]; then
            SHELL_CMD="sh"
        fi

        echo -e "${BLUE}🐚 Abriendo shell en $CONTAINER...${NC}"
        docker exec -it "$CONTAINER" $SHELL_CMD
        ;;

    help|--help|-h)
        show_usage
        ;;

    *)
        echo -e "${RED}❌ Comando no reconocido: $1${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac
