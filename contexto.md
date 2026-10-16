# 📊 Health Dashboard - Contexto del Proyecto

## 1. Stack Tecnológico y Estructura
- **Backend:** Python, FastAPI, SQLite / Turso (Base de datos en la nube), Uvicorn.
- **Seguridad:** Passlib (Bcrypt) para contraseñas, PyJWT para tokens de sesión (7 días).
- **Integraciones:** Librería `garminconnect` con caché local multiusuario (`garmin_cache_v2`) y sincronización asíncrona por `BackgroundTasks`.
- **Frontend:** HTML5, Tailwind CSS (modo oscuro, PWA instalable con `manifest.json` y Service Worker `sw.js`), Chart.js.
- **Estructura clave:**
  - `main.py`: Arranque de FastAPI, configuración de rutas estáticas y creación automática de tablas.
  - `database/db.py`: Conexión centralizada a Turso.
  - `routers/`: `auth_routes.py` (login/registro/Garmin), `dashboard_routes.py` (balance, histórico, gasto manual), `nutrition_routes.py` (IA de comidas).
  - `services/garmin_service.py`: Lógica de sesión y descargas en segundo plano protegidas contra bloqueos 429.

## 2. Estado Actual (Lo que ya funciona)
- Sistema completo de autenticación y aislamiento de datos por usuario.
- Balance diario inteligente (Ingeridas vs. Quemadas) con modo dual (Garmin automático vs. Gasto manual diario).
- Gráfica semanal de los últimos 7 días con Chart.js.
- PWA instalable con icono personalizado y Service Worker.

## 3. Próximos Pasos Pendientes (Plan de Trabajo)
- [ ] **Fase 1:** Crear tabla `plantillas_entrenamientos` en Turso y endpoint de IA para generar rutinas predefinidas.
- [ ] **Fase 2:** Dividir la interfaz web con un selector (🍽️ Comidas | 🔥 Entrenos) y añadir la biblioteca de rutinas con botones `[+]`.
- [ ] **Fase 3:** Extraer actividades reales de Garmin con `get_activities_by_date` para listarlas en el día.
- [ ] **Fase 4:** Blindar la suma calórica para que las actividades automáticas de Garmin no dupliquen el total del reloj.


Fase de moejora 🗺️ Plan de Trabajo (4 Fases Súper Eficientes)

Para no romper nada de lo que ya funciona, lo haremos en este orden exacto cuando quieras ponerte manos a la obra:

#### Fase 1: Base de Datos y IA para Plantillas (Backend)

- **Qué haremos:**
    
    1. Crear una tabla nueva muy sencilla en Turso llamada `plantillas_entrenamientos` (`id`, `usuario`, `nombre_corto`, `calorias`).
        
    2. Añadir un endpoint en `nutrition_routes.py` que reciba un texto libre (ej: _"1 hora de calistenia intensa y 15 min de comba"_), le pregunte a la IA cuántas calorías quema eso aproximadamente y le ponga un nombre corto limpio (ej: `"Calistenia + Comba (1h 15m)"`), guardándolo en tus plantillas fijas.
        
    3. Añadir rutas rápidas para **listar** tus plantillas y **borrar** alguna si te cansas de ella.
        

#### Fase 2: La Interfaz Dual Comidas / Entrenos (Frontend)

- **Qué haremos:**
    
    1. Eliminar el botón antiguo de Boxeo y separar la lista actual (que ahora mismo mezcla comidas y entrenos en el mismo cajón) en dos vistas independientes controladas por un selector arriba: **[ 🍽️ Comidas | 🔥 Entrenos ]**.
        
    2. En la vista de **Entrenos**, pondremos dos bloques:
        
        - **Arriba (Tus Rutinas Fijas):** Tus botones rápidos creados por ti con un botón `[+]` (que al pulsarlo lo añade al día actual) y un desplegable `"✨ Crear nueva rutina con IA"`.
            
        - **Abajo (Entrenamientos de Hoy):** La lista de lo que has hecho en la fecha seleccionada.
            

#### Fase 3: El "Blindaje" de Calorías y Sincronización de Actividades Garmin

- **Qué haremos:**
    
    1. En `garmin_service.py`, aprovechando el viaje que ya hace el "minion" en segundo plano (una vez pase el bloqueo 429), añadiremos una sola línea: `client.get_activities_by_date(fecha_iso, fecha_iso)`.
        
    2. Eso nos devuelve una lista con las actividades que hayas grabado con el reloj ese día (nombre, tipo de deporte y calorías).
        
    3. Las guardaremos en tu tabla `registro_entrenamientos` pero con un prefijo o columna especial (por ejemplo, empezando por `"⌚ [Garmin] "`) y evitando duplicados si recargas la página.
        

#### Fase 4: Ajuste de la Fórmula en `dashboard_routes.py`

- **Qué haremos:**
    
    1. Ajustar la suma de calorías en el servidor para que sea 100% inteligente:
        
        - **Si estás en Modo Garmin:** `Quemadas = Total_Reloj_Garmin + Entrenos_Manuales_Del_Dia` _(ignorando en la suma los que tengan la etiqueta `⌚ [Garmin]`, que solo se envían a la web para que los veas en la lista)_.
            
        - **Si estás en Modo Manual:** `Quemadas = Base_Manual_Dia + Todos_Los_Entrenos_Del_Dia`.