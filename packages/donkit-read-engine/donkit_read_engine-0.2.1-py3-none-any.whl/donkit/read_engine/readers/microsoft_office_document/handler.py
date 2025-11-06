import base64
import json
from collections import defaultdict

from docx import Document as DocxDocument
from loguru import logger

from ..microsoft_office_document.parser import DocumentParser
from ..static_visual_format.models import ImageAnalysisService


def document_read_handler(path: str) -> list[dict[str, str | int]]:
    """Simple DOCX reader without LLM - extracts only text and tables.

    Args:
        path: Path to the document file

    Returns:
        List of dictionaries containing extracted content with page numbers
    """
    try:
        document = DocxDocument(path)
        parser = DocumentParser(document)
        parsed_document = parser.parse()

        page_text: dict[int, list[str]] = defaultdict(list)

        for item in parsed_document:
            page_num = item.get("page", 1)
            item_type = item.get("type", "")
            if item_type == "Text":
                page_text[page_num].append(item.get("content", ""))
            elif item_type == "Table":
                table_content = []
                rows = item.get("content", [])

                for row in rows:
                    formatted_row = " | ".join(cell for cell in row if cell)
                    if formatted_row.strip():
                        table_content.append(formatted_row)

                if table_content:
                    table_text = "Table:\n" + "\n".join(table_content)
                    page_text[page_num].append(table_text)
        result = []
        for page_num, texts in sorted(page_text.items()):
            result.append(
                {"page": page_num, "type": "Text", "content": "\n\n".join(texts)}
            )

        return result
    except Exception as e:
        logger.exception(f"Error processing DOCX: {e}")
        return [
            {"page": 1, "type": "Error", "content": "Error processing DOCX document"}
        ]


class LlmDocumentReader:
    """DOCX reader with LLM-based image analysis."""

    def __init__(self, image_service: ImageAnalysisService):
        """Initialize document reader.

        Args:
            image_service: Image analysis service instance for LLM-based processing
        """
        self.image_service = image_service

    def read(
        self, path: str, output_path: str | None = None
    ) -> list[dict[str, str | int]] | str:
        """Process DOCX file with LLM image analysis.

        Args:
            path: Path to the document file
            output_path: Optional output path for batch processing (not used for DOCX)

        Returns:
            List of dictionaries containing extracted content with page numbers,
            or output_path string if provided
        """
        try:
            document = DocxDocument(path)
            parser = DocumentParser(document)
            parsed_document = parser.parse()

            page_text: dict[int, list[str]] = defaultdict(list)
            result = []

            for item in parsed_document:
                logger.debug(item)
                page_num = item.get("page", 1)
                item_type = item.get("type", "")

                if item_type == "Text":
                    page_text[page_num].append(item.get("content", ""))
                elif item_type == "Table":
                    table_content = []
                    rows = item.get("content", [])

                    for row in rows:
                        formatted_row = " | ".join(cell for cell in row if cell)
                        if formatted_row.strip():
                            table_content.append(formatted_row)

                    if table_content:
                        table_text = "Table:\n" + "\n".join(table_content)
                        page_text[page_num].append(table_text)
                elif item_type == "Image":
                    try:
                        image_bytes = item.get("content").getvalue()

                        # Skip blank/empty images
                        if not image_bytes or len(image_bytes) < 100:
                            logger.debug(
                                f"Skipping blank/empty image on page {page_num}"
                            )
                            continue

                        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
                        image_context = self.image_service.analyze_with_agent(
                            encoded_image
                        )

                        # Skip if analysis result is blank_image
                        if (
                            isinstance(image_context, dict)
                            and image_context.get("type") == "blank_image"
                        ):
                            logger.debug(
                                f"Skipping blank_image result on page {page_num}"
                            )
                            continue

                        if isinstance(image_context, str) and image_context.startswith(
                            "```json"
                        ):
                            image_context = json.loads(
                                image_context.replace("```json", "").replace("```", "")
                            )
                        result.append(
                            {
                                "page": page_num,
                                "type": "Image",
                                "content": image_context,
                                "image_index": len(
                                    [
                                        r
                                        for r in result
                                        if r.get("type") == "Image"
                                        and r.get("page") == page_num
                                    ]
                                ),
                            }
                        )
                    except Exception as e:
                        logger.error(f"Error analyzing image on page {page_num}: {e}")
                        # Don't add error entries for images, just skip them
                        continue
            for page_num, texts in sorted(page_text.items()):
                result.append(
                    {"page": page_num, "type": "Text", "content": "\n\n".join(texts)}
                )
            result.sort(
                key=lambda x: (
                    x.get("page", 0),
                    0 if x.get("type", "") == "Text" else 1,
                    x.get("image_index", 0),
                )
            )

            # Write to output_path if provided
            if output_path:
                import pathlib

                output_file = pathlib.Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump({"content": result}, f, ensure_ascii=False, indent=2)
                logger.debug(f"💾 DOCX results written to {output_path}")
                return output_path

            return result
        except Exception as e:
            logger.exception(f"Error processing DOCX: {e}")
            return [
                {
                    "page": 1,
                    "type": "Error",
                    "content": "Error processing DOCX document",
                }
            ]
