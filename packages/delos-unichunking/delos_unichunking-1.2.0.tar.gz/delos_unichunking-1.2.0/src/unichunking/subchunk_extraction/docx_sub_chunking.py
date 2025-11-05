"""Extract subchunks from DOCX file."""

import base64
import io
from pathlib import Path
from typing import Any

import pymupdf
from docx import Document
from PIL import Image

from unichunking.subchunk_extraction.pdf_sub_chunking import get_significant_images
from unichunking.tools import convert_file
from unichunking.types import (
    ChunkPosition,
    SubChunk,
)
from unichunking.utils import logger


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


async def _retrieve_text_subchunks(
    path: Path,
    status_manager: Any,
) -> tuple[
    list[list[list[list[SubChunk]]]],
    int,
]:
    chunks: list[list[list[list[SubChunk]]]] = []
    all_significant_images: list[list[tuple[float, float, float, float]]] = []
    idx = 0

    with pymupdf.Document(path) as doc:
        num_pages = int(doc.page_count)  # type: ignore
        image_counter = 0
        for page_num in range(num_pages):
            if page_num % (num_pages / 17 + 1) == 0:
                page_progress = int((page_num + 1) / num_pages * 75)
                await status_manager.update_status(
                    progress=page_progress,
                    start=status_manager.start,
                    end=status_manager.end,
                )

            page_chunks: list[list[list[SubChunk]]] = []
            page = doc.load_page(page_num)  # type: ignore

            significant_images = sorted(
                get_significant_images(page),
                key=lambda b: (b[1], b[0]),
            )

            all_significant_images.append(significant_images.copy())

            textpage: Any = page.get_textpage()  # type: ignore

            page = textpage.extractDICT(sort=False)
            width, height = page["width"], page["height"]
            blocks = page["blocks"]

            for block in blocks:
                block_chunks: list[list[SubChunk]] = []
                lines = block["lines"]
                for line in lines:
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

    return chunks, num_pages


async def extract_subchunks_docx(
    path: Path,
    extension: str,
    status_manager: Any,
) -> tuple[list[SubChunk], int, dict[int, str]]:
    """Filetype-specific function : extracts subchunks from a DOCX file."""
    images: list[str] = []

    if extension != "docx":
        new_path = await convert_file(path, "docx")
        if new_path is not None:
            path = new_path
        else:
            return [], 0, {}

    doc = Document(str(path))
    img_idx = 0
    image_rels: dict[str, str] = {}

    dict_base64_image: dict[int, str] = {}
    for rel in doc.part.rels.values():
        if "image" in rel.reltype:
            try:
                image_part = rel.target_part
                image_bytes = image_part.blob

                with Image.open(io.BytesIO(image_bytes)) as im:
                    img_width_px, img_height_px = im.size
                    dpi = im.info.get("dpi", (96, 96))
                    dpi_x, dpi_y = dpi

                    img_width_in = img_width_px / dpi_x
                    img_height_in = img_height_px / dpi_y

                    section = doc.sections[0]
                    page_width_in = (
                        section.page_width.inches if section.page_width else 1
                    )
                    page_height_in = (
                        section.page_height.inches if section.page_height else 1
                    )

                    rel_width = img_width_in / page_width_in
                    rel_height = img_height_in / page_height_in

                min_ratio = 0.15
                if rel_width > min_ratio or rel_height > min_ratio:
                    base64_image = base64.b64encode(image_bytes).decode("utf-8")

                    image_rels[rel.rId] = f"{img_idx}"
                    images.append(f"img_desc_{img_idx} end_img_desc_{img_idx}")

                    dict_base64_image[img_idx] = base64_image

                    img_idx += 1

            except Exception as e:  # noqa: BLE001
                logger.debug(f"Image couldn't be processed : {e}")

    path_pdf = await convert_file(path, "pdf")
    if path_pdf is None:
        return [], 0, {}

    chunks, num_pages = await _retrieve_text_subchunks(
        path=path_pdf,
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

    return flattened_chunks, num_pages, dict_base64_image
