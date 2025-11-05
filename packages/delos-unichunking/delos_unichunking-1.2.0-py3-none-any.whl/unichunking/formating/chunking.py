"""Chhunk formating."""

import asyncio
import copy
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from llmax import tokens

from unichunking.settings import unisettings
from unichunking.tools import clean_chunk
from unichunking.types import Chunk, StatusManager, SubChunk
from unichunking.utils import get_profiler

from .pages import edit_positions_on_page
from .subchunking import extract_subchunks

Action = Literal["describe", "transcribe"]


def split_chunks_with_overlap(
    chunks: list[SubChunk],
    page_id: int,
    k_min: int = unisettings.chunking.DEFAULT_K_MIN,
    k_max: int = unisettings.chunking.DEFAULT_K_MIN
    + unisettings.chunking.DEFAULT_MIN_MAX_GAP,
    overlap: int = unisettings.chunking.DEFAULT_OVERLAP,
) -> list[Chunk]:
    """Splits the text allowing some overlapping.

    - chunks: les différents chunks extraits du document
    - k_min: nombre de tokens minimal par chunk
    - k_max: nombre maximal de tokens par chunk
    - overlap: nombre de caractères pour l'overlap.
    """
    if not (0 < k_min <= k_max) or overlap < 0:
        message = "Please ensure that 0 < K_MIN <= K_MAX and that overlap >= 0"
        raise ValueError(message)

    chunks_final: list[Chunk] = []

    current_chunk = ""
    current_positions = []

    for it, chunk in enumerate(chunks):
        if tokens.count(current_chunk) + tokens.count(
            chunk.content,
        ) < k_max or it + 1 == len(chunks):
            current_chunk += f" {chunk.content}"
            current_positions.append(chunk.position.to_dict())
            if tokens.count(current_chunk) >= k_min or (it + 1 == len(chunks)):
                curr_chunk = Chunk(
                    chunk_num=len(chunks_final) + 1,
                    content=current_chunk,
                    page_num=page_id,
                    positions=copy.deepcopy(current_positions),
                    embedding=None,
                    chunk_uid=uuid4(),
                    num_tokens=tokens.count(current_chunk),
                )
                curr_chunk = clean_chunk(curr_chunk)
                if curr_chunk.content:
                    chunks_final.append(curr_chunk)
                current_positions = [chunk.position.to_dict()]
                current_chunk = current_chunk[-overlap:] if overlap else ""

        else:
            curr_chunk = Chunk(
                chunk_num=len(chunks_final) + 1,
                content=current_chunk,
                page_num=page_id,
                positions=copy.deepcopy(current_positions),
                embedding=None,
                chunk_uid=uuid4(),
                num_tokens=tokens.count(current_chunk),
            )
            curr_chunk = clean_chunk(curr_chunk)
            if curr_chunk.content:
                chunks_final.append(curr_chunk)
            current_positions = [chunk.position.to_dict()]
            current_chunk = (
                current_chunk[-overlap:] + chunk.content if overlap else chunk.content
            )

    return chunks_final


async def default_function(base64_image: str) -> str:  # noqa: ARG001
    """Default function."""
    return ""


async def build_chunked_pages(
    path: Path,
    k_min: int = unisettings.chunking.DEFAULT_K_MIN,
    overlap: int = unisettings.chunking.DEFAULT_OVERLAP,
    status_manager: Any = None,
) -> tuple[
    list[list[Chunk]],
    int,
    list[list[tuple[float, float, float, float]]],
    dict[int, str],
    bool,
]:
    """Returns a list of Pages and Chunks objects, once extracted, merged when necessary, cleaned and embedded."""
    k_max = k_min + unisettings.chunking.DEFAULT_MIN_MAX_GAP

    extension = path.suffix[1:].lower()
    if unisettings.files.CONTENT_TYPES[extension] == "application/docx":
        extension = "docx"

    chunks: list[Chunk] = []
    chunks_pages: list[list[Chunk]] = []

    if not status_manager:
        status_manager = StatusManager(task="Subchunk extraction")
    status_manager.start = 0
    status_manager.end = 40

    (
        chunks_extracted,
        num_pages_default,
        pdf_images_vault,
        docx_images_vault,
        success,
    ) = await extract_subchunks(
        path,
        k_max=k_max,
        status_manager=status_manager,
    )

    if not success:
        return [[]], 0, [], {}, False

    pages_numbers = [ch.page for ch in chunks_extracted]
    if len(pages_numbers) == 0 and num_pages_default == 0:
        return [[]], 0, [], {}, True

    num_pages = max(pages_numbers) + 1 if len(pages_numbers) > 0 else num_pages_default

    profiler = get_profiler()

    status_manager.task = "Chunk formating"
    status_manager.start = 40
    status_manager.end = 100

    with profiler.measure("chunking.page_loop_total"):
        for page_id in range(num_pages):
            # Yield to event loop every few pages to stay responsive
            if page_id % 3 == 0:
                await asyncio.sleep(0)

            if page_id % int(num_pages / 30 + 1) == 0:
                page_progress = int((page_id + 1) / num_pages * 100)
                await status_manager.update_status(
                    progress=page_progress,
                    start=status_manager.start,
                    end=status_manager.end,
                )

            with profiler.measure("chunking.filter_relevant_chunks"):
                relevant_chunks = [ch for ch in chunks_extracted if ch.page == page_id]

            with profiler.measure("chunking.split_chunks_with_overlap"):
                # Run blocking token counting in thread pool to avoid blocking event loop
                res = await asyncio.to_thread(
                    split_chunks_with_overlap,
                    relevant_chunks,
                    page_id + 1,
                    k_min,
                    k_max,
                    overlap,
                )
            chunks.extend(res)
            chunks_pages.append(res)

    with profiler.measure("chunking.edit_positions_on_page"):
        # Run blocking position editing in thread pool
        result_chunks = await asyncio.to_thread(
            edit_positions_on_page, chunks_pages, "pdf",
        )

    return (
        result_chunks,
        num_pages,
        pdf_images_vault,
        docx_images_vault,
        success,
    )
