# BKDev · Recepción inteligente
Demostrador de automatización e IA generativa para droguerías, con datos sintéticos y revisión humana.

## Ejecutar
Python 3.12 o superior. Sin dependencias externas de runtime.
```bash
python run.py
```
Abre http://127.0.0.1:8001. Carga el ejemplo o importa un archivo JSON, analiza, revisa las evidencias, exporta CSV y registra la revisión. El historial se guarda en `var/demo.sqlite`.

```bash
python -m unittest discover -s tests -v
python scripts/evaluate.py
```

## IA generativa opcional
Por defecto funciona con una plantilla explícitamente identificada. Para narración con un modelo local, instala Ollama por separado y descarga el modelo elegido. Configura en la terminal antes de iniciar:
```bash
export AI_MODE=ollama
export OLLAMA_URL=http://127.0.0.1:11434
export OLLAMA_MODEL=qwen2.5:7b
python run.py
```
En PowerShell usa `$env:AI_MODE="ollama"`, etc. Se usa `POST /api/chat`, JSON no streaming, timeout 30 s y prompt versionado. No se incluye una suscripción ni un modelo dentro del proyecto. Las referencias se validan por id; toda narración requiere revisión semántica humana. El proveedor de IA no decide ni escribe inventario. Si falla, se conserva el análisis y se muestra una plantilla.

## Docker
```bash
docker build -t bkdev-recepcion .
docker run --rm -p 127.0.0.1:8001:8001 -v bkdev-recepcion-data:/app/var bkdev-recepcion
```
Para persistencia con volumen verifica permisos del usuario `demo`. El endpoint Ollama requiere configuración de red específica desde contenedores. El demo sin IA no requiere conexiones externas.

## Contrato de recepción
`order`: lista de `{sku, quantity}`. `receipt`: `{sku, lot, quantity, expiry}`.
`documents`: factura (`invoice`), guía (`delivery_note`) y certificados (`certificate`, con `id, sku, lot, expiry`).
Fechas ISO, cantidades enteras no negativas. Se agregan cantidades entre lotes del mismo SKU.
180 días es un umbral ilustrativo, no una exigencia legal. El demo verifica la presencia declarada de factura/guía; no compara importes tributarios ni sustituye inspección física.
La carga principal es JSON estructurado. El panel opcional extrae factura, guía o certificado desde texto mediante Ollama. Para PDF con capa de texto instala `python -m pip install -r requirements-pdf.txt`. Se muestra el borrador y su cita textual antes de incorporarlo al JSON; valida cada campo. PDF escaneado requiere OCR externo, que no está incluido. No se extraen automáticamente todas las líneas de la orden o factura. La evidencia textual valida una cita, no cada campo: requiere cotejo humano.

## API
- `GET /api/sample`: ejemplo sintético.
- `POST /api/extract`: extracción documental opcional (texto o PDF base64).
- `POST /api/analyze`: analiza JSON y guarda ejecución.
- `GET /api/history`: últimas 100 revisiones.
- `POST /api/review`: `{id, reviewer, note}`; una sola revisión por ejecución.
- `GET /api/export/ID`: observaciones CSV.
- `GET /api/health`: estado.

## Harness y arquitectura
MVC con servicios y adaptadores: [arquitectura](docs/architecture.md), [instrucciones del agente](AGENTS.md), [caso de estudio](docs/case-study.md), golden dataset en `evals/` y CI en `.github/workflows/`.

Primera versión local: sin autenticación, OCR, integraciones de ERP ni certificación de cumplimiento normativo. Preparar identidad, roles, infraestructura y revisión sectorial antes de un uso real. No contiene datos de clientes ni resultados comerciales atribuidos.
