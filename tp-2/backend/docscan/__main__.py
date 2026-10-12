import argparse
import sys
from pathlib import Path

from docscan import encode_png, read_photo
from docscan.exceptions import ScanError
from docscan.scanner import Scanner


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detecta y escanea un documento de una foto."
    )
    parser.add_argument("entrada", type=Path, help="Foto original")
    parser.add_argument("salida", type=Path, help="Ruta del PNG escaneado")
    parser.add_argument(
        "--color-mode",
        choices=("color", "grayscale", "bw"),
        default="color",
    )
    parser.add_argument(
        "--no-color-correction",
        action="store_false",
        dest="color_correction",
        default=True,
        help="No corregir la dominante de color",
    )
    parser.add_argument(
        "--soften-colors",
        type=float,
        default=0.0,
        help="Aclarado de colores fuertes entre 0 y 1",
    )

    args = parser.parse_args()

    if not 0.0 <= args.soften_colors <= 1.0:
        parser.error("--soften-colors debe estar entre 0 y 1")

    try:
        photo = read_photo(args.entrada.read_bytes())
        result = Scanner().scan(
            photo.image,
            color_mode=args.color_mode,
            color_correction=args.color_correction,
            soften_colors=args.soften_colors,
        )
        args.salida.write_bytes(encode_png(result.image))
    except (ScanError, OSError) as error:
        print(f"No se pudo escanear la imagen: {error}", file=sys.stderr)
        return 1

    print(f"Escaneo guardado en: {args.salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())