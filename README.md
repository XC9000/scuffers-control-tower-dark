# 🚀 Scuffers AI Ops Control Tower
**Entregable Final - UDIA × ESIC Hackathon**

> 🖥️ **Demo en Vivo (Despliegue Full-Stack Recomendado):** [https://scuffers-control-tower-dark-production.up.railway.app/](https://scuffers-control-tower-dark-production.up.railway.app/)
> 📦 **Repositorio Oficial:** [https://github.com/XC9000/scuffers-control-tower-dark](https://github.com/XC9000/scuffers-control-tower-dark)
> 
> *<small>💡 **Nota del desarrollador:** Existe una [Versión Light (Frontend-only)](https://xc9000.github.io/scuffers-ai-ops-control-tower/) publicada en GitHub Pages ([Repo Alternativo](https://github.com/XC9000/scuffers-ai-ops-control-tower)). Sin embargo, **se recomienda evaluar y puntuar esta versión Full-Stack (Dark)**, ya que es la original y la única que contiene todo el cerebro backend en Python y la integración concurrente real con la API logística que exige el hackathon.</small>*
## 1. Resumen Ejecutivo
**Scuffers AI Ops Control Tower** es una capa de inteligencia operativa construida sobre un stack basado en Python, automatización y agentes, que integra múltiples fuentes de datos —CSV operativos, señales de negocio y estado logístico en tiempo real vía API— para orquestar decisiones durante lanzamientos de alta demanda.

La arquitectura combina pipelines de datos ligeros, lógica de scoring interpretable y agentes automatizados que priorizan riesgos, generan acciones y mantienen el flujo operativo sin intervención manual constante.

El sistema no solo consolida información, sino que la transforma en decisiones ejecutables, adaptándose dinámicamente con nuevas señales como el estado de *shipping*, para reforzar la capacidad del equipo de operaciones en escenarios de máxima presión.

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

## 4. Top 10 Acciones Priorizadas (Ejemplos del Dashboard)
En lugar de mostrar gráficos estáticos, el algoritmo cruza las variables de todas las fuentes y escupe literalmente el **Top 10 de cosas que el equipo de Operaciones debe hacer YA**. Ejemplos de las acciones que genera la torre de control:

1. **Atender Pedido ORD-XXXXX (VIP):** Cliente VIP (CLV >€300) con paquete paralizado por alto riesgo de retraso según la API Logística.
2. **Reabastecimiento Urgente (SKU Crítico):** Mover unidades de almacén central para la Sudadera Negra (stock ≤ 2 uds, sell-through > 70%).
3. **Frenar Inversión en Ads:** Solicitar a marketing reducir la campaña activa en TikTok (intensidad *very_high*) para un SKU a 15 minutos del *stockout*.
4. **Resolver Bloqueo Financiero:** Revisar fraude/pago en pedido atascado en *payment_review* de alto valor (>€120).
5. **Apaciguar Cliente At-Risk:** Intervenir ticket de soporte urgente con sentimiento negativo de un usuario con alta probabilidad de abandono (*churn*).
6. **Desbloquear Envío Retenido:** Revisión manual logística detectada por la API de Shipping para un pedido internacional de alto volumen.
7. **Priorizar Empaquetado:** Alertar a almacén para empaquetar de inmediato pedidos de clientes Leales afectados por fallos de la pasarela de pago.
8. **Compensación Proactiva:** Enviar código de descuento automático a clientes atrapados en incidencias aduaneras antes de que abran un ticket de soporte.
9. **Mitigar Rotura Parcial:** Dividir un pedido (*split fulfillment*) si contiene un SKU agotado pero el resto de artículos están disponibles para el cliente VIP.
10. **Alineación de Stock:** Alertar al equipo de compras ante una anomalía de demanda donde un artículo no promocionado tiene un pico de *sell-through* inesperado.

### Top 10 Acciones Priorizadas Durante el Desarrollo (Arquitectura MVP)
Durante la construcción de esta versión (*MVP*), el equipo técnico centró sus esfuerzos en las siguientes decisiones arquitectónicas prioritarias para garantizar la entrega de un producto robusto y funcional en tiempo récord:

1. **Unificación de Datos Desestructurados:** Construcción de una capa de ingesta y sanitización capaz de cruzar 5 orígenes de datos dispares (pedidos, tickets, inventario, campañas, logística) normalizando SKUs y IDs en un estado global único.
2. **Diseño del Motor de *Scoring* Heurístico:** Desarrollo de un algoritmo determinista súper rápido (0 a 100+) en lugar de depender de LLMs generativos en tiempo real, asegurando latencia mínima al cruzar múltiples variables de riesgo.
3. **Simulador Táctico de Inventario:** Implementación de métricas proyectivas cruzando el stock actual con el ritmo de ventas (*sell-through* por hora) para anticipar roturas críticas.
4. **Integración Logística Concurrente:** Uso intensivo de `ThreadPoolExecutor` para paralelizar las peticiones a la API externa de Supabase, limitando el procesamiento a los pedidos de mayor riesgo para no saturar la red.
5. **Degradación Elegante (*Graceful Degradation*):** Implementación de *fallbacks* y *timeouts* ultra-rápidos (2.5s) que aseguran que si la API externa cae o responde lento, el dashboard carga inmediatamente asumiendo un estado neutral.
6. **Interfaz "Zero-Clicks" de Alta Tensión:** Diseño UI/UX orientado a operarios de alta presión (*Glassmorphism*, modo oscuro, código de colores estricto) para que la urgencia máxima se perciba instantáneamente sin necesidad de navegar.
7. **Simulación de *Streaming* de Datos:** Construcción de una arquitectura que imita un motor de eventos en tiempo real recalculando íntegramente las prioridades logísticas con cada consulta o refresco del cliente.
8. **Desacoplamiento Frontend/Backend:** Separación total de responsabilidades creando endpoints RESTful limpios (`/api/data`, `/api/shipping/test`) que aíslan la pesada carga computacional del renderizado visual.
9. **Empaquetado para Producción en la Nube:** Configuración del entorno WSGI mediante `gunicorn` y gestión de variables de entorno para una migración limpia desde entorno local al despliegue nativo en Railway.
10. **Seguridad Integrada (Hardcoding Temporal MVP):** Inserción segura y ofuscación de dependencias externas (como el *Candidate ID* de la API logística) para garantizar un despliegue "plug & play" infalible durante las demostraciones.

## 5. Limitaciones Conocidas (Trade-offs de Arquitectura)
Con el fin de garantizar una entrega rápida y funcional para este prototipo (MVP), se han asumido ciertas decisiones técnicas que escalarían diferente en un entorno de producción masivo:
* **Ingesta Estática vs Streaming:** Actualmente el motor ingesta *snapshots* mediante archivos CSV locales. En producción, esto se sustituiría por un bus de eventos (ej. Kafka, RabbitMQ) para streaming de datos en tiempo real.
* **Procesamiento de la API Externa:** Para evitar colapsos en la UI, las peticiones a la API de Supabase se realizan en paralelo mediante un `ThreadPoolExecutor` con *timeout* agresivo (2.5s) restringido a las órdenes de mayor prioridad. En un entorno *Enterprise*, este enriquecimiento debería ocurrir de forma asíncrona mediante *background workers* (ej. Celery) que actualicen la base de datos en segundo plano.
* **Control de Accesos (RBAC):** La versión actual es de acceso directo para facilitar la demo. Un entorno productivo requeriría integración con un IdP (Identity Provider) y gestión de roles.
