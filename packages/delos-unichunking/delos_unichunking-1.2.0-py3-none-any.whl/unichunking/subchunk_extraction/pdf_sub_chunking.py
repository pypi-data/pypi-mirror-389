"""Extract subchunks from PDF file."""

import asyncio
from pathlib import Path
from typing import Any

import fitz
import pymupdf

from unichunking.types import ChunkPosition, SubChunk
from unichunking.utils import get_profiler

MIN_PIXELS: int = 128


def get_text_bbox_area(page: Any) -> float:
    """Return the area of the union of all text bounding boxes."""
    blocks = page.get_text("blocks")
    if not blocks:
        return 0.0

    x0 = min(b[0] for b in blocks)
    y0 = min(b[1] for b in blocks)
    x1 = max(b[2] for b in blocks)
    y1 = max(b[3] for b in blocks)

    return (x1 - x0) * (y1 - y0)


def is_scanned_page_with_text(page: Any, min_ratio: float = 0.95) -> bool:
    """Checks if the page contains a large image with text.

    Return True if the page contains at least one drawn image that covers at least
    `min_ratio` of the page area AND the page also has text.
    Otherwise, return False.
    """
    page_rect = page.rect
    page_area = page_rect.width * page_rect.height

    text = page.get_text("text")
    has_text = bool(text.strip())

    for block in page.get_text("rawdict")["blocks"]:
        if block["type"] == 1:
            bbox: Any = fitz.Rect(block["bbox"])
            img_area = bbox.width * bbox.height

            if img_area / page_area >= min_ratio:
                return has_text

    return False


def _handle_line(
    line: Any,
    width: float,
    height: float,
    subchunk_idx: int,
    page_num: int,
    file_name: str,
    sig_images_sorted: list[tuple[float, float, float, float]],
    image_counter: int,
) -> tuple[list[SubChunk], int, int]:
    line_chunks: list[SubChunk] = []

    for span in line["spans"]:
        text = str(span["text"].replace("�", " ").strip())
        font: Any = span["font"]
        bbox: Any = span["bbox"]

        if "bold" in font.lower():
            text = f"**{text}**"

        if text:
            x0, y0, x1, y1 = bbox

            while sig_images_sorted and sig_images_sorted[0][1] <= y0:
                ix0, iy0, ix1, iy1 = sig_images_sorted.pop(0)
                position = ChunkPosition(
                    x0=ix0 / width,
                    y0=iy0 / height,
                    x1=ix1 / width,
                    y1=iy1 / height,
                )
                placeholder = f"img_desc_{image_counter} end_img_desc_{image_counter}"
                line_chunks.append(
                    SubChunk(
                        subchunk_id=subchunk_idx,
                        content=placeholder,
                        page=page_num,
                        position=position,
                        file_name=file_name,
                    ),
                )
                subchunk_idx += 1
                image_counter += 1

            position = ChunkPosition(
                x0=x0 / width,
                y0=y0 / height,
                x1=x1 / width,
                y1=y1 / height,
            )
            line_chunks.append(
                SubChunk(
                    subchunk_id=subchunk_idx,
                    content=text,
                    page=page_num,
                    position=position,
                    file_name=file_name,
                ),
            )
            subchunk_idx += 1

    return line_chunks, subchunk_idx, image_counter


def get_significant_images(
    page: Any,
    min_ratio: float = 0.15,
    overlap_threshold: float = 0.2,
) -> list[tuple[float, float, float, float]]:
    """Return a list of bounding boxes of significant images on the page."""
    page_width, page_height = page.rect.width, page.rect.height
    significant_bboxes: list[tuple[float, float, float, float]] = []

    img_refs = page.get_image_info(xrefs=True)
    if not img_refs:
        return []

    for img in img_refs:
        x0, y0, x1, y1 = img["bbox"]
        w, h = abs(x1 - x0), abs(y1 - y0)
        if (w / page_width) >= min_ratio or (h / page_height) >= min_ratio:
            significant_bboxes.append((x0, y0, x1, y1))

    significant_bboxes.sort(key=lambda b: (b[1], b[0]))

    merged: list[tuple[float, float, float, float]] = []

    def overlap_area(
        box1: tuple[float, float, float, float],
        box2: tuple[float, float, float, float],
    ) -> float:
        x0 = max(box1[0], box2[0])
        y0 = max(box1[1], box2[1])
        x1 = min(box1[2], box2[2])
        y1 = min(box1[3], box2[3])
        if x1 <= x0 or y1 <= y0:
            return 0
        return (x1 - x0) * (y1 - y0)

    for box in significant_bboxes:
        if not merged:
            merged.append(box)
            continue

        last = merged[-1]
        inter_area = overlap_area(last, box)
        smaller_area = min(
            (last[2] - last[0]) * (last[3] - last[1]),
            (box[2] - box[0]) * (box[3] - box[1]),
        )

        if inter_area / smaller_area > overlap_threshold:
            merged[-1] = (
                min(last[0], box[0]),
                min(last[1], box[1]),
                max(last[2], box[2]),
                max(last[3], box[3]),
            )
        else:
            merged.append(box)

    return merged


async def _retrieve_text_subchunks(
    path: Path,
    status_manager: Any,
) -> tuple[
    list[list[list[list[SubChunk]]]],
    int,
    list[list[tuple[float, float, float, float]]],
]:
    profiler = get_profiler()
    chunks: list[list[list[list[SubChunk]]]] = []
    all_significant_images: list[list[tuple[float, float, float, float]]] = []
    idx = 0

    with profiler.measure("pdf.open_document"):
        doc = pymupdf.Document(path)

    with doc:
        num_pages = int(doc.page_count)  # type: ignore
        for page_num in range(num_pages):
            # Yield to event loop every few pages to stay responsive
            if page_num % 3 == 0:
                await asyncio.sleep(0)

            if page_num % (num_pages / 17 + 1) == 0:
                page_progress = int((page_num + 1) / num_pages * 75)
                await status_manager.update_status(
                    progress=page_progress,
                    start=status_manager.start,
                    end=status_manager.end,
                )

            page_chunks: list[list[list[SubChunk]]] = []

            with profiler.measure("pdf.load_page"):
                # Run blocking page loading in thread pool
                page = await asyncio.to_thread(doc.load_page, page_num)  # type: ignore

            with profiler.measure("pdf.get_significant_images"):
                # Run blocking image extraction in thread pool to avoid blocking event loop
                significant_images_raw = await asyncio.to_thread(
                    get_significant_images, page,
                )
                significant_images = sorted(
                    significant_images_raw,
                    key=lambda b: (b[1], b[0]),
                )
                use_text = await asyncio.to_thread(is_scanned_page_with_text, page)
                if use_text:
                    significant_images = []

                all_significant_images.append(significant_images.copy())

            with profiler.measure("pdf.extract_text"):
                # Run blocking text extraction in thread pool
                def extract_text_from_page(p: Any) -> Any:
                    textpage = p.get_textpage()
                    return textpage.extractDICT(sort=False)

                page = await asyncio.to_thread(extract_text_from_page, page)
            width, height = page["width"], page["height"]
            blocks = page["blocks"]
            image_counter = 0

            for block in blocks:
                block_chunks: list[list[SubChunk]] = []
                lines = block["lines"]
                for line in lines:
                    with profiler.measure("pdf.handle_line"):
                        line_chunks, idx, image_counter = _handle_line(
                            line=line,
                            width=width,
                            height=height,
                            subchunk_idx=idx,
                            page_num=page_num,
                            file_name=path.name,
                            image_counter=image_counter,
                            sig_images_sorted=significant_images,
                        )
                    if line_chunks:
                        block_chunks.append(line_chunks)
                if block_chunks:
                    page_chunks.append(block_chunks)

            while significant_images:
                ix0, iy0, ix1, iy1 = significant_images.pop(0)
                position = ChunkPosition(
                    x0=ix0 / width,
                    y0=iy0 / height,
                    x1=ix1 / width,
                    y1=iy1 / height,
                )
                placeholder = f"img_desc_{image_counter} end_img_desc_{image_counter}"
                img_chunk = SubChunk(
                    subchunk_id=idx,
                    content=placeholder,
                    page=page_num,
                    position=position,
                    file_name=path.name,
                )
                idx += 1
                image_counter += 1
                page_chunks.append([[img_chunk]])

            if page_chunks:
                chunks.append(page_chunks)

    return chunks, num_pages, all_significant_images


async def extract_subchunks_pdf(
    path: Path,
    status_manager: Any,
) -> tuple[list[SubChunk], int, list[list[tuple[float, float, float, float]]]]:
    """Filetype-specific function : extracts subchunks from a PDF file.

    Args:
        path: Path to the local file.
        status_manager: Optional, special object to manage task progress.
        function: Function to handle images.

    Returns:
        A list of SubChunk objects.
    """
    chunks, num_pages, all_significant_images = await _retrieve_text_subchunks(
        path=path,
        status_manager=status_manager,
    )

    flattened_chunks = [
        chunk
        for page_chunks in chunks
        for block_chunks in page_chunks
        for line_chunks in block_chunks
        for chunk in line_chunks
    ]

    progress = 100
    await status_manager.update_status(
        progress=progress,
        start=status_manager.start,
        end=status_manager.end,
    )

    return flattened_chunks, num_pages, all_significant_images
