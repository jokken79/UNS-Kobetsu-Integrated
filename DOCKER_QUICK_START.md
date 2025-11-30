# Docker Quick Start - UNS Kobetsu

Guía rápida de 5 minutos para gestionar la infraestructura Docker.

---

## ⚡ Inicio en 30 Segundos

```bash
# 1. Verificar conflictos
./scripts/check-conflicts.sh

# 2. Iniciar aplicación
./scripts/kobetsu.sh up

# 3. Abrir navegador
# Frontend:  http://localhost:3010
# API Docs:  http://localhost:8010/docs
# Adminer:   http://localhost:8090
```

**¿Puerto ocupado?** → `./scripts/change-ports.sh`

---

## 📋 Comandos Esenciales

### Gestión Básica

```bash
# INICIAR
./scripts/kobetsu.sh up

# VER LOGS
./scripts/kobetsu.sh logs          # Todos
./scripts/kobetsu.sh logs backend  # Solo backend

# DETENER
./scripts/kobetsu.sh down

# REINICIAR
./scripts/kobetsu.sh restart

# ESTADO
./scripts/kobetsu.sh status
```

### Backup & Restore

```bash
# BACKUP
./scripts/kobetsu.sh backup

# RESTAURAR
./scripts/kobetsu.sh restore backups/latest.sql.gz
```

### Debugging

```bash
# SHELL EN CONTAINER
./scripts/kobetsu.sh shell backend   # Bash en backend
./scripts/kobetsu.sh shell frontend  # Sh en frontend
./scripts/kobetsu.sh shell db        # Sh en PostgreSQL

# VERIFICAR CONFLICTOS
./scripts/kobetsu.sh check

# VER PUERTOS
./scripts/kobetsu.sh ports
```

---

## 🔧 Resolución Rápida de Problemas

### Puerto Ocupado

```bash
# 1. Identificar conflicto
./scripts/check-conflicts.sh

# 2. Cambiar puerto
./scripts/change-ports.sh

# 3. Reiniciar
./scripts/kobetsu.sh restart
```

### Container No Inicia

```bash
# 1. Ver logs
./scripts/kobetsu.sh logs backend

# 2. Reiniciar servicios
./scripts/kobetsu.sh down
./scripts/kobetsu.sh up

# 3. Reconstruir si hay cambios en código
./scripts/kobetsu.sh down
./scripts/kobetsu.sh build
./scripts/kobetsu.sh up
```

### Base de Datos Corrupta

```bash
# Restaurar último backup
./scripts/kobetsu.sh restore backups/latest.sql.gz
```

### Limpieza Completa

```bash
# CUIDADO: Elimina todo (containers, volumes, images)
./scripts/kobetsu.sh clean

# Reiniciar desde cero
./scripts/kobetsu.sh up --build
```

---

## 🌐 URLs de Acceso

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| **Frontend** | http://localhost:3010 | - |
| **Backend API** | http://localhost:8010/api/v1 | JWT token |
| **API Docs** | http://localhost:8010/docs | - |
| **Adminer** | http://localhost:8090 | Ver abajo ↓ |

### Adminer (DB UI)

```
Sistema:   PostgreSQL
Servidor:  uns-kobetsu-db
Usuario:   kobetsu_admin
Password:  (ver archivo .env)
Database:  kobetsu_db
```

---

## 📚 Documentación Completa

- **Scripts:** `/home/user/UNS-Kobetsu-Integrated/scripts/README.md`
- **Análisis Docker:** `/home/user/UNS-Kobetsu-Integrated/DOCKER_ANALYSIS.md`
- **Proyecto:** `/home/user/UNS-Kobetsu-Integrated/CLAUDE.md`

---

## 🆘 Ayuda

```bash
# Ver todos los comandos
./scripts/kobetsu.sh help

# Ver este archivo
cat DOCKER_QUICK_START.md
```

---

**Tip:** Agrega alias a tu `.bashrc` para acceso rápido:

```bash
alias kobetsu='/home/user/UNS-Kobetsu-Integrated/scripts/kobetsu.sh'

# Uso:
# kobetsu up
# kobetsu logs
# kobetsu down
```
