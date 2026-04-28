# 🚀 Scuffers AI Ops Control Tower
**Entregable Final - UDIA × ESIC Hackathon**

## 1. Resumen Ejecutivo
**Scuffers AI Ops Control Tower** es un sistema inteligente diseñado para resolver el caos operativo durante lanzamientos de alta demanda (drops). En lugar de abrumar al equipo con paneles llenos de gráficas estáticas, el sistema ingesta datos imperfectos de múltiples fuentes (inventario, pedidos, atención al cliente, logística) y los transforma en un **Top 10 de acciones quirúrgicas priorizadas**. Responde en tiempo real a la pregunta: *"¿Qué es lo más importante que debe hacer operaciones ahora mismo?"* garantizando la protección de clientes clave (VIP) y la prevención de roturas de stock.

## 2. Enfoque y Arquitectura
Arquitectura **ligera, rápida y libre de fricciones** (sin dependencias pesadas), ideal para despliegues ágiles:

* **Backend Inteligente (Python/Flask):** Motor de reglas y scoring que normaliza datos sucios, unifica SKUs y evalúa el riesgo multivariable. Incluye un simulador predictivo de demanda que proyecta el stock a 2 horas vista.
* **Integración Incremental API:** Se conecta de forma concurrente (mediante `ThreadPoolExecutor`) a una API logística externa para enriquecer el score, con degradación elegante (*graceful degradation*) si falla, asegurando que la carga del dashboard sea siempre < 1s.
* **Frontend Glassmorphism (HTML/JS/CSS):** Interfaz orientada a operarios de alta presión. Dark mode profesional, animaciones en tiempo real, terminal visual de carga y estado de los datos.

## 3. Instalación Local
1. Clona el repositorio: `git clone https://github.com/tu-usuario/scuffers-ai-ops.git`
2. Instala las dependencias: `pip install -r requirements.txt`
3. Ejecuta el servidor: `python app.py`
4. Abre el navegador en `http://localhost:5004`

> **Nota para la demo logística:** Configura tu variable de entorno `SCUFFERS_CANDIDATE_ID` antes de arrancar la app para conectar exitosamente a la API de Supabase.
