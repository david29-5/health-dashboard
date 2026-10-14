1. Estado Actual y Tecnologías

    Stack tecnológico:

        Backend: Python, FastAPI, SQLite / Turso (Base de datos en la nube), Uvicorn.

        Seguridad: Passlib (Bcrypt) para hash de contraseñas, PyJWT para autenticación por tokens de sesión.

        Integraciones: Librería garminconnect para sincronización de datos biométricos y de actividad.

        Frontend: HTML5, Tailwind CSS (modo oscuro y diseño responsive), JavaScript vainilla, Chart.js para visualización de gráficas semanales.

    Estructura del proyecto:

        main.py: Punto de entrada del servidor FastAPI, inicialización de base de datos y registro de routers.

        database/db.py: Conexión centralizada a la base de datos SQLite/Turso.

        routers/:

            auth_routes.py: Gestión de registro, inicio de sesión seguro y vinculación de credenciales de Garmin por usuario.

            dashboard_routes.py: Lógica del balance diario, histórico de 7 días y control de gasto manual/entrenamientos.

        services/garmin_service.py: Gestión multiusuario de sesiones de Garmin, caché local (garmin_cache_v2) y sincronización asíncrona en segundo plano (BackgroundTasks).

        index.html: Interfaz completa de la aplicación (vistas de Día y Semana, autenticación, paneles dinámicos y gráficos).

    Qué funciona ya:

        Sistema de Autenticación Multiusuario: Registro con contraseñas seguras cifradas, login con generación de tokens y aislamiento de datos por usuario en la base de datos.

        Balance Diario Inteligente: Cálculo en tiempo real de calorías ingeridas (vía IA), calorías quemadas y balance neto con indicador de estado (Superávit/Déficit).

        Modo Dual (Garmin vs. Manual): Posibilidad de alternar mediante un switch interactivo entre la sincronización automática con el reloj y un modo manual de calorías fijas por día.

        Optimización de Rendimiento: Uso de BackgroundTasks en FastAPI y caché local para permitir cargas instantáneas de la interfaz mientras la sincronización con Garmin corre en segundo plano.

        Histórico y Gráfica Semanal: Visualización comparativa de ingesta y gasto calórico de los últimos 7 días mediante Chart.js.

2. Próximos Pasos Pendientes (Lo que quiero tocar)

    [ ] Tarea 1: Mitigar y gestionar de forma robusta las limitaciones de tasa de peticiones de Garmin (bloqueos HTTP 429 por exceso de logins) optimizando la reutilización de la sesión en disco por usuario.

    [ ] Tarea 2: Extracción automática de actividades granulares desde Garmin (carreras, entrenamientos, etc.) para listarlas y sumarlas automáticamente en el desglose diario.

    [ ] Tarea 3: Pulir la experiencia de usuario (UX) en el panel de configuración de credenciales de Garmin y añadir indicadores visuales de estado de sincronización en segundo plano.

3. Reglas de Código y Estilo

    Mantener el código limpio, comentado y modular (separación clara entre rutas, servicios y base de datos).

    Seguir la estructura y convenciones existentes en los routers y servicios de FastAPI.

    Priorizar la seguridad en el manejo de credenciales externas (encriptación y almacenamiento seguro en base de datos).