"""
Excel XML Document Service - Generates documents by modifying XML directly.

This service preserves column widths by NOT using openpyxl to save.
Instead, it modifies the Excel XML directly and repackages the xlsx file.
"""
import zipfile
import tempfile
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from io import BytesIO
from datetime import date, datetime
from decimal import Decimal

from app.core.config import settings

# XML namespaces used in Excel
NAMESPACES = {
    'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}

# Register namespaces to avoid ns0: prefix
for prefix, uri in NAMESPACES.items():
    ET.register_namespace('' if prefix == 'main' else prefix, uri)


class ExcelXMLService:
    """
    Generates Excel documents by modifying XML directly.

    This preserves column widths that openpyxl would otherwise corrupt.
    """

    # Path to the original Excel template (with correct formatting)
    ORIGINAL_TEMPLATE = "/app/ExcelKobetsukeiyakusho.xlsx"

    # Sheet indices in the original Excel
    SHEET_INDICES = {
        "kobetsu_keiyakusho": 0,  # 個別契約書X
        "tsuchisho": 1,           # 通知書
        "daicho": 2,              # DAICHO
        "hakenmoto_daicho": 3,    # 派遣元管理台帳
        "shugyo_joken": 4,        # 就業条件明示書
        "keiyakusho": 5,          # 契約書
    }

    # Cell mappings for kobetsu_keiyakusho
    # Maps cell reference to (data_key, type) where type is 'text', 'number', 'date'
    # The Excel uses control cells in column AD that drive formulas in the document
    KOBETSU_CELL_MAP = {
        # Control cells in column AD (these drive the formulas)
        'AD1': ('client_company_name', 'text'),    # 派遣先 (company name)
        'AD2': ('factory_name', 'text'),           # 工場名 (factory name)
        'AD3': ('organizational_unit', 'text'),    # 配属先 (department/unit)
        'AD4': ('line', 'text'),                   # ライン (line - optional)
        'AD5': ('hourly_rate', 'number'),          # 時給単価 (hourly rate)
        'AD7': ('dispatch_start_date', 'date'),    # 派遣開始日 (start date)
    }

    @classmethod
    def generate_kobetsu_keiyakusho(cls, data: Dict[str, Any]) -> bytes:
        """
        Generate 個別契約書 (Individual Contract) document.

        Args:
            data: Dictionary with contract data including:
                - company_name: 派遣先会社名
                - factory_name: 工場名
                - department: 配属先
                - line: ライン
                - hourly_rate: 時給
                - dispatch_start_date: 派遣開始日
                - dispatch_end_date: 派遣終了日
                - work_content: 業務内容
                - etc.

        Returns:
            bytes: The generated xlsx file content
        """
        return cls._generate_with_data(data, cls.KOBETSU_CELL_MAP)

    @classmethod
    def _generate_with_data(cls, data: Dict[str, Any], cell_map: Dict[str, Tuple[str, str]]) -> bytes:
        """
        Generate Excel with data filled in.

        Args:
            data: Dictionary with values to fill
            cell_map: Mapping of cell references to (data_key, value_type)

        Returns:
            bytes: The generated xlsx file content
        """
        template_path = Path(cls.ORIGINAL_TEMPLATE)
        if not template_path.exists():
            template_path = Path("/tmp/original.xlsx")
            if not template_path.exists():
                raise FileNotFoundError(
                    f"Template not found at {cls.ORIGINAL_TEMPLATE}"
                )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Extract the xlsx
            with zipfile.ZipFile(template_path, 'r') as z:
                z.extractall(temp_path)

            # Read and modify shared strings
            ss_path = temp_path / 'xl' / 'sharedStrings.xml'
            shared_strings = []
            string_to_index = {}

            if ss_path.exists():
                shared_strings, string_to_index = cls._read_shared_strings(ss_path)

            # Read sheet1.xml
            sheet_path = temp_path / 'xl' / 'worksheets' / 'sheet1.xml'
            sheet_content = sheet_path.read_text(encoding='utf-8')

            # Apply cell modifications
            for cell_ref, (data_key, value_type) in cell_map.items():
                value = data.get(data_key)
                if value is not None:
                    sheet_content = cls._modify_cell(
                        sheet_content, cell_ref, value, value_type,
                        shared_strings, string_to_index
                    )

            # Write modified sheet
            sheet_path.write_text(sheet_content, encoding='utf-8')

            # Write updated shared strings if modified
            if ss_path.exists():
                cls._write_shared_strings(ss_path, shared_strings)

            # Repackage xlsx
            output = BytesIO()
            with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zout:
                for item in temp_path.rglob('*'):
                    if item.is_file():
                        arcname = str(item.relative_to(temp_path)).replace('\\', '/')
                        zout.write(item, arcname)

            return output.getvalue()

    @classmethod
    def _read_shared_strings(cls, path: Path) -> Tuple[List[str], Dict[str, int]]:
        """Read shared strings from XML file."""
        content = path.read_text(encoding='utf-8')
        strings = []
        string_to_index = {}

        # Parse <si><t>value</t></si> entries
        pattern = r'<si[^>]*>(?:<t[^>]*>([^<]*)</t>|<t[^>]*/>'
        # More robust pattern to extract text
        si_pattern = r'<si[^>]*>(.*?)</si>'
        t_pattern = r'<t[^>]*>([^<]*)</t>'

        for si_match in re.finditer(si_pattern, content, re.DOTALL):
            si_content = si_match.group(1)
            t_match = re.search(t_pattern, si_content)
            if t_match:
                text = t_match.group(1)
                string_to_index[text] = len(strings)
                strings.append(text)
            else:
                strings.append('')

        return strings, string_to_index

    @classmethod
    def _write_shared_strings(cls, path: Path, strings: List[str]) -> None:
        """Write shared strings to XML file."""
        # Read original to preserve structure
        content = path.read_text(encoding='utf-8')

        # Update count
        content = re.sub(
            r'count="\d+"',
            f'count="{len(strings)}"',
            content
        )
        content = re.sub(
            r'uniqueCount="\d+"',
            f'uniqueCount="{len(strings)}"',
            content
        )

        path.write_text(content, encoding='utf-8')

    @classmethod
    def _modify_cell(
        cls,
        sheet_xml: str,
        cell_ref: str,
        value: Any,
        value_type: str,
        shared_strings: List[str],
        string_to_index: Dict[str, int]
    ) -> str:
        """
        Modify a cell value in the sheet XML.

        Handles three types:
        - 'text': String value (modifies shared strings or uses inline string)
        - 'number': Numeric value
        - 'date': Date value (converted to Excel serial number)
        """
        if value_type == 'date':
            # Convert date to Excel serial number
            if isinstance(value, (date, datetime)):
                excel_value = cls._date_to_excel_serial(value)
            else:
                # Try to parse string date
                try:
                    if isinstance(value, str):
                        d = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        excel_value = cls._date_to_excel_serial(d)
                    else:
                        excel_value = value
                except:
                    excel_value = value

            # Replace cell value, remove formula if present
            pattern = rf'(<c r="{cell_ref}"[^>]*>)(?:<f>[^<]*</f>)?<v>[^<]*</v>(</c>)'
            replacement = rf'\g<1><v>{excel_value}</v>\2'
            sheet_xml = re.sub(pattern, replacement, sheet_xml)

        elif value_type == 'number':
            # Numeric value - just replace <v> content
            numeric_value = float(value) if value else 0
            pattern = rf'(<c r="{cell_ref}"[^>]*>)<v>[^<]*</v>(</c>)'
            replacement = rf'\g<1><v>{numeric_value}</v>\2'
            sheet_xml = re.sub(pattern, replacement, sheet_xml)

        elif value_type == 'text':
            str_value = str(value) if value else ''

            # Use inline string (t="inlineStr") to avoid modifying shared strings
            # Escape XML special characters
            str_value = str_value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            # First, remove any existing t="..." attribute from the cell
            # Then add t="inlineStr" and replace content with inline string
            # Step 1: Find the cell and extract its structure
            pattern = rf'<c r="{cell_ref}"([^>]*)>(?:<f>[^<]*</f>)?<v>[^<]*</v></c>'

            def replace_with_inline(match):
                attrs = match.group(1)
                # Remove any existing t="..." attribute
                attrs = re.sub(r'\s*t="[^"]*"', '', attrs)
                return f'<c r="{cell_ref}"{attrs} t="inlineStr"><is><t>{str_value}</t></is></c>'

            sheet_xml = re.sub(pattern, replace_with_inline, sheet_xml)

        return sheet_xml

    @classmethod
    def _date_to_excel_serial(cls, d: date) -> int:
        """Convert Python date to Excel serial number."""
        # Excel epoch is 1900-01-01 = 1 (with bug for 1900-02-29)
        excel_epoch = date(1899, 12, 30)
        if isinstance(d, datetime):
            d = d.date()
        return (d - excel_epoch).days

    @classmethod
    def _copy_sheet_as_xlsx(cls, sheet_index: int) -> bytes:
        """
        Copy a sheet from the original Excel as a new xlsx file.
        (Legacy method - use _generate_with_data for data filling)

        Args:
            sheet_index: Index of the sheet to copy

        Returns:
            bytes: The xlsx file content
        """
        template_path = Path(cls.ORIGINAL_TEMPLATE)
        if not template_path.exists():
            template_path = Path("/tmp/original.xlsx")
            if not template_path.exists():
                raise FileNotFoundError(
                    f"Template not found at {cls.ORIGINAL_TEMPLATE}"
                )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            with zipfile.ZipFile(template_path, 'r') as z:
                z.extractall(temp_path)

            output = BytesIO()
            with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zout:
                for item in temp_path.rglob('*'):
                    if item.is_file():
                        arcname = str(item.relative_to(temp_path)).replace('\\', '/')
                        zout.write(item, arcname)

            return output.getvalue()

    @classmethod
    def _modify_cell_value(cls, sheet_xml: str, cell_ref: str, new_value: str) -> str:
        """
        Modify a cell value in the sheet XML.

        Args:
            sheet_xml: The sheet XML content
            cell_ref: Cell reference (e.g., "B5")
            new_value: New value to set

        Returns:
            Modified XML string
        """
        # Excel XML cell format:
        # <c r="B5" s="123"><v>old value</v></c>
        # or for strings:
        # <c r="B5" s="123" t="s"><v>string_index</v></c>

        # For simplicity, we'll replace inline strings
        # More complex implementation would handle shared strings

        pattern = rf'(<c r="{cell_ref}"[^>]*>)<v>[^<]*</v>(</c>)'
        replacement = rf'\1<v>{new_value}</v>\2'

        return re.sub(pattern, replacement, sheet_xml)

    @classmethod
    def _format_japanese_date(cls, d: Optional[date]) -> str:
        """Format date in Japanese era format (令和X年X月X日)."""
        if not d:
            return ""

        # Calculate Reiwa year (Reiwa started May 1, 2019)
        reiwa_start = date(2019, 5, 1)
        if d >= reiwa_start:
            year = d.year - 2018
            era = "令和"
        else:
            # Heisei
            year = d.year - 1988
            era = "平成"

        return f"{era}{year}年{d.month}月{d.day}日"

    @classmethod
    def _format_currency(cls, amount: Optional[Decimal]) -> str:
        """Format currency with yen symbol and commas."""
        if amount is None:
            return ""
        return f"¥{int(amount):,}"


# Convenience function
def generate_kobetsu_document(data: Dict[str, Any]) -> bytes:
    """Generate a kobetsu keiyakusho document."""
    return ExcelXMLService.generate_kobetsu_keiyakusho(data)
