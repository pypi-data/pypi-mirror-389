import numpy as np
import cv2
from skimage.filters import threshold_yen


# ----------------------- Helpers (MATCH ORIGINAL) ------------------ #

def normalize_and_resize(proj: np.ndarray, size=(300, 300)) -> np.ndarray:
    """
    Match your original: (proj - min) / (max + eps)  → scale to [0,255] → uint8 → INTER_LINEAR resize.
    (Yes, note this divides by max, not (max-min), to reproduce your numbers.)
    """
    eps = 1e-8
    proj = proj - np.min(proj)
    proj = proj / (np.max(proj) + eps)
    u8 = np.clip(proj * 255.0, 0, 255).astype(np.uint8)
    w, h = size
    return cv2.resize(u8, (w, h), interpolation=cv2.INTER_LINEAR)


def normalize(img: np.ndarray) -> np.ndarray:
    """Standard min-max normalize to [0,1] (matches your script)."""
    img = img.astype(np.float32)
    return (img - img.min()) / (img.max() - img.min() + 1e-8)


def apply_gaussian_blur(img01: np.ndarray, ksize=(5, 5), sigma=1.5) -> np.ndarray:
    """Gaussian blur on [0,1] → [0,1]."""
    src = np.clip(img01, 0.0, 1.0).astype(np.float32)
    blur = cv2.GaussianBlur(src, ksize, sigmaX=sigma)
    return np.clip(blur, 0.0, 1.0)


def threshold_otsu_like_yen(img01: np.ndarray) -> np.ndarray:
    """
    Your original 'threshold_otsu' actually used skimage's Yen threshold on a normalized image.
    Return uint8 mask {0,255}.
    """
    img_norm = (img01 - img01.min()) / (img01.max() - img01.min() + 1e-8)
    t = threshold_yen(img_norm)
    return ((img_norm > t).astype(np.uint8)) * 255


def floodfill_keep_inner_white(bin_u8: np.ndarray) -> np.ndarray:
    """
    Keep only inner white regions: invert → flood-fill from (0,0) → invert back → AND with original.
    Inputs/outputs are uint8 {0,255}.
    """
    inv = cv2.bitwise_not(bin_u8)
    h, w = inv.shape
    ff_mask = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(inv, ff_mask, (0, 0), 255)
    flood_back = cv2.bitwise_not(inv)
    return cv2.bitwise_and(bin_u8, flood_back)


# --------------------------- Core logic --------------------------- #

def _axis_projections(raw: np.ndarray, mask: np.ndarray):
    """
    Build sum projections for x,y,z to mirror your original:
      z-proj: sum over axis=0 → XY
      y-proj: sum over axis=1 → XZ
      x-proj: sum over axis=2 → YZ
    """
    return {
        "x": (np.sum(raw, axis=2), np.sum(mask, axis=2)),  # YZ
        "y": (np.sum(raw, axis=1), np.sum(mask, axis=1)),  # XZ
        "z": (np.sum(raw, axis=0), np.sum(mask, axis=0)),  # XY
    }


def _coverage_from_2d(raw2d: np.ndarray, mask2d: np.ndarray, size=(300, 300)) -> float:
    """
    Reproduce your 2D pipeline exactly (normalize -> blur -> Yen threshold -> floodfill; mask fixed 0.05).
    """
    # As in your script, first create the uint8 "projection images" via normalize_and_resize
    raw_img_u8 = normalize_and_resize(raw2d, size=size)
    mask_img_u8 = normalize_and_resize(mask2d, size=size)

    # RAW pipeline
    raw_norm = normalize(raw_img_u8)             # [0,1]
    raw_blur = apply_gaussian_blur(raw_norm)     # [0,1]
    raw_bin  = threshold_otsu_like_yen(raw_blur) # uint8 {0,255}
    raw_clean = floodfill_keep_inner_white(raw_bin)

    # MASK pipeline: fixed 0.05 threshold after normalize()
    mask_norm = normalize(mask_img_u8)
    mask_bin  = ((mask_norm > 0.05).astype(np.uint8)) * 255

    # Coverage = intersection / raw_area
    inter = np.logical_and(mask_bin == 255, raw_clean == 255)
    raw_area = int((raw_clean == 255).sum())
    inter_area = int(inter.sum())
    return (inter_area / raw_area) if raw_area > 0 else 0.0


def map_coverage_2d(rawmap: np.ndarray, mask_map: np.ndarray, target_size=(300, 300)) -> float:
    """
    Return mean 2D coverage across X/Y/Z projections using your exact pipeline.
    """
    if rawmap.shape != mask_map.shape:
        raise ValueError(f"Shape mismatch: raw {rawmap.shape} vs mask {mask_map.shape}")
    coverages = []
    for axis, (rp, mp) in _axis_projections(rawmap, mask_map).items():
        cov = _coverage_from_2d(rp, mp, size=target_size)
        coverages.append(cov)

    return coverages


# ------------------------------ CLI -------------------------------- #

# def main():
#     ap = argparse.ArgumentParser(description="2D coverage (raw vs mask) using your original projection pipeline.")
#     ap.add_argument("--r", "--raw", dest="raw_path", required=True, type=Path, help="Path to raw map (.mrc/.map)")
#     ap.add_argument("--m", "--mask", dest="mask_path", required=True, type=Path, help="Path to mask map (.mrc/.map)")
#     ap.add_argument("--size", type=int, default=300, help="2D processing size (square). Default: 300")
#     ap.add_argument("--print-axes", action="store_true", help="Also print per-axis coverage (x,y,z).")
#     ap.add_argument("--json", action="store_true", help="Print a JSON object with details.")
#     args = ap.parse_args()
#
#     raw_vol  = load_volume(args.raw_path)
#     mask_vol = load_volume(args.mask_path)
#
#     if raw_vol.shape != mask_vol.shape:
#         raise ValueError(f"Shape mismatch: raw {raw_vol.shape} vs mask {mask_vol.shape}")
#
#     # Per-axis coverages (matching your process_images steps)
#     axis_cov = {}
#     for axis, (rp, mp) in _axis_projections(raw_vol, mask_vol).items():
#         axis_cov[axis] = _coverage_from_2d(rp, mp, size=(args.size, args.size))
#
#     coverage_mean = float(np.mean(list(axis_cov.values())))
#
#     if args.json:
#         print(json.dumps({
#             "coverage_axes": axis_cov,
#             "coverage_mean": coverage_mean,
#             "size": args.size,
#             "raw_path": str(args.raw_path),
#             "mask_path": str(args.mask_path),
#         }, ensure_ascii=False))
#     else:
#         if args.print_axes:
#             print(f"x: {axis_cov['x']:.4f}")
#             print(f"y: {axis_cov['y']:.4f}")
#             print(f"z: {axis_cov['z']:.4f}")
#         print(f"{coverage_mean:.6f}")
#
#
# if __name__ == "__main__":
#     main()

