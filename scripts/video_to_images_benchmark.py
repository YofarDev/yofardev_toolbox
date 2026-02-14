#!/usr/bin/env python3
"""Benchmark script for video to images conversion - tests multiple approaches."""
import argparse
import os
import sys
import datetime
import time
from pathlib import Path
import cv2
import threading
import queue
from concurrent.futures import ThreadPoolExecutor

# Constants
TEST_FRAMES = 20  # Number of frames to extract for each test

NAME = "Video to Images Benchmark"
DESCRIPTION = "Benchmarks different approaches for video frame extraction. Tests multiple methods with 20 frames each and reports timing results."
INPUT_TYPES = "Videos (*.mp4 *.mov *.avi *.webm *.mkv)"
PARAMETERS = [
    {"name": "interval", "type": "float", "default": 0, "description": "The interval in seconds between frame extractions. Set to 0 to extract all frames."},
    {"name": "start_time", "type": "float", "default": 0, "description": "The timestamp (in seconds) from where to start extracting frames. Default is 0 (start of video)."},
]


class BenchmarkResults:
    """Stores and reports benchmark results."""

    def __init__(self):
        self.results = []

    def add_result(self, method_name, time_taken, frames_saved, output_dir):
        self.results.append({
            "method": method_name,
            "time": time_taken,
            "frames": frames_saved,
            "output_dir": output_dir,
            "fps": frames_saved / time_taken if time_taken > 0 else 0
        })

    def print_report(self):
        """Print a formatted benchmark report."""
        print("\n" + "=" * 80)
        print("BENCHMARK RESULTS")
        print("=" * 80)
        print(f"{'Method':<40} {'Time (s)':<12} {'Frames':<10} {'FPS':<10}")
        print("-" * 80)

        for result in sorted(self.results, key=lambda x: x["time"]):
            print(f"{result['method']:<40} {result['time']:<12.4f} {result['frames']:<10} {result['fps']:<10.2f}")

        print("-" * 80)

        # Find fastest
        if self.results:
            fastest = min(self.results, key=lambda x: x["time"])
            slowest = max(self.results, key=lambda x: x["time"])
            speedup = slowest["time"] / fastest["time"] if fastest["time"] > 0 else 0

            print(f"\nFastest: {fastest['method']} ({fastest['time']:.4f}s)")
            print(f"Slowest: {slowest['method']} ({slowest['time']:.4f}s)")
            print(f"Speedup: {speedup:.2f}x")

        print("=" * 80 + "\n")

        # Save to file
        home_dir = os.path.expanduser("~")
        report_path = os.path.join(home_dir, "Downloads", "video_to_images_benchmark_report.txt")
        with open(report_path, "w") as f:
            f.write("VIDEO TO IMAGES BENCHMARK REPORT\n")
            f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            for result in sorted(self.results, key=lambda x: x["time"]):
                f.write(f"{result['method']}: {result['time']:.4f}s ({result['fps']:.2f} FPS)\n")
            f.write("=" * 80 + "\n")
        print(f"Report saved to: {report_path}\n")


def setup_output_folder(base_name):
    """Create output folder for benchmark."""
    home_dir = os.path.expanduser("~")
    output_folder = os.path.join(home_dir, "Downloads", f"benchmark_{base_name}")
    os.makedirs(output_folder, exist_ok=True)
    return output_folder


# ============================================================================
# METHOD 1: Original PNG (default compression)
# ============================================================================

def method_1_original_png(video_path, start_time=0, frame_interval=1):
    """Original approach - PNG with default compression."""
    output_folder = setup_output_folder("1_original_png")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0, output_folder

    if start_time > 0:
        cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)

    start_time_total = time.time()
    frame_count = 0
    saved_count = 0

    while saved_count < TEST_FRAMES:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count == 0 or frame_count % frame_interval == 0:
            video_name = Path(video_path).stem
            output_path = os.path.join(output_folder, f"{video_name}_{saved_count:06d}.png")
            cv2.imwrite(output_path, frame)
            saved_count += 1

        frame_count += 1

    cap.release()
    elapsed = time.time() - start_time_total
    return elapsed, saved_count


# ============================================================================
# METHOD 2: PNG with compression level 1 (fastest PNG)
# ============================================================================

def method_2_png_compression_1(video_path, start_time=0, frame_interval=1):
    """PNG with lowest compression (level 1)."""
    output_folder = setup_output_folder("2_png_compression_1")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0, output_folder

    if start_time > 0:
        cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)

    start_time_total = time.time()
    frame_count = 0
    saved_count = 0

    while saved_count < TEST_FRAMES:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count == 0 or frame_count % frame_interval == 0:
            video_name = Path(video_path).stem
            output_path = os.path.join(output_folder, f"{video_name}_{saved_count:06d}.png")
            cv2.imwrite(output_path, frame, [int(cv2.IMWRITE_PNG_COMPRESSION), 1])
            saved_count += 1

        frame_count += 1

    cap.release()
    elapsed = time.time() - start_time_total
    return elapsed, saved_count


# ============================================================================
# METHOD 3: PNG with compression level 9 (max compression)
# ============================================================================

def method_3_png_compression_9(video_path, start_time=0, frame_interval=1):
    """PNG with highest compression (level 9)."""
    output_folder = setup_output_folder("3_png_compression_9")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0, output_folder

    if start_time > 0:
        cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)

    start_time_total = time.time()
    frame_count = 0
    saved_count = 0

    while saved_count < TEST_FRAMES:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count == 0 or frame_count % frame_interval == 0:
            video_name = Path(video_path).stem
            output_path = os.path.join(output_folder, f"{video_name}_{saved_count:06d}.png")
            cv2.imwrite(output_path, frame, [int(cv2.IMWRITE_PNG_COMPRESSION), 9])
            saved_count += 1

        frame_count += 1

    cap.release()
    elapsed = time.time() - start_time_total
    return elapsed, saved_count


# ============================================================================
# METHOD 4: JPEG quality 100 (near lossless, very fast)
# ============================================================================

def method_4_jpeg_quality_100(video_path, start_time=0, frame_interval=1):
    """JPEG with maximum quality (100) - lossy but very fast."""
    output_folder = setup_output_folder("4_jpeg_quality_100")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0, output_folder

    if start_time > 0:
        cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)

    start_time_total = time.time()
    frame_count = 0
    saved_count = 0

    while saved_count < TEST_FRAMES:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count == 0 or frame_count % frame_interval == 0:
            video_name = Path(video_path).stem
            output_path = os.path.join(output_folder, f"{video_name}_{saved_count:06d}.jpg")
            cv2.imwrite(output_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
            saved_count += 1

        frame_count += 1

    cap.release()
    elapsed = time.time() - start_time_total
    return elapsed, saved_count


# ============================================================================
# METHOD 5: JPEG quality 95 (fast, good quality)
# ============================================================================

def method_5_jpeg_quality_95(video_path, start_time=0, frame_interval=1):
    """JPEG with quality 95 - fast with good quality."""
    output_folder = setup_output_folder("5_jpeg_quality_95")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0, output_folder

    if start_time > 0:
        cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)

    start_time_total = time.time()
    frame_count = 0
    saved_count = 0

    while saved_count < TEST_FRAMES:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count == 0 or frame_count % frame_interval == 0:
            video_name = Path(video_path).stem
            output_path = os.path.join(output_folder, f"{video_name}_{saved_count:06d}.jpg")
            cv2.imwrite(output_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            saved_count += 1

        frame_count += 1

    cap.release()
    elapsed = time.time() - start_time_total
    return elapsed, saved_count


# ============================================================================
# METHOD 6: TIFF uncompressed (no compression, fastest write)
# ============================================================================

def method_6_tiff_uncompressed(video_path, start_time=0, frame_interval=1):
    """TIFF with no compression - fastest save."""
    output_folder = setup_output_folder("6_tiff_uncompressed")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0, output_folder

    if start_time > 0:
        cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)

    start_time_total = time.time()
    frame_count = 0
    saved_count = 0

    while saved_count < TEST_FRAMES:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count == 0 or frame_count % frame_interval == 0:
            video_name = Path(video_path).stem
            output_path = os.path.join(output_folder, f"{video_name}_{saved_count:06d}.tif")
            cv2.imwrite(output_path, frame)
            saved_count += 1

        frame_count += 1

    cap.release()
    elapsed = time.time() - start_time_total
    return elapsed, saved_count


# ============================================================================
# METHOD 7: Threaded I/O (separate read and write threads)
# ============================================================================

def method_7_threaded_io(video_path, start_time=0, frame_interval=1):
    """Use separate threads for reading and writing frames."""
    output_folder = setup_output_folder("7_threaded_io")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0, output_folder

    if start_time > 0:
        cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)

    start_time_total = time.time()

    # Queue for frame data
    frame_queue = queue.Queue(maxsize=10)
    write_errors = []

    def write_worker():
        """Worker thread for writing frames."""
        while True:
            item = frame_queue.get()
            if item is None:  # Sentinel value to stop
                break
            idx, frame, video_name = item
            output_path = os.path.join(output_folder, f"{video_name}_{idx:06d}.png")
            try:
                cv2.imwrite(output_path, frame)
            except Exception as e:
                write_errors.append(e)
            frame_queue.task_done()

    # Start writer thread
    writer_thread = threading.Thread(target=write_worker, daemon=True)
    writer_thread.start()

    # Read frames
    frame_count = 0
    saved_count = 0
    video_name = Path(video_path).stem

    while saved_count < TEST_FRAMES:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count == 0 or frame_count % frame_interval == 0:
            frame_queue.put((saved_count, frame.copy(), video_name))
            saved_count += 1

        frame_count += 1

    # Signal writer to stop and wait
    frame_queue.put(None)
    writer_thread.join()

    cap.release()
    elapsed = time.time() - start_time_total

    if write_errors:
        print(f"  Warning: {len(write_errors)} write errors occurred")

    return elapsed, saved_count


# ============================================================================
# METHOD 8: Threaded with JPEG (fastest format + threading)
# ============================================================================

def method_8_threaded_jpeg(video_path, start_time=0, frame_interval=1):
    """Threaded I/O with JPEG format."""
    output_folder = setup_output_folder("8_threaded_jpeg")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0, output_folder

    if start_time > 0:
        cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)

    start_time_total = time.time()

    frame_queue = queue.Queue(maxsize=10)

    def write_worker():
        while True:
            item = frame_queue.get()
            if item is None:
                break
            idx, frame, video_name = item
            output_path = os.path.join(output_folder, f"{video_name}_{idx:06d}.jpg")
            cv2.imwrite(output_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            frame_queue.task_done()

    writer_thread = threading.Thread(target=write_worker, daemon=True)
    writer_thread.start()

    frame_count = 0
    saved_count = 0
    video_name = Path(video_path).stem

    while saved_count < TEST_FRAMES:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count == 0 or frame_count % frame_interval == 0:
            frame_queue.put((saved_count, frame.copy(), video_name))
            saved_count += 1

        frame_count += 1

    frame_queue.put(None)
    writer_thread.join()

    cap.release()
    elapsed = time.time() - start_time_total
    return elapsed, saved_count


# ============================================================================
# METHOD 9: Batch writing (collect frames, write all at once)
# ============================================================================

def method_9_batch_writing(video_path, start_time=0, frame_interval=1):
    """Collect all frames first, then write them in batch."""
    output_folder = setup_output_folder("9_batch_writing")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0, output_folder

    if start_time > 0:
        cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)

    # Phase 1: Read all frames into memory
    start_read = time.time()
    frames = []
    frame_count = 0
    video_name = Path(video_path).stem

    while len(frames) < TEST_FRAMES:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count == 0 or frame_count % frame_interval == 0:
            frames.append(frame.copy())

        frame_count += 1

    cap.release()
    read_time = time.time() - start_read

    # Phase 2: Write all frames
    start_write = time.time()
    for i, frame in enumerate(frames):
        output_path = os.path.join(output_folder, f"{video_name}_{i:06d}.png")
        cv2.imwrite(output_path, frame)
    write_time = time.time() - start_write

    total_time = read_time + write_time
    print(f"    Read time: {read_time:.4f}s, Write time: {write_time:.4f}s")

    return total_time, len(frames)


# ============================================================================
# METHOD 10: ThreadPoolExecutor (parallel writes)
# ============================================================================

def method_10_threadpool(video_path, start_time=0, frame_interval=1):
    """Use ThreadPoolExecutor for parallel frame writing."""
    output_folder = setup_output_folder("10_threadpool")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0, output_folder

    if start_time > 0:
        cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)

    start_time_total = time.time()

    frames = []
    frame_count = 0
    video_name = Path(video_path).stem

    # Read all frames
    while len(frames) < TEST_FRAMES:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count == 0 or frame_count % frame_interval == 0:
            frames.append((frame.copy(), video_name, len(frames)))

        frame_count += 1

    cap.release()

    # Write in parallel
    def write_frame(data):
        frame, video_name, idx = data
        output_path = os.path.join(output_folder, f"{video_name}_{idx:06d}.png")
        cv2.imwrite(output_path, frame)

    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(write_frame, frames)

    elapsed = time.time() - start_time_total
    return elapsed, len(frames)


# ============================================================================
# MAIN BENCHMARK RUNNER
# ============================================================================

def run_benchmark(video_paths, start_time=0, interval=0):
    """Run all benchmark methods."""
    if not video_paths:
        print("Error: No video paths provided")
        return

    video_path = video_paths[0]  # Use first video for benchmark

    # Get video FPS to calculate frame interval
    cap_test = cv2.VideoCapture(video_path)
    fps = cap_test.get(cv2.CAP_PROP_FPS)
    cap_test.release()

    if interval == 0:
        frame_interval = 1
        interval_str = "0 (all frames)"
    else:
        frame_interval = int(fps * interval)
        interval_str = f"{interval}s (every {frame_interval} frames)"

    print(f"\nBenchmarking video: {Path(video_path).name}")
    print(f"Extracting {TEST_FRAMES} frames per method...")
    print(f"Starting from: {start_time}s")
    print(f"Frame interval: {interval_str}\n")

    results = BenchmarkResults()

    # Run all methods
    methods = [
        ("1. Original PNG (default compression)", method_1_original_png),
        ("2. PNG compression level 1 (fast)", method_2_png_compression_1),
        ("3. PNG compression level 9 (slow)", method_3_png_compression_9),
        ("4. JPEG quality 100 (near lossless)", method_4_jpeg_quality_100),
        ("5. JPEG quality 95 (fast)", method_5_jpeg_quality_95),
        ("6. TIFF uncompressed", method_6_tiff_uncompressed),
        ("7. Threaded I/O with PNG", method_7_threaded_io),
        ("8. Threaded I/O with JPEG", method_8_threaded_jpeg),
        ("9. Batch writing (read then write)", method_9_batch_writing),
        ("10. ThreadPoolExecutor (parallel writes)", method_10_threadpool),
    ]

    for method_name, method_func in methods:
        print(f"Running: {method_name}...")
        try:
            elapsed, frames_saved = method_func(video_path, start_time, frame_interval)
            print(f"  Completed in {elapsed:.4f}s ({frames_saved} frames)")
            results.add_result(method_name, elapsed, frames_saved, "")
        except Exception as e:
            print(f"  ERROR: {e}")

    # Print report
    results.print_report()


def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("video_paths", nargs="+", help="Paths to the videos to process.")

    for param in PARAMETERS:
        parser.add_argument(f'--{param["name"]}', type=eval(param["type"]), default=param["default"], help=f'Default: {param["default"]}')

    args = parser.parse_args()

    run_benchmark(args.video_paths, start_time=args.start_time, interval=args.interval)


if __name__ == "__main__":
    main()
