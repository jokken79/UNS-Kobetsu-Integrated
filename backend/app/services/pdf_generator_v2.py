"""
PDF Generator V2 - Template-based generation using JSON data and Jinja2.

This is the NEW approach: JSON → Jinja2 HTML Template → WeasyPrint → PDF

Advantages:
- Flexible design using HTML/CSS
- Beautiful typography with Japanese fonts
- Precise control over layout
- Easy to maintain templates
"""
from datetime import date, time
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import Optional, Union

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML, CSS

from app.core.config import settings
from app.schemas.document_data import DocumentDataSchema


class PDFGeneratorV2:
    """
    PDF document generator using Jinja2 templates and WeasyPrint.

    This generator:
    1. Loads an HTML template (with Jinja2 syntax)
    2. Renders it with data from JSON (DocumentDataSchema)
    3. Converts HTML to PDF using WeasyPrint
    4. Returns the PDF as bytes

    Templates are stored in: backend/templates/pdf/
    """

    def __init__(self, data: DocumentDataSchema):
        """
        Initialize generator with document data.

        Args:
            data: DocumentDataSchema (JSON format)
        """
        self.data = data
        self.template_dir = Path(settings.PDF_TEMPLATE_DIR)

        # Setup Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

        # Register custom filters
        self.jinja_env.filters['format_date_japanese'] = self._format_date_japanese
        self.jinja_env.filters['format_time'] = self._format_time
        self.jinja_env.filters['format_currency'] = self._format_currency
        self.jinja_env.filters['format_work_days'] = self._format_work_days

    # ========================================
    # FORMATTING HELPERS
    # ========================================

    def _format_date_japanese(self, d: Optional[date]) -> str:
        """Format date as Japanese era (令和X年X月X日)."""
        if d is None:
            return ""

        if d.year >= 2019 and (d.month > 4 or (d.month == 4 and d.year > 2019)):
            reiwa_year = d.year - 2018
            return f"令和{reiwa_year}年{d.month}月{d.day}日"

        if d.year >= 1989:
            heisei_year = d.year - 1988
            return f"平成{heisei_year}年{d.month}月{d.day}日"

        return f"{d.year}年{d.month}月{d.day}日"

    def _format_time(self, t: Optional[time]) -> str:
        """Format time as HH:MM."""
        if t is None:
            return ""
        return t.strftime("%H:%M")

    def _format_currency(self, value: Optional[Union[Decimal, int, float]]) -> str:
        """Format as Japanese yen (¥X,XXX)."""
        if value is None:
            return ""
        return f"¥{int(value):,}"

    def _format_work_days(self, days: list) -> str:
        """Format work days list."""
        if not days:
            return "月・火・水・木・金"
        return "・".join(days)

    # ========================================
    # PDF GENERATION
    # ========================================

    def _render_html(self, template_name: str) -> str:
        """
        Render Jinja2 template with data.

        Args:
            template_name: Name of template file (e.g., 'kobetsu_keiyakusho.html')

        Returns:
            Rendered HTML string
        """
        template = self.jinja_env.get_template(template_name)
        return template.render(data=self.data)

    def _html_to_pdf(self, html_string: str) -> bytes:
        """
        Convert HTML string to PDF bytes using WeasyPrint.

        Args:
            html_string: Rendered HTML

        Returns:
            PDF file as bytes
        """
        # Load base CSS for Japanese documents
        css_path = self.template_dir / "base.css"
        css = None
        if css_path.exists():
            css = CSS(filename=str(css_path))

        # Convert HTML to PDF
        html = HTML(string=html_string, base_url=str(self.template_dir))
        pdf_bytes = html.write_pdf(stylesheets=[css] if css else None)

        return pdf_bytes

    # ========================================
    # DOCUMENT GENERATORS
    # ========================================

    def generate_kobetsu_keiyakusho(self) -> bytes:
        """
        Generate 個別契約書 (Individual Dispatch Contract) as PDF.

        Returns:
            PDF file as bytes
        """
        html = self._render_html("kobetsu_keiyakusho.html")
        return self._html_to_pdf(html)

    def generate_tsuchisho(self) -> bytes:
        """
        Generate 通知書 (Notification) as PDF.

        Returns:
            PDF file as bytes
        """
        html = self._render_html("tsuchisho.html")
        return self._html_to_pdf(html)

    def generate_daicho(self) -> bytes:
        """
        Generate DAICHO (Registry) as PDF.

        Returns:
            PDF file as bytes
        """
        html = self._render_html("daicho.html")
        return self._html_to_pdf(html)

    def generate_all(self) -> dict:
        """
        Generate all available documents as PDFs.

        Returns:
            Dict mapping document name to bytes
        """
        results = {}

        try:
            results["kobetsu_keiyakusho"] = self.generate_kobetsu_keiyakusho()
        except Exception as e:
            results["kobetsu_keiyakusho_error"] = str(e)

        try:
            results["tsuchisho"] = self.generate_tsuchisho()
        except Exception as e:
            results["tsuchisho_error"] = str(e)

        try:
            results["daicho"] = self.generate_daicho()
        except Exception as e:
            results["daicho_error"] = str(e)

        return results


# ========================================
# CONVENIENCE FUNCTIONS
# ========================================

def generate_pdf_from_json(json_data: dict, document_type: str) -> bytes:
    """
    Generate PDF from JSON data.

    Args:
        json_data: Document data as dict
        document_type: Type of document ('kobetsu_keiyakusho', 'tsuchisho', etc.)

    Returns:
        PDF bytes

    Example:
        >>> json_data = {"contract_number": "KOB-001", ...}
        >>> pdf_bytes = generate_pdf_from_json(json_data, 'kobetsu_keiyakusho')
    """
    schema = DocumentDataSchema(**json_data)
    generator = PDFGeneratorV2(schema)

    if document_type == "kobetsu_keiyakusho":
        return generator.generate_kobetsu_keiyakusho()
    elif document_type == "tsuchisho":
        return generator.generate_tsuchisho()
    elif document_type == "daicho":
        return generator.generate_daicho()
    else:
        raise ValueError(f"Unknown document type: {document_type}")
