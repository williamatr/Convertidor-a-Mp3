"""
convertir_audio.py
==================
Convierte archivos de audio de múltiples formatos a MP3.
NO requiere instalar FFmpeg manualmente — se descarga automáticamente.

Llama a FFmpeg directamente via subprocess (sin depender del PATH del sistema).

Instalación:
  pip install imageio-ffmpeg

Carpetas:
  - Originales/   → archivos fuente
  - Convertidos/  → archivos MP3 resultantes
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

# ── Obtener FFmpeg embebido ──────────────────────────────────────────────────
try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    print("ERROR: Falta la librería imageio-ffmpeg.")
    print("Ejecuta: pip install imageio-ffmpeg")
    sys.exit(1)

# ──────────────────────────────────────────────
# CONFIGURACIÓN
# ──────────────────────────────────────────────

CARPETA_ORIGINALES  = Path("Originales")
CARPETA_CONVERTIDOS = Path("Convertidos")

# Calidad del MP3. Valores posibles: "128k", "192k", "256k", "320k"
BITRATE_MP3 = "192k"

FORMATOS_SOPORTADOS = {
    ".mp3", ".wav", ".ogg", ".flac", ".aac",
    ".m4a", ".wma", ".opus", ".mpeg", ".mpga",
    ".mp2", ".aiff", ".aif", ".webm", ".ra",
}

# ──────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("conversion.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# FUNCIONES
# ──────────────────────────────────────────────

def verificar_ffmpeg() -> None:
    """Verifica que el FFmpeg embebido funcione correctamente."""
    try:
        result = subprocess.run(
            [FFMPEG_PATH, "-version"],
            capture_output=True, text=True, timeout=10
        )
        version_line = result.stdout.splitlines()[0] if result.stdout else "desconocida"
        log.info(f"FFmpeg listo : {version_line}")
        log.info(f"Ruta         : {FFMPEG_PATH}")
    except Exception as e:
        log.error(f"Error verificando FFmpeg: {e}")
        sys.exit(1)


def preparar_carpetas() -> None:
    CARPETA_ORIGINALES.mkdir(exist_ok=True)
    CARPETA_CONVERTIDOS.mkdir(exist_ok=True)
    log.info(f"Carpeta origen  : {CARPETA_ORIGINALES.resolve()}")
    log.info(f"Carpeta destino : {CARPETA_CONVERTIDOS.resolve()}")


def obtener_archivos_audio() -> list[Path]:
    return sorted(
        f for f in CARPETA_ORIGINALES.iterdir()
        if f.is_file() and f.suffix.lower() in FORMATOS_SOPORTADOS
    )


def convertir_a_mp3(origen: Path) -> bool:
    """
    Convierte un archivo de audio a MP3 llamando a FFmpeg directamente
    via subprocess — sin depender del PATH del sistema.
    """
    destino = CARPETA_CONVERTIDOS / (origen.stem + ".mp3")

    if destino.exists():
        log.info(f"[OMITIDO]  '{origen.name}' ya fue convertido.")
        return True

    # Comando FFmpeg:
    #   -i        → archivo de entrada
    #   -vn       → ignorar video si lo hubiera
    #   -ab       → bitrate de audio
    #   -ar 44100 → sample rate estándar para MP3
    #   -ac 2     → stereo
    #   -y        → sobreescribir sin preguntar
    cmd = [
        FFMPEG_PATH,
        "-i", str(origen),
        "-vn",
        "-ab", BITRATE_MP3,
        "-ar", "44100",
        "-ac", "2",
        "-f", "mp3",
        "-y",
        str(destino),
    ]

    try:
        log.info(f"[CONVIRTIENDO]  {origen.name}  →  {destino.name}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos máximo por archivo
        )

        if result.returncode == 0:
            size_kb = destino.stat().st_size // 1024
            log.info(f"[OK]  Guardado: {destino.name}  ({size_kb} KB)")
            return True
        else:
            # FFmpeg escribe sus errores en stderr
            error_msg = result.stderr.strip().splitlines()[-1] if result.stderr else "error desconocido"
            log.error(f"[ERROR]  FFmpeg falló con '{origen.name}': {error_msg}")
            # Eliminar archivo de destino incompleto si quedó
            if destino.exists():
                destino.unlink()
            return False

    except subprocess.TimeoutExpired:
        log.error(f"[ERROR]  Tiempo de espera agotado para '{origen.name}'.")
        if destino.exists():
            destino.unlink()
        return False
    except Exception as exc:
        log.error(f"[ERROR]  Fallo inesperado con '{origen.name}': {exc}")
        return False


def mostrar_resumen(total: int, exitosos: int, fallidos: int) -> None:
    sep = "─" * 50
    print(f"\n{sep}")
    print("  RESUMEN DE CONVERSIÓN")
    print(sep)
    print(f"  Total encontrados : {total}")
    print(f"  Convertidos OK    : {exitosos}")
    print(f"  Con errores       : {fallidos}")
    print(f"  Bitrate MP3       : {BITRATE_MP3}")
    print(f"  Destino           : {CARPETA_CONVERTIDOS.resolve()}")
    print(f"{sep}\n")


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main() -> None:
    print("\n🎵  Conversor de Audio a MP3  (FFmpeg embebido)")
    print("=" * 50)

    verificar_ffmpeg()
    preparar_carpetas()

    archivos = obtener_archivos_audio()

    if not archivos:
        log.warning(
            f"No se encontraron archivos en '{CARPETA_ORIGINALES}/'. "
            f"Formatos soportados: {', '.join(sorted(FORMATOS_SOPORTADOS))}"
        )
        return

    log.info(f"Archivos encontrados: {len(archivos)}")

    exitosos, fallidos = 0, 0
    for archivo in archivos:
        if convertir_a_mp3(archivo):
            exitosos += 1
        else:
            fallidos += 1

    mostrar_resumen(len(archivos), exitosos, fallidos)


if __name__ == "__main__":
    main()