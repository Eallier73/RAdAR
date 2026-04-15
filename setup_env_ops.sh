#!/usr/bin/env bash
# =============================================================================
# setup_env_ops.sh — Crea o actualiza el entorno operativo RAdAR
# =============================================================================
#
# Entorno: radar-ops-py311 (extraccion, preprocessing, utilidades operativas)
# Archivo de entorno: environment.ops.yml
#
# USO:
#   bash setup_env_ops.sh                          # usa environment.ops.yml del repo
#   bash setup_env_ops.sh /ruta/otra/env.yml       # entorno alternativo
#
# Si conda.sh no esta en la ruta por defecto, exportala antes:
#   export CONDA_SH=$HOME/miniconda3/etc/profile.d/conda.sh
#   bash setup_env_ops.sh
#
# NOTA: Playwright requiere instalacion adicional de navegadores (chromium).
# Este script la ejecuta automaticamente. Si falla, hacerlo manualmente:
#   conda activate radar-ops-py311
#   playwright install chromium
#
# =============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${1:-$ROOT_DIR/environment.ops.yml}"
CONDA_SH="${CONDA_SH:-$HOME/anaconda3/etc/profile.d/conda.sh}"

# ── Validaciones previas ─────────────────────────────────────────────────────

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: No existe el archivo de entorno: $ENV_FILE" >&2
  exit 1
fi

if [[ ! -f "$CONDA_SH" ]]; then
  echo "ERROR: No encontre conda.sh en: $CONDA_SH" >&2
  echo "" >&2
  echo "Exporta CONDA_SH apuntando a tu instalacion de conda, por ejemplo:" >&2
  echo "  export CONDA_SH=\$HOME/miniconda3/etc/profile.d/conda.sh" >&2
  echo "  export CONDA_SH=\$HOME/anaconda3/etc/profile.d/conda.sh" >&2
  exit 1
fi

source "$CONDA_SH"

ENV_NAME="$(awk '/^name:/ {print $2; exit}' "$ENV_FILE")"
if [[ -z "$ENV_NAME" ]]; then
  echo "ERROR: No pude leer el nombre del entorno desde: $ENV_FILE" >&2
  exit 1
fi

# ── Crear o actualizar entorno ───────────────────────────────────────────────

if conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  echo "Actualizando entorno existente: $ENV_NAME"
  conda env update -n "$ENV_NAME" -f "$ENV_FILE" --prune
else
  echo "Creando entorno nuevo: $ENV_NAME"
  conda env create -f "$ENV_FILE"
fi

# ── Playwright: instalar navegadores ─────────────────────────────────────────
#
# playwright install debe correr DESPUES de instalar el paquete.
# chromium es el navegador usado por twitter_extractor y medios_extractor.
#
echo ""
echo "Instalando navegadores de Playwright (chromium)..."
if conda run -n "$ENV_NAME" playwright install chromium; then
  echo "Playwright chromium instalado correctamente."
else
  echo "" >&2
  echo "ADVERTENCIA: Fallo la instalacion automatica de Playwright chromium." >&2
  echo "Completa la instalacion manualmente antes de correr extractores:" >&2
  echo "  conda activate $ENV_NAME" >&2
  echo "  playwright install chromium" >&2
fi

# ── Resumen ───────────────────────────────────────────────────────────────────

cat <<EOF

Entorno listo: $ENV_NAME

Activacion:
  source "$CONDA_SH"
  conda activate $ENV_NAME

Verificar configuracion antes de extraer:
  conda run -n $ENV_NAME python -m src.shared.check_config
  conda run -n $ENV_NAME python -m src.shared.check_config --ensure-dirs

Nota: este es el entorno operativo (extraccion, preprocessing).
No incluye stack de modelado ni registra kernel Jupyter.
Para modelado/notebooks, usa: bash setup_env_experimentos.sh
EOF
