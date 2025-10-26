# Vivero Rocío - Sistema de Gestión v2.0

## 📦 Instalación y Configuración

### Requisitos Previos
- Python 3.11.0 o superior
- PostgreSQL 12+ (producción) o SQLite (desarrollo)
- pip (gestor de paquetes de Python)

---

## 🚀 Instalación

### 1. Extraer el archivo
```bash
unzip vivero_rocio_optimizado.zip
cd vivero_rocio
```

### 2. Crear entorno virtual
```bash
python -m venv venv

# En Windows:
venv\Scripts\activate

# En Linux/Mac:
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

**Para Desarrollo (SQLite):**
```bash
# No requiere configuración adicional
# El sistema creará automáticamente data/vivero.db
```

**Para Producción (PostgreSQL):**
```bash
# Crear archivo .env en la raíz del proyecto
echo "DATABASE_URL=postgresql://usuario:password@host:5432/nombre_bd" > .env
```

### 5. Ejecutar migraciones
```bash
# Las migraciones se ejecutan automáticamente al iniciar la aplicación
# Para forzar recreación (SOLO DESARROLLO):
# Editar main.py línea 23: ensure_schema(force_recreate=True)
```

### 6. Iniciar la aplicación
```bash
python main.py
```

La aplicación se abrirá automáticamente en el navegador en:
```
http://localhost:8550
```

---

## 🔐 Credenciales por Defecto

```
Usuario: admin
Contraseña: admin123
```

**⚠️ IMPORTANTE:** Cambiar la contraseña del administrador después del primer inicio.

---

## 📁 Estructura del Proyecto

```
vivero_rocio/
├── main.py                      # Punto de entrada
├── requirements.txt             # Dependencias
├── render.yaml                  # Configuración de deployment
│
├── modules/                     # Módulos principales
│   ├── config.py               # Configuración centralizada
│   ├── utils.py                # Utilidades compartidas
│   ├── db_service.py           # Servicio de base de datos
│   ├── session_service.py      # Gestión de sesiones
│   ├── auth_service.py         # Autenticación
│   ├── migrations_new.py       # Sistema de migraciones
│   │
│   ├── dashboard.py            # Panel de control
│   ├── productos.py            # Gestión de productos
│   ├── clientes.py             # Gestión de clientes
│   ├── proveedores.py          # Gestión de proveedores
│   ├── pedidos.py              # Gestión de pedidos
│   ├── ventas.py               # Punto de venta
│   ├── reportes.py             # Sistema de reportes
│   └── usuarios.py             # Gestión de usuarios
│
├── tests/                       # Tests unitarios
│   ├── test_utils.py
│   ├── test_db_service.py
│   ├── test_auth.py
│   └── test_session.py
│
├── assets/                      # Recursos visuales
├── reportes/                    # Reportes generados (PDF)
├── tickets/                     # Tickets de venta (PDF)
│
├── ANALISIS_MODULOS.md         # Análisis técnico completo
└── MIGRACION_RESUMEN.md        # Resumen de migración
```

---

## 🧪 Ejecutar Tests

```bash
# Todos los tests
pytest tests/ -v

# Con cobertura
pytest tests/ -v --cov=modules --cov-report=html

# Test específico
pytest tests/test_utils.py -v
```

---

## 🔧 Configuración

### Configuración de Colores y Estilos
Editar: `modules/config.py`

### Configuración de Base de Datos
- **Desarrollo:** SQLite automático en `data/vivero.db`
- **Producción:** PostgreSQL via variable `DATABASE_URL`

### Configuración de Puerto
```bash
# Variable de entorno
export PORT=8550

# O editar main.py línea 49
```

---

## 📊 Módulos del Sistema

### 1. Dashboard
- KPIs en tiempo real
- Ventas totales
- Pedidos pendientes/entregados
- Clientes activos
- Productos con stock bajo

### 2. Productos
- Catálogo completo
- Control de stock
- Precios de compra/venta
- Categorías
- Alertas de stock mínimo

### 3. Clientes
- Base de datos de clientes
- Información de contacto
- Integración con WhatsApp
- Historial de compras

### 4. Proveedores
- Gestión de proveedores
- Información de contacto
- Integración con WhatsApp

### 5. Pedidos
- Registro de pedidos
- Seguimiento de estado
- Costo de delivery
- Generación de PDFs

### 6. Ventas (Punto de Venta)
- Carrito de compras
- Métodos de pago múltiples
- Descuentos
- Sesiones de caja
- Generación de tickets

### 7. Reportes
- Reportes de ventas
- Reportes de pedidos
- Reportes de clientes
- Reportes de productos
- Productos más vendidos
- Clientes frecuentes
- Exportación a PDF

### 8. Usuarios
- Gestión de usuarios
- 4 roles: Administrador, Gerente, Vendedor, Usuario
- Sistema de permisos granular
- Control por módulo y acción

---

## 🔒 Sistema de Permisos

### Roles Disponibles:

#### Administrador
- Acceso total a todos los módulos
- Todas las acciones (ver, crear, editar, eliminar)

#### Gerente
- Acceso a todos los módulos
- Limitaciones en eliminación según configuración

#### Vendedor
- Acceso a: Ventas, Pedidos, Clientes, Productos (solo lectura)
- Puede crear ventas y pedidos

#### Usuario
- Acceso básico según permisos asignados

### Configurar Permisos:
1. Ingresar como Administrador
2. Ir a módulo "Usuarios"
3. Editar usuario
4. Configurar permisos por módulo

---

## 🚀 Deployment en Render

### 1. Crear cuenta en Render.com

### 2. Crear PostgreSQL Database
- Nombre: `viverodb`
- Plan: Free o Starter
- Copiar la URL de conexión

### 3. Crear Web Service
- Repository: Conectar con GitHub
- Branch: `claude/comprehensive-project-audit-011CUUTELyVTRuc2coBkN17V`
- Build Command: `pip install -r requirements.txt`
- Start Command: `python main.py`

### 4. Configurar Variables de Entorno
```
DATABASE_URL = [URL de PostgreSQL copiada]
PYTHON_VERSION = 3.11.0
PORT = 8550
```

### 5. Deploy
- Render detectará el `render.yaml` automáticamente
- El deployment se ejecutará automáticamente

---

## 📖 Documentación Adicional

### Reportes Técnicos:
- **`ANALISIS_MODULOS.md`**: Análisis completo de la auditoría técnica
- **`MIGRACION_RESUMEN.md`**: Resumen detallado de la migración

### Código:
- Todos los módulos están documentados con docstrings
- Código limpio y comentado
- Patrones consistentes

---

## 🛠️ Solución de Problemas

### Error: "No se encontró DATABASE_URL"
**Solución:** El sistema usará SQLite por defecto en desarrollo. Para producción, configurar variable de entorno.

### Error: "Error al ejecutar migraciones"
**Solución:** Verificar que PostgreSQL esté corriendo y la URL de conexión sea correcta.

### Error: "Usuario o contraseña incorrectos"
**Solución:** Usar credenciales por defecto (admin/admin123). Si persiste, verificar que las migraciones se ejecutaron correctamente.

### Error: "No tienes permisos"
**Solución:** Ingresar como Administrador y configurar permisos del usuario.

### La aplicación no se abre en el navegador
**Solución:** Abrir manualmente: `http://localhost:8550`

---

## 📞 Soporte

Para reportar problemas o sugerencias:
- Crear issue en el repositorio de GitHub
- Documentar el error con capturas de pantalla
- Incluir logs de consola

---

## 📝 Notas Importantes

1. **Backup de Base de Datos:** Hacer backups regulares de la base de datos PostgreSQL
2. **Seguridad:** Cambiar contraseña del administrador en producción
3. **Permisos:** Configurar permisos de usuarios según necesidad
4. **Actualizaciones:** Mantener dependencias actualizadas con `pip install --upgrade -r requirements.txt`

---

## ✅ Checklist de Instalación

- [ ] Python 3.11+ instalado
- [ ] Entorno virtual creado y activado
- [ ] Dependencias instaladas
- [ ] Variables de entorno configuradas (si aplica)
- [ ] Aplicación iniciada exitosamente
- [ ] Login con credenciales por defecto funcional
- [ ] Contraseña de administrador cambiada
- [ ] Permisos de usuarios configurados
- [ ] Backup configurado (producción)

---

## 🎉 ¡Listo para Usar!

El sistema está completamente funcional y optimizado para producción.

**Versión:** 2.0.0
**Última actualización:** 2025-10-26
**Estado:** ✅ Producción Ready

---

🤖 Sistema optimizado por Claude Code
