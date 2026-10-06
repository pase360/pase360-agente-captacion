# Pase 360 — Agente de Captación Limpio

Proyecto independiente y nuevo. Funciona primero en **modo prueba** y pasa a producción cambiando una sola variable:

`MODO_PRUEBA=no`

## Qué hace

- Busca prospectos de Córdoba Capital mediante OpenStreetMap/Overpass.
- Intenta obtener email y datos desde el sitio web público del prospecto.
- Clasifica separando comercios y generadores.
- Descarta categorías que no corresponden.
- Deduplica por email, dominio, sitio y nombre.
- En modo prueba **NO envía correos ni crea leads en Odoo**.
- Genera reportes CSV/JSON.
- En producción crea leads en Odoo y envía invitaciones.
- Mantiene historial para no volver a contactar al mismo prospecto.
- Puede hacer seguimientos.
- Puede abrir GitHub Issues para casos que requieren decisión humana.
- Tiene diagnóstico de fuentes, Gemini y Odoo.
- Está preparado para GitHub Actions.

## Regla de seguridad

El agente no inventa emails. Un prospecto solo queda `listo_para_contactar` si tiene un email válido obtenido de OSM o del sitio web real.

Los casos dudosos no reciben invitación automática.

## Requisitos

- GitHub
- Odoo 19 Online
- Python 3.12 (GitHub Actions lo instala)
- Gemini opcional pero recomendable

## Secrets de GitHub

Crear en `Settings → Secrets and variables → Actions`.

### Odoo
- `ODOO_URL`
- `ODOO_DB`
- `ODOO_USER`
- `ODOO_API_KEY`
- `ODOO_COMPANY_ID` = `3` para Pase 360

### Gemini
- `GEMINI_API_KEY`
- `GEMINI_MODEL` = `gemini-2.5-flash`

### Identidad
- `OWNER_NAME`
- `OWNER_EMAIL`
- `SENDER_EMAIL`

### Agente
- `MODO_PRUEBA` = `si` inicialmente
- `META_CONTACTOS` = `100`
- `MAX_CANDIDATOS_SCAN` = `1000`

`GOOGLE_MAPS_API_KEY` es opcional. El agente arranca sin ella usando OpenStreetMap.

GitHub Actions proporciona `GITHUB_TOKEN` automáticamente.

## Instalación

1. Crear un repositorio vacío, por ejemplo `pase360/agente-captacion`.
2. Subir **todo el contenido del ZIP** a la raíz.
3. Crear los Secrets anteriores.
4. Mantener `MODO_PRUEBA=si`.
5. Ir a `Actions → Pase 360 - Agente`.
6. Ejecutar manualmente `diagnostico`.
7. Ejecutar manualmente `captar`.
8. Revisar el artifact generado por el workflow.
9. Cuando apruebes el resultado, cambiar solamente `MODO_PRUEBA=no`.

## Acciones manuales

- `diagnostico`
- `captar`
- `preguntas`
- `seguimiento`
- `reporte`

## 100 prospectos

`META_CONTACTOS=100` significa hasta 100 prospectos **realmente listos para contactar** por día. Si las fuentes reales no entregan 100 emails válidos, el agente no inventa ni fuerza contactos; informa el faltante.

## Pruebas locales

```bash
python -m unittest discover -s tests -v
python -m agente.main diagnostico
python -m agente.main captar
```

## Fuentes

Fuente primaria de lugares: OpenStreetMap mediante servidores Overpass configurados en `agente/config.py`.

El sitio web de cada prospecto se consulta solo para completar información pública.
