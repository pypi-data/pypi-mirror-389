import argparse
import json
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any
from typing import Literal

from donkit.read_engine.readers.static_visual_format.models import (
    get_image_analysis_service,
)
from dotenv import find_dotenv, load_dotenv
from loguru import logger

from .readers.portable_document_format.handler import LlmPDFReader
from .readers.portable_document_format.pdf_parser import simple_pdf_read_handler
from .readers.json_document_format.handler import json_document_read_handler
from .readers.microsoft_office_sheet.handler import sheet_read_handler
from .readers.microsoft_office_document.handler import (
    document_read_handler,
    LlmDocumentReader,
)
from .readers.microsoft_office_presentation.handler import presentation_read_handler
from .readers.text_document_format.handler import text_document_read_handler
from .readers.static_visual_format.handler import image_read_handler

# Load .env file with explicit search (important for Windows)
# Try multiple locations in priority order
_env_loaded = False
for _fname in (".env.local", ".env"):
    # 1. Try current working directory
    _cwd_path = Path.cwd() / _fname
    if _cwd_path.exists():
        load_dotenv(_cwd_path, override=False)
        _env_loaded = True
    # 2. Try parent directories (walk up to 3 levels)
    _parent = Path.cwd()
    for _ in range(3):
        _parent = _parent.parent
        _parent_env = _parent / _fname
        if _parent_env.exists():
            load_dotenv(_parent_env, override=False)
            _env_loaded = True
            break
    # 3. Fallback to find_dotenv
    if not _env_loaded:
        _found = find_dotenv(filename=_fname, usecwd=True)
        if _found:
            load_dotenv(_found, override=False)
            _env_loaded = True

if not _env_loaded:
    logger.warning(
        "⚠️ No .env file found in current or parent directories. "
        "LLM-based PDF processing may not be available. "
        f"Current directory: {Path.cwd()}"
    )
    logger.remove()
    logger.configure(handlers=[{"sink": sys.stderr, "level": "DEBUG"}])
else:
    logger.remove()
    logger.configure(
        handlers=[{"sink": sys.stderr, "level": os.getenv("RAGOPS_LOG_LEVEL", "ERROR")}]
    )


class DonkitReader:
    """Main document reader orchestrator.

    Manages initialization of all services and delegates to specific readers.
    """

    def __init__(
        self,
        use_llm: bool = True,
        progress_callback: Callable[[int, int, str | None], None] | None = None,
    ) -> None:
        """Initialize DonkitReader with appropriate services based on environment.

        Args:
            use_llm: Whether to use LLM for PDF processing (default: True)
                     If False, will use simple PDF reader even if credentials are available
            progress_callback: Optional callback for progress reporting.
                               Signature: (current: int, total: int, message: str | None) -> None
        """
        self._progress_callback = progress_callback
        self._image_service = self._initialize_image_service() if use_llm else None
        self._pdf_reader = self._initialize_pdf_reader() if use_llm else None
        self._document_reader = self._initialize_document_reader() if use_llm else None

        self.readers = {
            ".txt": text_document_read_handler,
            ".json": json_document_read_handler,
            ".csv": text_document_read_handler,
            ".pdf": self._read_pdf,
            ".docx": self._read_docx,
            ".pptx": lambda p: presentation_read_handler(p, pdf_handler=self._read_pdf),
            ".xlsx": sheet_read_handler,
            ".xls": sheet_read_handler,
            ".png": image_read_handler,
            ".jpg": image_read_handler,
            ".jpeg": image_read_handler,
        }

    @staticmethod
    def _initialize_image_service():
        """Initialize image analysis service based on available credentials and use_llm flag."""
        # Check if LLM usage is disabled
        creds_keys = {
            "RAGOPS_OPENAI_API_KEY": os.getenv("RAGOPS_OPENAI_API_KEY"),
            "RAGOPS_VERTEX_CREDENTIALS": os.getenv("RAGOPS_VERTEX_CREDENTIALS"),
            "GOOGLE_APPLICATION_CREDENTIALS": os.getenv(
                "GOOGLE_APPLICATION_CREDENTIALS"
            ),
            "RAGOPS_AZURE_OPENAI_API_KEY": os.getenv("RAGOPS_AZURE_OPENAI_API_KEY"),
        }
        available_creds = [k for k, v in creds_keys.items() if v]

        if available_creds:
            logger.info(
                f"📄 Image service available (credentials: {', '.join(available_creds)})"
            )
            return get_image_analysis_service()
        else:
            logger.info("📄 No LLM credentials found, image analysis disabled")
            return None

    def _initialize_pdf_reader(self) -> LlmPDFReader | None:
        """Initialize PDF reader with image service if available."""
        if self._image_service:
            return LlmPDFReader(
                image_service=self._image_service,
                progress_callback=self._progress_callback,
            )
        return None

    def _initialize_document_reader(self) -> LlmDocumentReader | None:
        """Initialize document reader with image service if available."""
        if self._image_service:
            return LlmDocumentReader(image_service=self._image_service)
        return None

    def _read_pdf(self, path: str, output_path: str | None = None) -> list[dict] | str:
        """Read PDF using initialized PDF reader.

        Args:
            path: Path to PDF file
            output_path: Optional output path for batch processing

        Returns:
            List of dicts if output_path is None, otherwise output_path string
        """
        if self._pdf_reader:
            return self._pdf_reader.read(path, output_path=output_path)
        else:
            return simple_pdf_read_handler(path)

    async def _aread_pdf(
        self, path: str, output_path: str | None = None
    ) -> list[dict] | str:
        """Async: Read PDF using initialized PDF reader.

        Args:
            path: Path to PDF file
            output_path: Optional output path for batch processing

        Returns:
            List of dicts if output_path is None, otherwise output_path string
        """
        import asyncio

        if self._pdf_reader:
            return await self._pdf_reader.aread(path, output_path=output_path)
        else:
            return await asyncio.to_thread(simple_pdf_read_handler, path)

    def _read_docx(self, path: str, output_path: str | None = None) -> list[dict] | str:
        """Read DOCX using initialized document reader.

        Args:
            path: Path to DOCX file
            output_path: Optional output path for batch processing

        Returns:
            List of dicts if output_path is None, otherwise output_path string
        """
        if self._document_reader:
            return self._document_reader.read(path, output_path=output_path)
        else:
            return document_read_handler(path)

    def read_document(
        self,
        file_path: str,
        output_type: Literal["text", "json", "markdown"],
        output_dir: str | None = None,
    ) -> str:
        """Main method to read a document from S3 and extract its content.

        Args:
            file_path: Path to the file in S3 storage (path/to/file)
                       without bucket name
            output_type: Output format ("text", "json", or "markdown")
            output_dir: Optional custom output directory. If not provided,
                       creates 'processed/' subdirectory next to the source file.
            transition process. When we completely switch to a system with projects in companies,
            we need to make it required.

        Returns:
            Path to the processed output file in S3
        """
        try:
            # Get file extension to determine which reader to use
            file_extension = Path(file_path).suffix.lower()

            # For PDF/PPTX/DOCX with LLM and JSON output, use batch processing
            if file_extension in (".pdf", ".pptx", ".docx") and output_type == "json":
                # Check if we have LLM reader for this file type
                has_llm_reader = (
                    file_extension in (".pdf", ".pptx") and self._pdf_reader
                ) or (file_extension == ".docx" and self._document_reader)

                if has_llm_reader:
                    # Prepare output path
                    path = Path(file_path)
                    file_name = path.stem
                    if output_dir is None:
                        output_dir_path = path.parent / Path("processed")
                    else:
                        output_dir_path = Path(output_dir)
                    output_dir_path.mkdir(parents=True, exist_ok=True)
                    output_file_path = output_dir_path / f"{file_name}.json"

                    # Process with batching directly to file
                    if file_extension == ".pdf":
                        result = self._read_pdf(
                            file_path, output_path=str(output_file_path)
                        )
                    elif file_extension == ".pptx":
                        result = presentation_read_handler(
                            file_path,
                            pdf_handler=self._read_pdf,
                            output_path=str(output_file_path),
                        )
                    else:  # .docx
                        result = self._read_docx(
                            file_path, output_path=str(output_file_path)
                        )
                    return result if isinstance(result, str) else str(output_file_path)
            else:
                # Standard processing for other files
                content = self.__extract_content_sync(file_path, file_extension)
                # Process output based on requested format
                output_file_path = self._process_output(
                    content, file_path, output_type, output_dir
                )
                return output_file_path
        except Exception as e:
            raise RuntimeError(f"Failed to process document: {e!s}") from e

    def __extract_content_sync(
        self, file_path: str, file_extension: str
    ) -> str | list[dict[str, Any]]:
        """Synchronous content extraction (runs in thread pool).
        Args:
            file_path: Path to the local file
            file_extension: File extension (including the dot)
        Returns:
            Content extracted from the document (either text or structured data)
        """
        try:
            if file_extension in self.readers:
                return self.readers[file_extension](file_path)
            else:
                msg = (
                    f"Unsupported file extension: {file_extension}"
                    f"Supported extensions: {list(self.readers.keys())}"
                )
                raise ValueError(msg)
        except Exception:
            raise

    @staticmethod
    def _process_output(
        content: str | list[dict[str, Any]],
        file_path: str,
        output_type: Literal["text", "json", "markdown"],
        output_dir: str | None = None,
    ) -> str:
        """Process extracted content.

        Args:
            content: Extracted content (text or structured data)
            file_path: Original S3 object key
            output_type: Output format type
            output_dir: Optional custom output directory
        """
        # Create output file name based on original file and output type
        path = Path(file_path)
        file_name = path.stem  # Get filename without extension

        # Use custom output_dir if provided, otherwise default to processed/ subdirectory
        if output_dir is None:
            output_dir = str(path.parent / Path("processed"))
        else:
            output_dir = str(Path(output_dir))
        if output_type == "text" and isinstance(content, str):  # noqa duplicate content
            output_file_name = f"{file_name}.txt"  # Use .txt extension
            processed_content = content
        elif output_type == "text" and not isinstance(content, str):
            # Convert structured content to text
            output_file_name = f"{file_name}.txt"  # Use .txt extension
            if isinstance(content, list):
                # Handle list of pages/sections
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and "content" in item:
                        text_parts.append(str(item.get("content", "")))
                    else:
                        text_parts.append(str(item))
                processed_content = "\n".join(text_parts)
            else:
                processed_content = str(content)
        elif output_type == "markdown":
            output_file_name = f"{file_name}.md"
            if isinstance(content, list):
                # Handle list of pages/sections
                md_parts = []
                for item in content:
                    if isinstance(item, dict):
                        # Add page headers
                        page_num = item.get("page", "")
                        item_type = item.get("type", "")

                        if page_num:
                            if item_type == "Text":
                                md_parts.append(
                                    f"## Page {page_num}\n\n{item.get('content', '')}"
                                )
                            elif item_type == "Image":
                                md_parts.append(
                                    f"### Image on Page {page_num}\n\n{item.get('content', '')}"
                                )
                            else:
                                md_parts.append(
                                    f"### {item_type} on Page {page_num}\n\n{item.get('content', '')}"
                                )
                        else:
                            md_parts.append(str(item.get("content", "")))
                    else:
                        md_parts.append(str(item))
                processed_content = "\n\n".join(md_parts)
            elif isinstance(content, str):
                processed_content = content
            else:
                processed_content = str(content)
        else:  # json
            output_file_name = f"{file_name}.json"
            if isinstance(content, str):
                content = [
                    {
                        "page": 1,
                        "type": "Text",
                        "content": content,
                    }
                ]
            processed_content = json.dumps(
                {"content": content}, ensure_ascii=False, indent=2
            )
        output_path = Path(output_dir) / output_file_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(processed_content, encoding="utf-8")
        return output_path.as_posix()

    async def aread_document(
        self,
        file_path: str,
        output_type: Literal["text", "json", "markdown"],
        output_dir: str | None = None,
    ) -> str:
        """Async: Main method to read a document and extract its content.

        Args:
            file_path: Path to the file
            output_type: Output format ("text", "json", or "markdown")
            output_dir: Optional custom output directory. If not provided,
                       creates 'processed/' subdirectory next to the source file.

        Returns:
            Path to the processed output file
        """
        import asyncio

        try:
            # Get file extension to determine which reader to use
            file_extension = Path(file_path).suffix.lower()

            # For PDF/PPTX/DOCX with LLM and JSON output, use batch processing
            if file_extension in (".pdf", ".pptx", ".docx") and output_type == "json":
                # Check if we have LLM reader for this file type
                has_llm_reader = (
                    file_extension in (".pdf", ".pptx") and self._pdf_reader
                ) or (file_extension == ".docx" and self._document_reader)

                if has_llm_reader:
                    # Prepare output path
                    path = Path(file_path)
                    file_name = path.stem
                    if output_dir is None:
                        output_dir_path = path.parent / Path("processed")
                    else:
                        output_dir_path = Path(output_dir)
                    output_dir_path.mkdir(parents=True, exist_ok=True)
                    output_file_path = output_dir_path / f"{file_name}.json"

                    # Process with batching directly to file
                    if file_extension == ".pdf":
                        result = await self._aread_pdf(
                            file_path, output_path=str(output_file_path)
                        )
                    elif file_extension == ".pptx":
                        # PPTX uses sync handler for now - run in thread
                        result = await asyncio.to_thread(
                            presentation_read_handler,
                            file_path,
                            pdf_handler=self._read_pdf,
                            output_path=str(output_file_path),
                        )
                    else:  # .docx
                        # DOCX uses sync handler for now - run in thread
                        result = await asyncio.to_thread(
                            self._read_docx,
                            file_path,
                            output_path=str(output_file_path),
                        )
                    return result if isinstance(result, str) else str(output_file_path)
            else:
                # Standard processing for other files (run in thread)
                content = await asyncio.to_thread(
                    self.__extract_content_sync, file_path, file_extension
                )
                # Process output based on requested format
                output_file_path = await asyncio.to_thread(
                    self._process_output, content, file_path, output_type, output_dir
                )
                return output_file_path
        except Exception as e:
            raise RuntimeError(f"Failed to process document: {e!s}") from e


def main() -> None:
    """CLI entry point for Donkit read engine.

    Usage:
        donkit-read-engine <file_path> [--output-type text|json|markdown]
    """
    parser = argparse.ArgumentParser(
        prog="donkit-read-engine",
        description="Read a document and export extracted content to text/json/markdown",
    )
    parser.add_argument(
        "file_path",
        nargs="?",
        default="/Users/romanlosev/donkit/platform/ragops-agent/shared/read-engine/src/files",
        help="Path to a local file or directory to read (directory will be processed recursively)",
    )
    parser.add_argument(
        "--output-type",
        choices=["text", "json", "markdown"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--pdf-strategy",
        choices=["fast", "hi_res", "ocr_only", "auto"],
        default=None,
        help="unstructured parsing strategy (overrides UNSTRUCTURED_STRATEGY)",
    )
    parser.add_argument(
        "--ocr-lang",
        default=None,
        help="OCR languages for unstructured (e.g., 'rus+eng') (overrides UNSTRUCTURED_OCR_LANG)",
    )

    args = parser.parse_args()

    # Apply optional strategy settings for unstructured before constructing reader
    if args.pdf_strategy:
        os.environ["UNSTRUCTURED_STRATEGY"] = args.pdf_strategy
    if args.ocr_lang:
        os.environ["UNSTRUCTURED_OCR_LANG"] = args.ocr_lang

    reader = DonkitReader()
    input_path = Path(args.file_path)
    if input_path.is_dir():
        exts = set(reader.readers.keys())
        files: list[Path] = [
            f for f in input_path.rglob("*") if f.is_file() and f.suffix.lower() in exts
        ]
        for f in sorted(files):
            try:
                output_path = reader.read_document(f.as_posix(), args.output_type)  # type: ignore[arg-type]
                print(output_path)
            except Exception as e:
                print(f"ERROR processing {f}: {e}")
    else:
        output_path = reader.read_document(input_path.as_posix(), args.output_type)  # type: ignore[arg-type]
        print(output_path)


if __name__ == "__main__":
    main()
