import asyncio
import base64
import errno
import gc
import io
import json
import os
import pathlib
import re
import shutil
import stat
import tempfile
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import fitz
from json_repair import repair_json
from loguru import logger

from ..static_visual_format.models import ImageAnalysisService


@dataclass
class PageContent:
    """Represents extracted content from a single PDF page."""

    page_num: int
    content: dict[str, Any]
    type: str = "Slide"


class PDFSplitter:
    """Splits PDF into individual pages."""

    @staticmethod
    def split(pdf_path: pathlib.Path, output_dir: pathlib.Path) -> None:
        """Split PDF into individual pages.

        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save page files
        """
        if output_dir.exists():
            safe_rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        document = fitz.open(pdf_path)
        try:
            for page_num in range(document.page_count):
                output_file = output_dir / f"page_{page_num + 1}.pdf"
                pdf_writer = fitz.open()
                try:
                    pdf_writer.insert_pdf(
                        document, from_page=page_num, to_page=page_num
                    )
                    pdf_writer.save(output_file)
                finally:
                    pdf_writer.close()
        finally:
            document.close()

    @staticmethod
    def get_sorted_pages(directory: pathlib.Path) -> list[str]:
        """Get sorted list of page files."""

        def extract_page_number(filename: str) -> int:
            match = re.search(r"page_(\d+)\.pdf", filename)
            return int(match.group(1)) if match else 0

        return sorted(os.listdir(directory), key=extract_page_number)


class PageProcessor:
    """Processes individual PDF pages."""

    def __init__(self, image_service: ImageAnalysisService):
        """Initialize page processor.

        Args:
            image_service: Image analysis service instance for LLM-based processing
        """
        self.image_service = image_service

    def process(self, page_path: str, page_num: int) -> PageContent:
        """Process a single PDF page.

        Args:
            page_path: Path to page PDF file
            page_num: Page number

        Returns:
            PageContent with extracted data

        Raises:
            RuntimeError: If page processing fails
        """
        try:
            # Convert page to image and analyze
            encoded_image = self._page_to_image(page_path)
            raw_data = self.image_service.analyze_with_agent(
                encoded_image, image_type="Slides"
            )

            # Parse model output
            parsed_content = self._parse_output(raw_data, page_num)

            return PageContent(page_num=page_num, content=parsed_content)
        except Exception as e:
            logger.error(f"Error processing page {page_num}: {e}", exc_info=True)
            raise RuntimeError(f"Failed to process page {page_num}: {e}") from e

    async def aprocess(self, page_path: str, page_num: int) -> PageContent:
        """Async: Process a single PDF page.

        Args:
            page_path: Path to page PDF file
            page_num: Page number

        Returns:
            PageContent with extracted data

        Raises:
            RuntimeError: If page processing fails
        """
        import asyncio

        try:
            # Convert page to image (quick sync operation - run in thread)
            encoded_image = await asyncio.to_thread(self._page_to_image, page_path)

            # Analyze with LLM (async)
            raw_data = await self.image_service.aanalyze_with_agent(
                encoded_image, image_type="Slides"
            )

            # Parse model output (sync, quick)
            parsed_content = self._parse_output(raw_data, page_num)

            return PageContent(page_num=page_num, content=parsed_content)
        except Exception as e:
            logger.error(f"Error processing page {page_num}: {e}", exc_info=True)
            raise RuntimeError(f"Failed to process page {page_num}: {e}") from e

    @staticmethod
    def _page_to_image(page_path: str) -> str:
        """Convert PDF page to base64-encoded image."""
        document = fitz.open(page_path)
        try:
            page = document[0]
            pix = page.get_pixmap()
            png_bytes = pix.tobytes("png")
            image_bytes = io.BytesIO(png_bytes)
            try:
                encoded_image = base64.b64encode(image_bytes.getvalue()).decode("utf-8")
            finally:
                image_bytes.close()
            del png_bytes
            gc.collect()
            return encoded_image
        finally:
            document.close()
            gc.collect()

    @staticmethod
    def _parse_output(raw_data: str | dict, page_num: int) -> dict[str, Any]:
        """Parse model output into structured format."""
        if isinstance(raw_data, dict):
            return raw_data

        if not isinstance(raw_data, str):
            logger.warning(
                f"Unexpected data type for page {page_num}: {type(raw_data)}"
            )
            return {"error": "Unexpected data type from model"}

        text = raw_data.strip()

        # Remove markdown fences
        if text.startswith("```json"):
            text = text[len("```json") :].strip()
        if text.startswith("```"):
            text = text[len("```") :].strip()
        if text.endswith("```"):
            text = text[:-3].strip()

        if not text:
            logger.warning(f"Empty content for page {page_num}")
            return {"error": "Empty content from model"}

        try:
            return json.loads(repair_json(text, return_objects=False))
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed for page {page_num}: {e}")
            return {"error": "JSON parsing failed", "raw": text[:500]}


class LlmPDFReader:
    """Main PDF reader with LLM-based image analysis."""

    def __init__(
        self,
        image_service: ImageAnalysisService,
        progress_interval: int = 1,
        progress_callback: Callable[[int, int, str | None], None] | None = None,
    ):
        """Initialize PDF reader.

        Args:
            image_service: Image analysis service instance (required for LLM-based processing)
            progress_interval: Log progress every N pages
            progress_callback: Optional callback for progress reporting.
                               Signature: (current: int, total: int, message: str | None) -> None
        """
        self.image_service = image_service
        self.progress_interval = progress_interval
        self.progress_callback = progress_callback
        self._splitter = PDFSplitter

    def read(
        self, pdf_path: str, output_path: str | None = None
    ) -> list[dict[str, Any]] | str:
        """Read and process PDF file.

        Args:
            pdf_path: Path to PDF file
            output_path: Optional path to write results incrementally. If provided,
                        results are written in batches and path is returned.

        Returns:
            List of page dictionaries if output_path is None, otherwise path to output file

        Raises:
            RuntimeError: If processing fails
        """
        # Setup
        pdf_name = pathlib.Path(pdf_path).stem
        tmp_dir = self._create_temp_dir(pdf_name)

        try:
            # Split PDF
            self._splitter.split(pathlib.Path(pdf_path), tmp_dir)
            page_files = self._splitter.get_sorted_pages(tmp_dir)

            # Process pages
            processor = PageProcessor(self.image_service)

            if output_path:
                # Process in batches and write to file
                self._process_all_pages_to_file(
                    tmp_dir, page_files, processor, output_path
                )
                return output_path
            else:
                results = self._process_all_pages(tmp_dir, page_files, processor)
                return results

        except Exception as e:
            logger.error(f"Error processing PDF: {e}", exc_info=True)
            raise RuntimeError(f"Failed to process PDF: {e}") from e

        finally:
            if tmp_dir.exists():
                safe_rmtree(tmp_dir)

    async def aread(
        self, pdf_path: str, output_path: str | None = None
    ) -> list[dict[str, Any]] | str:
        """Async: Read and process PDF file.

        Args:
            pdf_path: Path to PDF file
            output_path: Optional path to write results incrementally. If provided,
                        results are written in batches and path is returned.

        Returns:
            List of page dictionaries if output_path is None, otherwise path to output file

        Raises:
            RuntimeError: If processing fails
        """
        # Setup
        pdf_name = pathlib.Path(pdf_path).stem
        tmp_dir = self._create_temp_dir(pdf_name)

        try:
            # Split PDF (sync, fast operation - run in thread)
            await asyncio.to_thread(
                self._splitter.split, pathlib.Path(pdf_path), tmp_dir
            )
            page_files = self._splitter.get_sorted_pages(tmp_dir)
            # Process pages
            processor = PageProcessor(self.image_service)

            if output_path:
                # Process in batches and write to file
                await self._aprocess_all_pages_to_file(
                    tmp_dir, page_files, processor, output_path
                )
                return output_path
            else:
                # Process all pages in memory (legacy behavior)
                results = await self._aprocess_all_pages(tmp_dir, page_files, processor)
                return results

        except Exception as e:
            logger.error(f"Error processing PDF: {e}", exc_info=True)
            raise RuntimeError(f"Failed to process PDF: {e}") from e

        finally:
            if tmp_dir.exists():
                safe_rmtree(tmp_dir)

    @staticmethod
    def _create_temp_dir(pdf_name: str) -> pathlib.Path:
        """Create temporary directory."""
        tmp_dir = pathlib.Path(tempfile.mkdtemp(prefix=f"donkit_pdf_{pdf_name}_"))
        tmp_dir.mkdir(parents=True, exist_ok=True)
        return tmp_dir

    def _process_all_pages(
        self, tmp_dir: pathlib.Path, page_files: list[str], processor: PageProcessor
    ) -> list[dict[str, Any]]:
        """Process all pages in parallel using threading."""
        results = []
        threads = []
        lock = threading.Lock()
        start_time = time.time()

        # Семафор для ограничения количества одновременных потоков
        semaphore = threading.Semaphore(4)

        def process_page_thread(page_num: int, page_file: str):
            """Process single page in thread."""
            with semaphore:
                try:
                    page_path = tmp_dir / page_file
                    page_content = processor.process(str(page_path), page_num)

                    with lock:
                        results.append(
                            {
                                "page": page_content.page_num,
                                "type": page_content.type,
                                "content": page_content.content,
                            }
                        )

                        # Progress logging and reporting
                        processed = len(results)
                        if processed % self.progress_interval == 0 or processed in [
                            1,
                            5,
                            15,
                            25,
                        ]:
                            elapsed = time.time() - start_time
                            avg_time = elapsed / processed
                            remaining = len(page_files) - processed
                            est_remaining = remaining * avg_time
                            msg = (
                                f"{processed}/{len(page_files)} pages "
                                f"({elapsed:.1f}s elapsed, ~{est_remaining:.1f}s remaining)"
                            )
                            # Report progress via callback if provided
                            if self.progress_callback:
                                self.progress_callback(processed, len(page_files), msg)

                        # Garbage collection
                        if processed % 5 == 0:
                            gc.collect()

                except Exception as e:
                    logger.error(f"Error processing page {page_num}: {e}")
                    with lock:
                        results.append(
                            {
                                "page": page_num,
                                "type": "Error",
                                "content": f"Error processing page: {str(e)}",
                            }
                        )

        # Start threads for all pages
        for page_num, page_file in enumerate(page_files, start=1):
            thread = threading.Thread(
                target=process_page_thread, args=(page_num, page_file)
            )
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Sort results by page number
        results.sort(key=lambda x: x.get("page", 0))

        return results

    async def _aprocess_all_pages(
        self, tmp_dir: pathlib.Path, page_files: list[str], processor: PageProcessor
    ) -> list[dict[str, Any]]:
        """Async: Process all pages in parallel using asyncio."""
        start_time = time.time()
        semaphore = asyncio.Semaphore(20)  # Limit concurrent LLM calls
        results = []
        lock = asyncio.Lock()

        async def process_one_page(page_num: int, page_file: str):
            """Process single page with semaphore."""
            async with semaphore:
                try:
                    page_path = tmp_dir / page_file
                    page_content = await processor.aprocess(str(page_path), page_num)

                    async with lock:
                        results.append(
                            {
                                "page": page_content.page_num,
                                "type": page_content.type,
                                "content": page_content.content,
                            }
                        )

                        # Progress logging and reporting
                        processed = len(results)
                        if processed % self.progress_interval == 0 or processed in [
                            1,
                            5,
                            15,
                            25,
                        ]:
                            elapsed = time.time() - start_time
                            avg_time = elapsed / processed
                            remaining = len(page_files) - processed
                            est_remaining = remaining * avg_time
                            msg = (
                                f"{processed}/{len(page_files)} pages "
                                f"({elapsed:.1f}s elapsed, ~{est_remaining:.1f}s remaining)"
                            )
                            # Report progress via callback if provided
                            if self.progress_callback:
                                self.progress_callback(processed, len(page_files), msg)

                        # Garbage collection
                        if processed % 5 == 0:
                            gc.collect()

                except Exception as e:
                    logger.error(f"Error processing page {page_num}: {e}")
                    async with lock:
                        results.append(
                            {
                                "page": page_num,
                                "type": "Error",
                                "content": f"Error processing page: {str(e)}",
                            }
                        )

        # Create tasks for all pages
        tasks = [
            process_one_page(page_num, page_file)
            for page_num, page_file in enumerate(page_files, start=1)
        ]

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)

        # Sort results by page number
        results.sort(key=lambda x: x.get("page", 0))

        return results

    def _process_all_pages_to_file(
        self,
        tmp_dir: pathlib.Path,
        page_files: list[str],
        processor: PageProcessor,
        output_path: str,
        batch_size: int = 20,
    ) -> None:
        """Process all pages in batches and write to file incrementally.

        Supports resume: if output file exists and contains partial results,
        continues from last processed page.

        Args:
            tmp_dir: Temporary directory with split PDF pages
            page_files: List of page file names
            processor: PageProcessor instance
            output_path: Path to output JSON file
            batch_size: Number of pages to process per batch (default: 20)
        """
        start_time = time.time()
        output_file = pathlib.Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Check for existing partial results
        already_processed = set()
        resume_mode = False

        if output_file.exists():
            try:
                # Try to read existing file and extract processed pages
                with open(output_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Try to parse as JSON
                    if content.strip():
                        # Remove incomplete JSON (might be cut off)
                        if not content.rstrip().endswith("]}"):
                            # Find last complete page entry
                            last_complete = content.rfind("}")
                            if last_complete > 0:
                                content = content[: last_complete + 1]

                        # Parse JSON to get processed pages
                        try:
                            # Quick parse to find page numbers
                            page_matches = re.findall(r'"page":\s*(\d+)', content)
                            already_processed = set(int(p) for p in page_matches)
                            if already_processed:
                                resume_mode = True
                                logger.info(
                                    f"🔄 Resume mode: Found {len(already_processed)} already processed pages"
                                )
                                logger.info(
                                    f"   Pages: {sorted(already_processed)[:10]}{'...' if len(already_processed) > 10 else ''}"
                                )
                        except Exception as e:
                            logger.warning(
                                f"Could not parse existing file for resume: {e}"
                            )
            except Exception as e:
                logger.warning(f"Could not read existing file for resume: {e}")

        # Start fresh if not resuming
        total_processed = len(already_processed)

        if not resume_mode:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write('{"content": [\n')

        # Process in batches
        for batch_start in range(0, len(page_files), batch_size):
            batch_end = min(batch_start + batch_size, len(page_files))
            batch_files = page_files[batch_start:batch_end]
            results = []
            threads = []
            lock = threading.Lock()
            semaphore = threading.Semaphore(4)

            def process_page_thread(page_num: int, page_file: str):
                """Process single page in thread."""
                nonlocal results
                with semaphore:
                    try:
                        page_path = tmp_dir / page_file
                        page_content = processor.process(str(page_path), page_num)

                        with lock:
                            results.append(
                                {
                                    "page": page_content.page_num,
                                    "type": page_content.type,
                                    "content": page_content.content,
                                }
                            )
                            processed = total_processed + len(results)
                            if processed % self.progress_interval == 0 or processed in [
                                1,
                                5,
                                15,
                                25,
                            ]:
                                elapsed = time.time() - start_time
                                avg_time = elapsed / processed
                                remaining = len(page_files) - processed
                                est_remaining = remaining * avg_time
                                msg = (
                                    f"{processed}/{len(page_files)} pages "
                                    f"({elapsed:.1f}s elapsed, ~{est_remaining:.1f}s remaining)"
                                )
                                if self.progress_callback:
                                    self.progress_callback(
                                        processed, len(page_files), msg
                                    )

                    except Exception as e:
                        logger.error(f"Error processing page {page_num}: {e}")
                        with lock:
                            results.append(
                                {
                                    "page": page_num,
                                    "type": "Error",
                                    "content": f"Error processing page: {str(e)}",
                                }
                            )

            # Start threads for batch (skip already processed pages)
            for idx, page_file in enumerate(batch_files):
                page_num = batch_start + idx + 1

                # Skip if already processed
                if page_num in already_processed:
                    continue

                thread = threading.Thread(
                    target=process_page_thread, args=(page_num, page_file)
                )
                threads.append(thread)
                thread.start()

            # Wait for all threads in batch to complete
            for thread in threads:
                thread.join()

            if not results:
                continue

            # Sort batch results by page number
            results.sort(key=lambda x: x.get("page", 0))

            # Write batch to file
            if resume_mode:
                # In resume mode, we need to reopen file and fix JSON structure
                with open(output_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Remove closing ]} if present
                if content.rstrip().endswith("]}"):
                    content = content.rstrip()[:-2].rstrip()
                elif content.rstrip().endswith("]"):
                    content = content.rstrip()[:-1].rstrip()

                # Write back with new results
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(content)
                    for result in results:
                        f.write(",\n")
                        json.dump(result, f, ensure_ascii=False, indent=2)

                resume_mode = False  # Only first batch needs special handling
            else:
                # Normal append mode
                with open(output_file, "a", encoding="utf-8") as f:
                    for i, result in enumerate(results):
                        if total_processed > 0 or i > 0:
                            f.write(",\n")
                        json.dump(result, f, ensure_ascii=False, indent=2)

            total_processed += len(results)

            # Clear memory
            del results
            gc.collect()
        # Close JSON array
        with open(output_file, "a", encoding="utf-8") as f:
            f.write("\n]}")

    async def _aprocess_all_pages_to_file(
        self,
        tmp_dir: pathlib.Path,
        page_files: list[str],
        processor: PageProcessor,
        output_path: str,
        batch_size: int = 20,
    ) -> None:
        """Async: Process all pages in batches and write to file incrementally."""
        start_time = time.time()
        output_file = pathlib.Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Start fresh
        with open(output_file, "w", encoding="utf-8") as f:
            f.write('{"content": [\n')

        # Process in batches
        total_processed = 0
        for batch_start in range(0, len(page_files), batch_size):
            batch_end = min(batch_start + batch_size, len(page_files))
            batch_files = page_files[batch_start:batch_end]
            semaphore = asyncio.Semaphore(10)
            results = []
            lock = asyncio.Lock()

            async def process_one_page(page_num: int, page_file: str):
                """Process single page with semaphore."""
                async with semaphore:
                    try:
                        page_path = tmp_dir / page_file
                        page_content = await processor.aprocess(
                            str(page_path), page_num
                        )

                        async with lock:
                            results.append(
                                {
                                    "page": page_content.page_num,
                                    "type": page_content.type,
                                    "content": page_content.content,
                                }
                            )

                            # Progress logging and reporting
                            processed = total_processed + len(results)
                            if processed % self.progress_interval == 0 or processed in [
                                1,
                                5,
                                15,
                                25,
                            ]:
                                elapsed = time.time() - start_time
                                avg_time = elapsed / processed
                                remaining = len(page_files) - processed
                                est_remaining = remaining * avg_time
                                msg = (
                                    f"{processed}/{len(page_files)} pages "
                                    f"({elapsed:.1f}s elapsed, ~{est_remaining:.1f}s remaining)"
                                )
                                # Report progress via callback if provided
                                if self.progress_callback:
                                    self.progress_callback(
                                        processed, len(page_files), msg
                                    )

                    except Exception as e:
                        logger.error(f"Error processing page {page_num}: {e}")
                        async with lock:
                            results.append(
                                {
                                    "page": page_num,
                                    "type": "Error",
                                    "content": f"Error processing page: {str(e)}",
                                }
                            )

            # Start tasks for batch
            tasks = [
                process_one_page(batch_start + idx + 1, page_file)
                for idx, page_file in enumerate(batch_files)
            ]

            # Wait for all tasks in batch to complete
            await asyncio.gather(*tasks)

            # Sort batch results by page number
            results.sort(key=lambda x: x.get("page", 0))

            # Write batch to file
            with open(output_file, "a", encoding="utf-8") as f:
                for idx, result in enumerate(results):
                    if total_processed > 0 or idx > 0:
                        f.write(",\n")
                    json.dump(result, f, ensure_ascii=False, indent=2)

            total_processed += len(results)

            # Memory cleanup
            if total_processed % 10 == 0:
                gc.collect()

        # Close JSON structure
        with open(output_file, "a", encoding="utf-8") as f:
            f.write("\n]}")


def safe_rmtree(path: pathlib.Path) -> None:
    """Safely remove directory tree with Windows-compatible error handling.

    On Windows, files might still be locked by the system. This function
    handles permission errors by trying to change file permissions before removal.

    Args:
        path: Path to directory to remove
    """
    import gc
    import platform

    # On Windows, force garbage collection and add small delay to release file handles
    if platform.system() == "Windows":
        gc.collect()
        time.sleep(0.1)  # 100ms delay for Windows to release file handles

    def handle_remove_error(func, filepath, exc_info):
        """Handle errors during directory removal on Windows."""
        # If permission error, try to change permissions and retry
        if exc_info[1].errno == errno.EACCES:
            try:
                os.chmod(filepath, stat.S_IWRITE)
                time.sleep(0.05)  # Small delay before retry
                func(filepath)
            except Exception as e:
                logger.warning(f"Could not remove {filepath}: {e}")
        else:
            logger.warning(f"Could not remove {filepath}: {exc_info[1]}")

    try:
        shutil.rmtree(path, onerror=handle_remove_error)
    except Exception as e:
        logger.warning(f"Failed to cleanup directory {path}: {e}")
