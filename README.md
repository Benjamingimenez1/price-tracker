# Price Tracker PRO

Sistema completo de seguimiento de precios con scraping real, base de datos, autenticación y deploy-ready.

---

## Estructura del proyecto

```
price-tracker/
├── app/
│   ├── database/
│   │   ├── models.py        # Tablas: User, Product, PriceHistory
│   │   └── session.py       # Engine SQLite + get_db()
│   ├── routes/
│   │   ├── auth.py          # POST /api/auth/register|login
│   │   ├── products.py      # CRUD + refresh endpoints
│   │   └── deps.py          # Dependencia get_current_user
│   ├── scraper/
│   │   ├── engine.py        # Orquestador requests → selenium
│   │   ├── requests_scraper.py
│   │   ├── selenium_scraper.py
│   │   ├── parsers.py       # MercadoLibre, Amazon, Falabella, genérico
│   │   └── headers.py       # User-agents realistas
│   ├── services/
│   │   ├── product_service.py  # Lógica de negocio
│   │   ├── alert_service.py    # Email SMTP
│   │   └── auth_service.py     # Registro/login/tokens
│   ├── config.py            # Settings con pydantic
│   ├── scheduler.py         # APScheduler — refresh automático
│   └── main.py              # FastAPI app
├── frontend/
│   ├── index.html
│   └── static/
│       ├── css/style.css
│       └── js/app.js
├── requirements.txt
├── .env.example
└── README.md
```

---

## Instalación local

### 1. Clonar y crear entorno virtual

```bash
git clone <tu-repo>
cd price-tracker

python -m venv venv
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus datos (SMTP es opcional para empezar)
```

### 4. Ejecutar

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Abrí `http://localhost:8000` en el navegador.

La documentación interactiva de la API está en `http://localhost:8000/docs`.

---

## API endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/auth/register` | Crear cuenta |
| POST | `/api/auth/login` | Ingresar, devuelve token |
| GET | `/api/products` | Listar productos del usuario |
| POST | `/api/products` | Agregar producto (scraping inmediato) |
| POST | `/api/products/{id}/refresh` | Actualizar precio ahora |
| GET | `/api/products/{id}/history` | Historial de precios |
| DELETE | `/api/products/{id}` | Eliminar producto |

Todos los endpoints de productos requieren header: `Authorization: Bearer <token>`

---

## Configurar alertas por email (opcional)

En `.env`:

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx   # App Password de Google
ALERT_FROM_EMAIL=tu@gmail.com
```

Para generar un App Password en Gmail:
1. Ir a myaccount.google.com → Seguridad
2. Activar verificación en dos pasos
3. Buscar "Contraseñas de aplicaciones" y generar una

---

## Deploy en Render (gratuito)

### 1. Subir a GitHub

```bash
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/tu-usuario/price-tracker.git
git push -u origin main
```

### 2. Crear servicio en Render

1. Ir a [render.com](https://render.com) → New → Web Service
2. Conectar tu repositorio de GitHub
3. Configurar:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment:** Python 3

4. En "Environment Variables" agregar:
   - `SECRET_KEY` → una cadena larga y aleatoria
   - `SCRAPE_INTERVAL_MINUTES` → `60`
   - (Optionals) variables SMTP

5. Click en "Create Web Service"

Render asigna una URL pública automáticamente del tipo `https://price-tracker-xxxx.onrender.com`.

---

## Deploy en Railway

```bash
# Instalar Railway CLI
npm install -g @railway/cli

railway login
railway init
railway up
```

O desde el dashboard web: [railway.app](https://railway.app) → New Project → Deploy from GitHub repo.

Variables de entorno a configurar:
- `SECRET_KEY`
- `SCRAPE_INTERVAL_MINUTES`
- SMTP si querés emails

---

## Notas sobre el scraping

- **MercadoLibre, Amazon, Falabella** tienen parsers específicos.
- Para cualquier otro sitio se usa el parser **genérico** (meta tags + selectores comunes).
- Si un sitio bloquea requests normales, el sistema hace **fallback automático a Selenium** (requiere Chrome instalado).
- En servidores de deploy sin Chrome, Selenium no funciona — funciona solo con requests.
- Para scraping a escala se recomienda agregar **proxies rotativos** en `headers.py`.

---

## Actualizar a producción real

Para escalar el proyecto a un SaaS real, los próximos pasos son:

1. **Cambiar SQLite por PostgreSQL** — solo cambiar `DATABASE_URL` en `.env`
2. **Agregar proxies rotativos** para evitar bloqueos
3. **Rate limiting** en los endpoints con slowapi
4. **Stripe** para cobrar suscripciones
5. **Redis** para cache y cola de trabajos con Celery

---

## Licencia

MIT — libre para uso personal y comercial.
