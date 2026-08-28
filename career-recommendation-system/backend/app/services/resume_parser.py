import os
import fitz
from docx import Document
from fastapi import UploadFile, HTTPException


ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


async def parse_resume(file: UploadFile):
    filename = file.filename

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided"
        )

    extension = os.path.splitext(filename)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload PDF, DOCX, or TXT."
        )

    try:
        file_content = await file.read()

        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty."
            )

        if extension == ".pdf":
            extracted_text = extract_pdf_text(file_content)

        elif extension == ".docx":
            extracted_text = extract_docx_text(file_content)

        elif extension == ".txt":
            extracted_text = extract_txt_text(file_content)

        extracted_text = extracted_text.strip()

        if not extracted_text:
            raise HTTPException(
                status_code=400,
                detail="No readable text was found in the resume."
            )

        return {
            "filename": filename,
            "file_type": extension,
            "extracted_text": extracted_text,
            "character_count": len(extracted_text)
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Error while reading resume: {str(error)}"
        )


def extract_pdf_text(file_content: bytes):
    text = ""

    pdf_document = fitz.open(stream=file_content, filetype="pdf")

    for page in pdf_document:
        text += page.get_text()

    pdf_document.close()

    return text


def extract_docx_text(file_content: bytes):
    import io

    document = Document(io.BytesIO(file_content))

    text = ""

    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"

    return text


def extract_txt_text(file_content: bytes):
    return file_content.decode("utf-8", errors="ignore")