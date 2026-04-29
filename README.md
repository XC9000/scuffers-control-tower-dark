# 🚀 Scuffers AI Ops Control Tower
**Entregable Final - UDIA × ESIC Hackathon**

> 🖥️ **Demo en Vivo (Despliegue Full-Stack):** [https://scuffers-control-tower-dark-production.up.railway.app/](https://scuffers-control-tower-dark-production.up.railway.app/)
> 📦 **Repositorio Oficial:** [https://github.com/XC9000/scuffers-control-tower-dark](https://github.com/XC9000/scuffers-control-tower-dark)
## 1. Resumen Ejecutivo
**Scuffers AI Ops Control Tower** es un sistema inteligente diseñado para resolver el caos operativo durante lanzamientos de alta demanda (drops). En lugar de abrumar al equipo con paneles llenos de gráficas estáticas, el sistema ingesta datos imperfectos de múltiples fuentes (inventario, pedidos, atención al cliente, logística) y los transforma en un **Top 10 de acciones quirúrgicas priorizadas**. Responde en tiempo real a la pregunta: *"¿Qué es lo más importante que debe hacer operaciones ahora mismo?"* garantizando la protección de clientes clave (VIP) y la prevención de roturas de stock.

## 2. Enfoque y Arquitectura
Arquitectura **ligera, rápida y libre de fricciones** (sin dependencias pesadas), ideal para despliegues ágiles:

* **Backend Inteligente (Python/Flask):** Motor de reglas y scoring que normaliza datos sucios, unifica SKUs y evalúa el riesgo multivariable. Incluye un simulador predictivo de demanda que proyecta el stock a 2 horas vista.
* **Integración Incremental API:** Se conecta de forma concurrente (mediante `ThreadPoolExecutor`) a una API logística externa para enriquecer el score, con degradación elegante (*graceful degradation*) si falla, asegurando que la carga del dashboard sea siempre < 1s.
* **Frontend Glassmorphism (HTML/JS/CSS):** Interfaz orientada a operarios de alta presión. Dark mode profesional, animaciones en tiempo real, terminal visual de carga y estado de los datos.

## 3. Instalación Local
1. Clona el repositorio: `git clone https://github.com/XC9000/scuffers-control-tower-dark.git`
2. Instala las dependencias: `pip install -r requirements.txt`
3. Ejecuta el servidor: `python app.py`
4. Abre el navegador en `http://localhost:8080`

> **O puedes ver la versión ya desplegada en la nube aquí:**
> [https://scuffers-control-tower-dark-production.up.railway.app/](https://scuffers-control-tower-dark-production.up.railway.app/)

## 4. Top 10 Acciones Priorizadas (Heurística del Motor)
El sistema no escupe datos brutos; aplica un modelo de *scoring* dinámico (escala de 0 a 100+) que cruza variables logísticas, de inventario y de atención al cliente para determinar qué requiere intervención humana inmediata. Las acciones priorizadas se centran en:
1. **Protección de Clientes VIP y Leales:** Intervención inmediata ante cualquier riesgo de retraso logístico o retención en aduanas.
2. **Mitigación de Stockouts Críticos:** Reabastecimiento urgente de SKUs con inventario ≤ 2 unidades o un *sell-through* superior al 70%.
3. **Resolución de Tickets Severos:** Escalado automático de incidencias de soporte marcadas como urgentes o que presentan un fuerte sentimiento negativo.
4. **Desbloqueo Financiero:** Revisión prioritaria de pedidos de alto valor (>€120) retenidos por procesos de *payment_review*.
5. **Gestión de Campañas (High Pressure):** Asignación rápida de recursos logísticos cuando las campañas en curso superan los umbrales operativos.

## 5. Limitaciones Conocidas (Trade-offs de Arquitectura)
Con el fin de garantizar una entrega rápida y funcional para este prototipo (MVP), se han asumido ciertas decisiones técnicas que escalarían diferente en un entorno de producción masivo:
* **Ingesta Estática vs Streaming:** Actualmente el motor ingesta *snapshots* mediante archivos CSV locales. En producción, esto se sustituiría por un bus de eventos (ej. Kafka, RabbitMQ) para streaming de datos en tiempo real.
* **Procesamiento de la API Externa:** Para evitar colapsos en la UI, las peticiones a la API de Supabase se realizan en paralelo mediante un `ThreadPoolExecutor` con *timeout* agresivo (2.5s) restringido a las órdenes de mayor prioridad. En un entorno *Enterprise*, este enriquecimiento debería ocurrir de forma asíncrona mediante *background workers* (ej. Celery) que actualicen la base de datos en segundo plano.
* **Control de Accesos (RBAC):** La versión actual es de acceso directo para facilitar la demo. Un entorno productivo requeriría integración con un IdP (Identity Provider) y gestión de roles.
