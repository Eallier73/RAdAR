#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${1:-$ROOT_DIR/environment.experimentos.yml}"
CONDA_SH="${CONDA_SH:-$HOME/anaconda3/etc/profile.d/conda.sh}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "No existe el archivo de entorno: $ENV_FILE" >&2
  exit 1
fi

if [[ ! -f "$CONDA_SH" ]]; then
  echo "No encontre conda.sh en: $CONDA_SH" >&2
  echo "Exporta CONDA_SH apuntando a tu instalacion de conda." >&2
  exit 1
fi

source "$CONDA_SH"

ENV_NAME="$(awk '/^name:/ {print $2; exit}' "$ENV_FILE")"
if [[ -z "$ENV_NAME" ]]; then
  echo "No pude leer el nombre del entorno desde: $ENV_FILE" >&2
  exit 1
fi

if conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  echo "Actualizando entorno existente: $ENV_NAME"
  conda env update -n "$ENV_NAME" -f "$ENV_FILE" --prune
else
  echo "Creando entorno nuevo: $ENV_NAME"
  conda env create -f "$ENV_FILE"
fi

echo "Registrando kernel de Jupyter para: $ENV_NAME"
conda run -n "$ENV_NAME" python -m ipykernel install --user --name "$ENV_NAME" --display-name "Python ($ENV_NAME)"

cat <<EOF

Entorno listo.

Activacion:
  source "$CONDA_SH"
  conda activate $ENV_NAME

Kernel Jupyter:
  Python ($ENV_NAME)
EOF
