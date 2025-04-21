from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path
import threading
from typing import Literal
from tqdm import tqdm
from queue import Queue
import httpx
from ants.utils import consume


def infer_name(url: str, headers: dict[str, str]) -> str:
    default = url.split("/")[-1]
    if headers.get("Content-Disposition"):
        filename = headers["Content-Disposition"].split("filename=")[-1].strip('"')
        return filename
    return default


def worker(req: httpx.Request, dest: Path, start: int, end: int, progress_queue: Queue[int]):
    client = httpx.Client()
    req.headers["Range"] = f"bytes={start}-{end}"
    res = client.send(req, stream=True).raise_for_status()
    with open(dest, "rb+") as f:
        f.seek(start)
        for chunk in res.iter_bytes(1024 * 1024):
            f.write(chunk)
            progress_queue.put(len(chunk))


def progress_worker(progress_queue: Queue[int], total: int) -> None:
    pbar = tqdm(
        total=total,
        desc="Downloading",
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
        mininterval=1,
        smoothing=0.2,
    )
    for chunk_size in consume(progress_queue):
        total += chunk_size
        pbar.update(chunk_size)


def download_file(
    req: httpx.Request,
    max_workers: int = 40,
    client: httpx.Client | None = None,
    output_dir: Path = Path.cwd() / "download",
    filename: str | None = None,
    on_conflict: Literal["overwrite", "skip", "rename", "raise"] = "skip",
) -> Path:
    client = client or httpx.Client()
    res = client.send(req, stream=True)
    filename = filename or infer_name(str(req.url), dict(req.headers))
    output_dir.mkdir(parents=True, exist_ok=True)
    content_length = int(res.headers["Content-Length"])
    dest = output_dir / filename
    dest_part = output_dir / f"{filename}.part"
    if dest_part.exists():
        match on_conflict:
            case "raise":
                raise FileExistsError(f"File {dest_part} already exists")
            case "overwrite":
                dest_part.unlink()
            case "skip":
                return dest
            case "rename":
                raise NotImplementedError("Renaming is not implemented yet")
    with open(dest_part, "wb") as f:
        f.truncate(content_length)
    progress_queue = Queue[int]()
    progress_thread = threading.Thread(
        target=progress_worker, args=(progress_queue, content_length), daemon=True
    )
    progress_thread.start()
    segment_size = content_length // max_workers
    segments: list[tuple[int, int]] = [
        (start, min(start + segment_size, content_length))
        for start in range(0, content_length, segment_size)
    ]
    with ThreadPoolExecutor(max_workers) as ex:
        try:
            futures = []
            for start, end in segments:
                future = ex.submit(
                    worker,
                    req,
                    dest_part,
                    start,
                    end,
                    progress_queue,
                )
                futures.append(future)
            wait(futures)
            progress_queue.shutdown()
            progress_thread.join()
        except KeyboardInterrupt:
            print("Shutting down gracefully")
            progress_queue.shutdown()
            progress_thread.join(timeout=0)
            ex.shutdown(wait=False)
            dest_part.unlink(missing_ok=True)
            dest.unlink(missing_ok=True)
    return dest
