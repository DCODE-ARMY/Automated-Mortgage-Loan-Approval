import os
from typing import Type, List
from pydantic import BaseModel, Field
from urllib.parse import urlparse
from mistralai import Mistral
from crewai.tools import BaseTool
from dotenv import load_dotenv

load_dotenv()

class PDFQAToolInput(BaseModel):
    """Accepts 1–10 PDF or image paths/URLs plus a question."""
    paths: List[str] = Field(
        ..., 
        description="List of local filesystem paths or public URLs to up to 10 PDF or image files (PDF, JPG, JPEG, PNG)",
        max_items=10
    )
    question: str = Field(
        ..., 
        description="The crew agent’s question to answer using the provided files"
    )

class PDFQATool(BaseTool):
    name: str = "PDFQATool"
    description: str = (
        "Uploads scanned PDFs or images (JPG, JPEG, PNG) to Mistral, retrieves signed HTTPS URLs, "
        "and answers a question across all of them in one go."
    )
    args_schema: Type[PDFQAToolInput] = PDFQAToolInput

    def _run(self, paths, question) -> str:
        # 1. Initialize SDK client
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY must be set in the environment")
        client = Mistral(api_key=api_key)

        # 2. Validate file types
        supported_extensions = {'.pdf', '.jpg', '.jpeg', '.png'}
        
        content_chunks = [{"type": "text", "text": question}]
        for path in paths:
            parsed = urlparse(path)
            is_url = parsed.scheme in ("http", "https")
            if is_url:
                # Extract extension from URL
                ext = os.path.splitext(parsed.path)[1].lower()
            else:
                # Extract extension from local path
                ext = os.path.splitext(path)[1].lower()
            
            if ext not in supported_extensions:
                raise ValueError(f"Unsupported file type: {ext}. Supported types: {', '.join(supported_extensions)}")

            # 3. Handle local files (upload) or URLs
            if is_url:
                url_ref = path
            else:
                # Upload local file for OCR processing
                with open(path, "rb") as f:
                    file_content = f.read()
                upload_resp = client.files.upload(
                    file={
                        "file_name": os.path.basename(path),
                        "content": file_content
                    },
                    purpose="ocr"
                )
                # Get a signed HTTPS URL
                url_ref = client.files.get_signed_url(file_id=upload_resp.id).url

            # 4. Add to content chunks based on file type
            if ext == '.pdf':
                content_chunks.append({
                    "type": "document_url",
                    "document_url": url_ref
                })
            else:  # Image formats: .jpg, .jpeg, .png
                content_chunks.append({
                    "type": "image_url",
                    "image_url": url_ref
                })

        # 5. Ask the model, which OCRs & understands all files at once
        chat_resp = client.chat.complete(
            model="mistral-medium-latest",
            messages=[{"role": "user", "content": content_chunks}],
            temperature=0.0,
        )

        # 6. Return the aggregated answer
        return chat_resp.choices[0].message.content

