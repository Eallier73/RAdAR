from __future__ import annotations

import argparse
import json

from .frozen_inference_assets import bootstrap_predict_only_asset, predict_only_asset_status


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap explícito de paquetes predict-only para operación post-W10."
    )
    parser.add_argument(
        "--run-id",
        default="E1_v5_clean",
        help="Perfil congelado a empaquetar. Soporta E1/E2/E3/E5/E7 y E9_v2_clean.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    asset = bootstrap_predict_only_asset(args.run_id)
    status = predict_only_asset_status(args.run_id)
    payload = {
        "run_id": args.run_id,
        "status": status,
        "manifest_path": str(asset.manifest_path),
        "canonical_run_dir": str(asset.canonical_run_dir),
        "horizons": list(asset.horizons),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
