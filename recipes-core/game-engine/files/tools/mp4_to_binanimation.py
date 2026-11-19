import argparse
from pathlib import Path
import cv2
import numpy as np

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


def convert_mp4_to_raw_bin(mp4_path: Path, output_bin_path: Path, target_cols: int = 48, target_rows: int = 48):
    cap = cv2.VideoCapture(str(mp4_path))
    if not cap.isOpened():
        print(f"[SKIP] Failed to open: {mp4_path}")
        return

    count = 0
    with open(output_bin_path, "wb") as f:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            small = cv2.resize(frame, (target_cols, target_rows), interpolation=cv2.INTER_NEAREST)
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
            grb = np.stack([g, r, b], axis=-1).astype(np.uint8)
            f.write(grb.tobytes())
            count += 1

    cap.release()
    print(f"Converted {count} frames: {mp4_path.name} -> {output_bin_path}")


def main():
    parser = argparse.ArgumentParser(description="Batch convert videos to raw GRB .bin files.")
    parser.add_argument("input_dir", type=Path, help="Directory containing input video files")
    parser.add_argument("output_dir", type=Path, help="Directory to save output .bin files")
    parser.add_argument("--cols", type=int, default=48, help="Target matrix columns (default: 48)")
    parser.add_argument("--rows", type=int, default=48, help="Target matrix rows (default: 48)")
    args = parser.parse_args()

    if not args.input_dir.is_dir():
        raise FileNotFoundError(f"Input directory does not exist: {args.input_dir}")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    video_files = sorted(
        p for p in args.input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS
    )

    if not video_files:
        print(f"No video files found in {args.input_dir}")
        return

    for video_path in video_files:
        out_path = args.output_dir / f"{video_path.stem}.bin"
        convert_mp4_to_raw_bin(video_path, out_path, args.cols, args.rows)


if __name__ == "__main__":
    main()
