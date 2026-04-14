# Оптимизация hero-картинок: пережимает исходники в WebP + JPG
# в нескольких размерах под srcset. Имена файлов — латиница со слагом.
#
# Запуск: python _scripts/optimize-hero-images.py

import os
import sys
from pathlib import Path
from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT / "images" / "images-финал"
OUT_DIR = PROJECT / "images" / "hero"

# Карта: исходный файл → целевой слаг, + список размеров (ширина в px)
# stat-иконки показываются ~60px → нужны 128 (1x) и 256 (2x retina)
# специалист-герой показывается до ~560px высоты → нужны 400, 800, 1200
JOBS = [
    ("довольный клиент.jpg",  "stat-clients",     [128, 256]),
    ("опыт.jpg",              "stat-experience",  [128, 256]),
    ("быстрый ответ.jpg",     "stat-fast",        [128, 256]),
    ("гарантия365.jpg",       "stat-guarantee",   [128, 256]),
    ("специалист-герой.jpg",  "specialist",       [400, 800, 1200]),
]

WEBP_QUALITY = 82   # WebP lossy, баланс качество/размер
JPG_QUALITY  = 82   # JPEG fallback


def process(src: Path, slug: str, widths: list[int]) -> list[tuple[str, int]]:
    results = []
    with Image.open(src) as img:
        img = img.convert("RGB")
        orig_w, orig_h = img.size
        for w in widths:
            if w >= orig_w:
                # исходник уже меньше — не апскейлим
                resized = img
                actual_w = orig_w
            else:
                ratio = w / orig_w
                new_h = round(orig_h * ratio)
                resized = img.resize((w, new_h), Image.LANCZOS)
                actual_w = w

            for fmt, ext, quality in (("WEBP", "webp", WEBP_QUALITY), ("JPEG", "jpg", JPG_QUALITY)):
                out = OUT_DIR / f"{slug}-{actual_w}.{ext}"
                save_kwargs = {"quality": quality, "optimize": True}
                if fmt == "WEBP":
                    save_kwargs["method"] = 6  # максимальное сжатие
                resized.save(out, fmt, **save_kwargs)
                size = out.stat().st_size
                results.append((out.name, size))
    return results


def main():
    if not SRC_DIR.exists():
        print(f"[!] Нет исходной папки: {SRC_DIR}")
        sys.exit(1)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    total_before = 0
    total_after = 0
    for src_name, slug, widths in JOBS:
        src = SRC_DIR / src_name
        if not src.exists():
            print(f"[!] Пропущено (не найдено): {src_name}")
            continue
        before = src.stat().st_size
        total_before += before
        print(f"\n[{slug}] {src_name} — {before/1024:.0f} КБ")
        for name, size in process(src, slug, widths):
            total_after += size
            print(f"  → {name}: {size/1024:.1f} КБ")

    print("\n" + "=" * 50)
    print(f"Исходники:    {total_before/1024:.0f} КБ")
    print(f"Оптимизация:  {total_after/1024:.0f} КБ")
    if total_before > 0:
        print(f"Экономия:     {(1 - total_after/total_before)*100:.1f}%")


if __name__ == "__main__":
    main()
