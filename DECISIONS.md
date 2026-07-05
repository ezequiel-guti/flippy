# DECISIONS.md — Flippy

Registro de decisiones arquitecturales y de implementación.
Fuente de verdad junto con SPEC.md. No duplicar contenido del Spec aquí.

---

════════════════════════════════════════════════════════
📋 DECISIÓN — LLM split: Gemini 2.0 Flash (chat) + Claude 3.5 Sonnet (imágenes)
════════════════════════════════════════════════════════
Fecha: 2026-07-05
Decisión: Usar Google Gemini 2.0 Flash para respuestas RAG del chat y Anthropic Claude 3.5 Sonnet exclusivamente para análisis de imágenes adjuntas por el usuario.
Racional: Gemini 2.0 Flash ofrece menor costo por token para el volumen de consultas de chat RAG; Claude 3.5 Sonnet se mantiene para visión por su calidad en análisis multimodal combinado con corpus.
Alternativas consideradas: Claude 3.5 Sonnet para ambos casos (descartado por costo en chat de alto volumen); Gemini para ambos (descartado — análisis de imágenes con corpus requiere evaluación adicional).
Impacto: flippy-api requiere dos clientes LLM (langchain-google-genai + langchain-anthropic), dos variables de entorno (GOOGLE_API_KEY + ANTHROPIC_API_KEY), lógica de routing en el endpoint de chat según presencia de imagen adjunta.
════════════════════════════════════════════════════════
