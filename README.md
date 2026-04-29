# 🚀 Scuffers AI Ops Control Tower
**Entregable Final - UDIA × ESIC Hackathon**

> 🖥️ **Demo en Vivo (Despliegue Full-Stack):** [https://scuffers-control-tower-dark-production.up.railway.app/](https://scuffers-control-tower-dark-production.up.railway.app/)
> 📦 **Repositorio Oficial:** [https://github.com/XC9000/scuffers-control-tower-dark](https://github.com/XC9000/scuffers-control-tower-dark)
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

### Próximos Pasos: Top 10 Acciones Priorizadas de Desarrollo (Roadmap)
Para evolucionar esta inteligencia operativa hacia un producto escalable y robusto, el equipo de ingeniería tiene priorizado el siguiente *backlog*:

1. **Migración a Event-Driven Architecture:** Reemplazar la ingesta *batch* de CSVs por consumo de eventos en tiempo real (ej. Kafka/RabbitMQ) directamente desde los sistemas de ERP y OMS.
2. **Procesamiento Asíncrono (Colas):** Trasladar las llamadas a la API de Shipping a *background workers* (Celery/Redis) para desacoplarlas del servidor principal y asegurar latencia 0 en el frontend.
3. **Control de Accesos Basado en Roles (RBAC):** Implementar autenticación y segregación de permisos (IdP/JWT) para que agentes de soporte, mánagers logísticos y administradores vean solo acciones de su competencia.
4. **Machine Learning Predictivo:** Evolucionar el cálculo lineal de *sell-through* integrando un modelo predictivo (ej. XGBoost) que anticipe roturas de stock basándose en datos históricos y estacionalidad.
5. **Auto-resolución mediante LLMs:** Integrar agentes conversacionales (RAG/LangChain) capaces de aplicar descuentos o emitir reembolsos automáticos en tickets de nivel 1 clasificados como urgentes.
6. **Webhooks Bidireccionales:** Desarrollar la capacidad de que la torre no solo lea, sino que dispare acciones (ej. ocultar automáticamente un SKU en Shopify si el sistema prevé rotura crítica inminente).
7. **Caché en Memoria (Redis):** Cachear perfiles de clientes VIP y scoring logístico para reducir masivamente el coste computacional y las consultas a base de datos en picos de demanda.
8. **Observabilidad Avanzada:** Integrar Grafana y Prometheus para monitorizar en tiempo real el *health check* del propio motor de reglas y la tasa de error de las APIs externas.
9. **Pipelines CI/CD y Tests E2E:** Aumentar la cobertura con Pytest y Cypress, orquestando el despliegue automático mediante GitHub Actions para evitar fallos críticos en plenos lanzamientos.
10. **Contexto Geopolítico en el Scoring:** Modificar el algoritmo de riesgo para ponderar automáticamente posibles retrasos logísticos en función del país de destino y los tiempos medios de aduanas.

## 5. Limitaciones Conocidas (Trade-offs de Arquitectura)
Con el fin de garantizar una entrega rápida y funcional para este prototipo (MVP), se han asumido ciertas decisiones técnicas que escalarían diferente en un entorno de producción masivo:
* **Ingesta Estática vs Streaming:** Actualmente el motor ingesta *snapshots* mediante archivos CSV locales. En producción, esto se sustituiría por un bus de eventos (ej. Kafka, RabbitMQ) para streaming de datos en tiempo real.
* **Procesamiento de la API Externa:** Para evitar colapsos en la UI, las peticiones a la API de Supabase se realizan en paralelo mediante un `ThreadPoolExecutor` con *timeout* agresivo (2.5s) restringido a las órdenes de mayor prioridad. En un entorno *Enterprise*, este enriquecimiento debería ocurrir de forma asíncrona mediante *background workers* (ej. Celery) que actualicen la base de datos en segundo plano.
* **Control de Accesos (RBAC):** La versión actual es de acceso directo para facilitar la demo. Un entorno productivo requeriría integración con un IdP (Identity Provider) y gestión de roles.
