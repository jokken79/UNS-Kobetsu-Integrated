"""
PDF Converter Utility - DOCX to PDF conversion using LibreOffice

Uses LibreOffice headless mode for server-side DOCX to PDF conversion.
LibreOffice is already installed in the Docker container (see Dockerfile).
"""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


class PDFConversionError(Exception):
    """Raised when PDF conversion fails."""
    pass


def convert_docx_to_pdf(docx_bytes: bytes, timeout: int = 60) -> bytes:
    """
    Convert DOCX bytes to PDF bytes using LibreOffice headless.

    Args:
        docx_bytes: The DOCX document as bytes
        timeout: Maximum time in seconds to wait for conversion

    Returns:
        bytes: The converted PDF document

    Raises:
        PDFConversionError: If conversion fails
    """
    # Create temp directory for the conversion
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Write DOCX to temp file
        docx_path = temp_path / "document.docx"
        docx_path.write_bytes(docx_bytes)

        # Expected PDF output path
        pdf_path = temp_path / "document.pdf"

        # Create user profile directory in temp to avoid permission issues
        user_profile = temp_path / "libreoffice_profile"
        user_profile.mkdir(exist_ok=True)

        # Set environment to use temp directory for LibreOffice config
        env = os.environ.copy()
        env["HOME"] = str(temp_path)

        try:
            # Run LibreOffice headless conversion with custom user profile
            result = subprocess.run(
                [
                    "libreoffice",
                    "--headless",
                    "--nofirststartwizard",
                    f"-env:UserInstallation=file://{user_profile}",
                    "--convert-to", "pdf",
                    "--outdir", str(temp_path),
                    str(docx_path)
                ],
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )

            # Check if conversion succeeded
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                raise PDFConversionError(
                    f"LibreOffice conversion failed (code {result.returncode}): {error_msg}"
                )

            # Verify PDF was created
            if not pdf_path.exists():
                raise PDFConversionError(
                    f"PDF file was not created. LibreOffice output: {result.stdout}"
                )

            # Read and return PDF bytes
            return pdf_path.read_bytes()

        except subprocess.TimeoutExpired:
            raise PDFConversionError(
                f"PDF conversion timed out after {timeout} seconds"
            )
        except FileNotFoundError:
            raise PDFConversionError(
                "LibreOffice not found. Ensure libreoffice-writer is installed."
            )


def convert_docx_file_to_pdf(docx_path: str, output_dir: Optional[str] = None) -> str:
    """
    Convert a DOCX file to PDF.

    Args:
        docx_path: Path to the DOCX file
        output_dir: Directory for output PDF (defaults to same as input)

    Returns:
        str: Path to the generated PDF file

    Raises:
        PDFConversionError: If conversion fails
    """
    docx_path = Path(docx_path)

    if not docx_path.exists():
        raise PDFConversionError(f"DOCX file not found: {docx_path}")

    if output_dir is None:
        output_dir = str(docx_path.parent)
    else:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    try:
        result = subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--convert-to", "pdf",
                "--outdir", output_dir,
                str(docx_path)
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown error"
            raise PDFConversionError(
                f"LibreOffice conversion failed: {error_msg}"
            )

        # Return expected PDF path
        pdf_path = Path(output_dir) / f"{docx_path.stem}.pdf"
        if not pdf_path.exists():
            raise PDFConversionError(
                f"PDF file was not created at expected path: {pdf_path}"
            )

        return str(pdf_path)

    except subprocess.TimeoutExpired:
        raise PDFConversionError("PDF conversion timed out")
    except FileNotFoundError:
        raise PDFConversionError(
            "LibreOffice not found. Ensure libreoffice-writer is installed."
        )


def is_libreoffice_available() -> bool:
    """Check if LibreOffice is available on the system."""
    try:
        result = subprocess.run(
            ["libreoffice", "--version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
