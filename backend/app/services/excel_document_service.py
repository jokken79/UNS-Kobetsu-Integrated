"""
Excel Document Service - Template-based document generation.

Generates legally compliant dispatch documents using Excel templates
that preserve exact formatting from the original Excel system.

This service:
1. Loads pre-formatted Excel templates
2. Fills them with contract/employee data
3. Returns the completed document as bytes

Supported documents:
- 個別契約書 (kobetsu_keiyakusho) - Individual Dispatch Contract
- 通知書 (tsuchisho) - Dispatch Notification
- DAICHO (daicho) - Individual Registry
- 派遣元管理台帳 (hakenmoto_daicho) - Dispatch Origin Ledger
- 就業条件明示書 (shugyo_joken) - Employment Conditions Document
- 契約書 (keiyakusho) - Labor Contract
"""
from datetime import date, time, datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.cell.cell import Cell

from app.core.config import settings
from app.services.template_manager import TemplateManager


class ExcelDocumentService:
    """
    Service for generating documents from Excel templates.

    This service replaces the DOCX-based document generation with
    Excel-based generation that preserves the original formatting
    from the legacy Excel system.
    """

    def __init__(self):
        """Initialize the service."""
        self.output_dir = Path(settings.PDF_OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ========================================
    # DATE/TIME FORMATTING
    # ========================================

    def _format_date_japanese(self, d: Optional[date]) -> str:
        """
        Format date as Japanese era (令和X年X月X日).

        Args:
            d: Date to format

        Returns:
            Formatted date string or empty if None
        """
        if d is None:
            return ""

        # Convert to date if datetime
        if isinstance(d, datetime):
            d = d.date()

        # Reiwa era started May 1, 2019
        if d.year >= 2019 and (d.month > 4 or (d.month == 4 and d.year > 2019)):
            reiwa_year = d.year - 2018
            return f"令和{reiwa_year}年{d.month}月{d.day}日"

        # Heisei era for dates before Reiwa
        if d.year >= 1989:
            heisei_year = d.year - 1988
            return f"平成{heisei_year}年{d.month}月{d.day}日"

        # Western format fallback
        return f"{d.year}年{d.month}月{d.day}日"

    def _format_date_short(self, d: Optional[date]) -> str:
        """Format date as YYYY.M.D."""
        if d is None:
            return ""
        if isinstance(d, datetime):
            d = d.date()
        return f"{d.year}.{d.month}.{d.day}"

    def _format_date_western(self, d: Optional[date]) -> str:
        """Format date as YYYY年MM月DD日."""
        if d is None:
            return ""
        if isinstance(d, datetime):
            d = d.date()
        return f"{d.year}年{d.month:02d}月{d.day:02d}日"

    def _format_time(self, t: Optional[time]) -> str:
        """Format time as HH:MM."""
        if t is None:
            return ""
        if isinstance(t, str):
            return t
        return t.strftime("%H:%M")

    def _format_time_range(
        self, start: Optional[time], end: Optional[time]
    ) -> str:
        """Format time range as HH:MM～HH:MM."""
        start_str = self._format_time(start)
        end_str = self._format_time(end)
        if start_str and end_str:
            return f"{start_str}～{end_str}"
        return ""

    # ========================================
    # CURRENCY FORMATTING
    # ========================================

    def _format_currency(self, value: Optional[Union[Decimal, int, float]]) -> str:
        """Format as Japanese yen (¥X,XXX)."""
        if value is None:
            return ""
        return f"¥{int(value):,}"

    def _format_currency_plain(
        self, value: Optional[Union[Decimal, int, float]]
    ) -> str:
        """Format as plain number with commas."""
        if value is None:
            return ""
        return f"{int(value):,}"

    # ========================================
    # CELL OPERATIONS
    # ========================================

    def _set_cell(
        self, ws: Worksheet, cell_ref: str, value: Any
    ) -> None:
        """
        Set a specific cell's value, preserving formatting.

        Args:
            ws: Worksheet to modify
            cell_ref: Cell reference (e.g., 'A1', 'B15')
            value: Value to set
        """
        cell = ws[cell_ref]
        cell.value = value

    def _find_and_replace(
        self, ws: Worksheet, placeholder: str, value: Any
    ) -> int:
        """
        Find placeholder text and replace with value.

        Args:
            ws: Worksheet to modify
            placeholder: Text to find (e.g., '{{contract_number}}')
            value: Replacement value

        Returns:
            Number of replacements made
        """
        count = 0
        str_value = str(value) if value is not None else ""

        for row in ws.iter_rows():
            for cell in row:
                if cell.value and isinstance(cell.value, str):
                    if placeholder in cell.value:
                        cell.value = cell.value.replace(placeholder, str_value)
                        count += 1

        return count

    def _find_and_replace_all(
        self, ws: Worksheet, replacements: Dict[str, Any]
    ) -> Dict[str, int]:
        """
        Replace multiple placeholders at once.

        Args:
            ws: Worksheet to modify
            replacements: Dict mapping placeholder to value

        Returns:
            Dict mapping placeholder to replacement count
        """
        results = {}
        for placeholder, value in replacements.items():
            results[placeholder] = self._find_and_replace(ws, placeholder, value)
        return results

    # ========================================
    # WORKBOOK OPERATIONS
    # ========================================

    def _workbook_to_bytes(self, wb: Workbook) -> bytes:
        """Convert workbook to bytes."""
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    def _save_workbook(
        self, wb: Workbook, filename: str, subfolder: str = "contracts"
    ) -> Path:
        """
        Save workbook to output directory.

        Args:
            wb: Workbook to save
            filename: Output filename
            subfolder: Subdirectory within output_dir

        Returns:
            Path to saved file
        """
        output_path = self.output_dir / subfolder
        output_path.mkdir(parents=True, exist_ok=True)

        file_path = output_path / filename
        wb.save(file_path)
        return file_path

    # ========================================
    # COMPANY INFO HELPERS
    # ========================================

    def _get_dispatch_company_info(self) -> Dict[str, str]:
        """Get dispatch company (派遣元) info from settings."""
        return {
            "name": settings.COMPANY_NAME,
            "name_legal": settings.COMPANY_NAME_LEGAL,
            "postal_code": settings.COMPANY_POSTAL_CODE,
            "address": settings.COMPANY_ADDRESS,
            "tel": settings.COMPANY_TEL,
            "mobile": settings.COMPANY_MOBILE,
            "fax": settings.COMPANY_FAX,
            "email": settings.COMPANY_EMAIL,
            "license_number": settings.COMPANY_LICENSE_NUMBER,
            "manager_name": settings.DISPATCH_MANAGER_NAME,
            "manager_position": settings.DISPATCH_MANAGER_POSITION,
            "responsible_department": settings.DISPATCH_RESPONSIBLE_DEPARTMENT,
            "responsible_position": settings.DISPATCH_RESPONSIBLE_POSITION,
            "responsible_name": settings.DISPATCH_RESPONSIBLE_NAME,
            "responsible_phone": settings.DISPATCH_RESPONSIBLE_PHONE,
            "complaint_department": settings.DISPATCH_COMPLAINT_DEPARTMENT,
            "complaint_position": settings.DISPATCH_COMPLAINT_POSITION,
            "complaint_name": settings.DISPATCH_COMPLAINT_NAME,
            "complaint_phone": settings.DISPATCH_COMPLAINT_PHONE,
        }

    # ========================================
    # 1. 個別契約書 (KOBETSU KEIYAKUSHO)
    # ========================================

    def generate_kobetsu_keiyakusho(self, data: Dict[str, Any]) -> bytes:
        """
        Generate 個別契約書 (Individual Dispatch Contract).

        This is the primary document required by 労働者派遣法第26条.
        It contains all 16 legally required items for dispatch contracts.

        Args:
            data: Contract data dictionary containing:
                - contract_number: Contract ID
                - contract_date: Date of contract
                - dispatch_start_date, dispatch_end_date: Period
                - factory.*: Client company info
                - worksite_*: Work location info
                - supervisor_*: Supervisor info
                - work_*: Work schedule and content
                - hourly_rate, overtime_rate: Compensation
                - employees: List of employee data
                - etc.

        Returns:
            Excel file as bytes
        """
        # Load template
        wb = TemplateManager.get_template("kobetsu_keiyakusho")
        ws = wb.active

        # Get company info
        dispatch_co = self._get_dispatch_company_info()

        # Build replacement dict
        replacements = {
            # Contract info
            "{{contract_number}}": data.get("contract_number", ""),
            "{{contract_date}}": self._format_date_japanese(
                data.get("contract_date")
            ),

            # Dispatch period
            "{{dispatch_start}}": self._format_date_japanese(
                data.get("dispatch_start_date")
            ),
            "{{dispatch_end}}": self._format_date_japanese(
                data.get("dispatch_end_date")
            ),

            # Client company (派遣先)
            "{{client_name}}": data.get("client_company_name", ""),
            "{{client_address}}": data.get("client_address", ""),
            "{{client_tel}}": data.get("client_tel", ""),

            # Worksite (就業場所)
            "{{worksite_name}}": data.get("worksite_name", ""),
            "{{worksite_address}}": data.get("worksite_address", ""),
            "{{org_unit}}": data.get("organizational_unit", ""),

            # Work content (業務内容)
            "{{work_content}}": data.get("work_content", ""),
            "{{responsibility}}": data.get("responsibility_level", "通常業務"),

            # Supervisor (指揮命令者)
            "{{supervisor_dept}}": data.get("supervisor_department", ""),
            "{{supervisor_position}}": data.get("supervisor_position", ""),
            "{{supervisor_name}}": data.get("supervisor_name", ""),
            "{{supervisor}}": self._format_supervisor(data),

            # Work schedule (就業時間)
            "{{work_days}}": self._format_work_days(data.get("work_days", [])),
            "{{work_time}}": self._format_time_range(
                data.get("work_start_time"),
                data.get("work_end_time")
            ),
            "{{work_start}}": self._format_time(data.get("work_start_time")),
            "{{work_end}}": self._format_time(data.get("work_end_time")),
            "{{break_minutes}}": f"{data.get('break_time_minutes', 60)}分",

            # Overtime (時間外労働)
            "{{overtime_day}}": f"{data.get('overtime_max_hours_day', 4)}時間/日",
            "{{overtime_month}}": f"{data.get('overtime_max_hours_month', 45)}時間/月",

            # Rates (派遣料金)
            "{{hourly_rate}}": self._format_currency(data.get("hourly_rate")),
            "{{overtime_rate}}": self._format_currency(data.get("overtime_rate")),
            "{{holiday_rate}}": self._format_currency(data.get("holiday_rate")),
            "{{night_rate}}": self._format_currency(data.get("night_shift_rate")),

            # Number of workers
            "{{num_workers}}": f"{data.get('number_of_workers', 1)}名",

            # Dispatch company (派遣元)
            "{{dispatch_company}}": dispatch_co["name"],
            "{{dispatch_address}}": dispatch_co["address"],
            "{{dispatch_tel}}": dispatch_co["tel"],
            "{{license_number}}": dispatch_co["license_number"],

            # Managers (責任者)
            "{{moto_manager}}": self._format_manager(
                data.get("haken_moto_manager", {})
            ),
            "{{saki_manager}}": self._format_manager(
                data.get("haken_saki_manager", {})
            ),
            "{{moto_manager_name}}": self._get_nested(
                data, "haken_moto_manager", "name", dispatch_co["responsible_name"]
            ),
            "{{saki_manager_name}}": self._get_nested(
                data, "haken_saki_manager", "name", ""
            ),

            # Complaint handlers (苦情処理担当者)
            "{{moto_complaint}}": self._format_complaint_handler(
                data.get("haken_moto_complaint_contact", {})
            ),
            "{{saki_complaint}}": self._format_complaint_handler(
                data.get("haken_saki_complaint_contact", {})
            ),

            # Legal checkboxes
            "{{kyotei_check}}": "☑" if data.get("is_kyotei_taisho") else "☐",
            "{{mukeiko_check}}": "☑" if data.get("is_mukeiko_60over_only") else "☐",
            "{{direct_hire_check}}": "☑" if data.get("is_direct_hire_prevention") else "☐",

            # Safety measures
            "{{safety_measures}}": data.get("safety_measures", "特になし"),

            # Welfare facilities
            "{{welfare}}": self._format_welfare(data.get("welfare_facilities", [])),
        }

        # Apply all replacements
        self._find_and_replace_all(ws, replacements)

        # Handle employee list if present
        employees = data.get("employees", [])
        if employees:
            self._fill_employee_table(ws, employees)

        return self._workbook_to_bytes(wb)

    def _format_supervisor(self, data: Dict) -> str:
        """Format supervisor info as single string."""
        parts = []
        if data.get("supervisor_department"):
            parts.append(data["supervisor_department"])
        if data.get("supervisor_position"):
            parts.append(data["supervisor_position"])
        if data.get("supervisor_name"):
            parts.append(data["supervisor_name"])
        return " ".join(parts)

    def _format_work_days(self, days: Union[List[str], str]) -> str:
        """Format work days list."""
        if isinstance(days, str):
            return days
        if not days:
            return "月・火・水・木・金"
        return "・".join(days)

    def _format_manager(self, manager: Dict) -> str:
        """Format manager info."""
        if not manager:
            return ""
        name = manager.get("name", "")
        phone = manager.get("phone", "")
        if name and phone:
            return f"{name} TEL:{phone}"
        return name

    def _format_complaint_handler(self, handler: Dict) -> str:
        """Format complaint handler info."""
        if not handler:
            return ""
        parts = []
        if handler.get("department"):
            parts.append(handler["department"])
        if handler.get("name"):
            parts.append(handler["name"])
        if handler.get("phone"):
            parts.append(f"TEL:{handler['phone']}")
        return " ".join(parts)

    def _format_welfare(self, facilities: Union[List[str], str]) -> str:
        """Format welfare facilities list."""
        if isinstance(facilities, str):
            return facilities
        if not facilities:
            return "食堂・更衣室・休憩室"
        return "・".join(facilities)

    def _get_nested(
        self, data: Dict, key1: str, key2: str, default: str = ""
    ) -> str:
        """Get nested dictionary value safely."""
        nested = data.get(key1, {})
        if isinstance(nested, dict):
            return nested.get(key2, default)
        return default

    def _fill_employee_table(
        self, ws: Worksheet, employees: List[Dict]
    ) -> None:
        """
        Fill employee table in worksheet.

        Looks for {{employee_N_name}}, {{employee_N_rate}} placeholders.
        """
        for i, emp in enumerate(employees, start=1):
            name_placeholder = f"{{{{employee_{i}_name}}}}"
            rate_placeholder = f"{{{{employee_{i}_rate}}}}"

            name = emp.get("name", emp.get("full_name_kanji", ""))
            rate = emp.get("hourly_rate", "")

            self._find_and_replace(ws, name_placeholder, name)
            self._find_and_replace(
                ws, rate_placeholder, self._format_currency(rate) if rate else ""
            )

    # ========================================
    # 2. 通知書 (TSUCHISHO)
    # ========================================

    def generate_tsuchisho(self, data: Dict[str, Any]) -> bytes:
        """
        Generate 通知書 (Dispatch Notification).

        Notification document sent to the client company.

        Args:
            data: Contract and employee data

        Returns:
            Excel file as bytes
        """
        wb = TemplateManager.get_template("tsuchisho")
        ws = wb.active

        dispatch_co = self._get_dispatch_company_info()

        replacements = {
            "{{notification_date}}": self._format_date_japanese(
                data.get("notification_date", date.today())
            ),
            "{{client_name}}": data.get("client_company_name", ""),
            "{{dispatch_company}}": dispatch_co["name"],
            "{{dispatch_address}}": dispatch_co["address"],
            "{{license_number}}": dispatch_co["license_number"],
            "{{dispatch_start}}": self._format_date_japanese(
                data.get("dispatch_start_date")
            ),
            "{{dispatch_end}}": self._format_date_japanese(
                data.get("dispatch_end_date")
            ),
            "{{worksite_name}}": data.get("worksite_name", ""),
            "{{work_content}}": data.get("work_content", ""),
            "{{work_time}}": self._format_time_range(
                data.get("work_start_time"),
                data.get("work_end_time")
            ),
            "{{break_minutes}}": f"{data.get('break_time_minutes', 60)}分",
        }

        self._find_and_replace_all(ws, replacements)

        # Fill employee list if present
        employees = data.get("employees", [])
        for i, emp in enumerate(employees, start=1):
            self._find_and_replace(
                ws, f"{{{{emp_{i}_name}}}}", emp.get("name", "")
            )
            self._find_and_replace(
                ws, f"{{{{emp_{i}_kana}}}}", emp.get("kana", "")
            )

        return self._workbook_to_bytes(wb)

    # ========================================
    # 3. DAICHO (台帳)
    # ========================================

    def generate_daicho(self, data: Dict[str, Any]) -> bytes:
        """
        Generate DAICHO (Individual Registry).

        Master registry document for individual employees.

        Args:
            data: Employee and assignment data

        Returns:
            Excel file as bytes
        """
        wb = TemplateManager.get_template("daicho")
        ws = wb.active

        replacements = {
            "{{registry_date}}": self._format_date_japanese(date.today()),
            "{{employee_name}}": data.get("employee_name", ""),
            "{{employee_kana}}": data.get("employee_kana", ""),
            "{{employee_number}}": data.get("employee_number", ""),
            "{{client_name}}": data.get("client_company_name", ""),
            "{{worksite_name}}": data.get("worksite_name", ""),
            "{{dispatch_start}}": self._format_date_japanese(
                data.get("dispatch_start_date")
            ),
            "{{dispatch_end}}": self._format_date_japanese(
                data.get("dispatch_end_date")
            ),
        }

        self._find_and_replace_all(ws, replacements)
        return self._workbook_to_bytes(wb)

    # ========================================
    # 4. 派遣元管理台帳 (HAKENMOTO DAICHO)
    # ========================================

    def generate_hakenmoto_daicho(self, data: Dict[str, Any]) -> bytes:
        """
        Generate 派遣元管理台帳 (Dispatch Origin Ledger).

        Management ledger kept by the dispatch company.

        Args:
            data: Contract and management data

        Returns:
            Excel file as bytes
        """
        wb = TemplateManager.get_template("hakenmoto_daicho")
        ws = wb.active

        dispatch_co = self._get_dispatch_company_info()

        replacements = {
            "{{ledger_date}}": self._format_date_japanese(date.today()),
            "{{dispatch_company}}": dispatch_co["name"],
            "{{dispatch_address}}": dispatch_co["address"],
            "{{license_number}}": dispatch_co["license_number"],
            "{{responsible_name}}": dispatch_co["responsible_name"],
            "{{responsible_phone}}": dispatch_co["responsible_phone"],
            "{{client_name}}": data.get("client_company_name", ""),
            "{{worksite_name}}": data.get("worksite_name", ""),
            "{{contract_number}}": data.get("contract_number", ""),
            "{{dispatch_start}}": self._format_date_japanese(
                data.get("dispatch_start_date")
            ),
            "{{dispatch_end}}": self._format_date_japanese(
                data.get("dispatch_end_date")
            ),
        }

        self._find_and_replace_all(ws, replacements)
        return self._workbook_to_bytes(wb)

    # ========================================
    # 5. 就業条件明示書 (SHUGYO JOKEN)
    # ========================================

    def generate_shugyo_joken(self, data: Dict[str, Any]) -> bytes:
        """
        Generate 就業条件明示書 (Employment Conditions Document).

        Document specifying working conditions for the dispatch worker.

        Args:
            data: Employment conditions data

        Returns:
            Excel file as bytes
        """
        wb = TemplateManager.get_template("shugyo_joken")
        ws = wb.active

        dispatch_co = self._get_dispatch_company_info()

        replacements = {
            "{{document_date}}": self._format_date_japanese(date.today()),
            "{{employee_name}}": data.get("employee_name", ""),
            "{{dispatch_company}}": dispatch_co["name"],
            "{{client_name}}": data.get("client_company_name", ""),
            "{{worksite_name}}": data.get("worksite_name", ""),
            "{{worksite_address}}": data.get("worksite_address", ""),
            "{{work_content}}": data.get("work_content", ""),
            "{{dispatch_start}}": self._format_date_japanese(
                data.get("dispatch_start_date")
            ),
            "{{dispatch_end}}": self._format_date_japanese(
                data.get("dispatch_end_date")
            ),
            "{{work_days}}": self._format_work_days(data.get("work_days", [])),
            "{{work_time}}": self._format_time_range(
                data.get("work_start_time"),
                data.get("work_end_time")
            ),
            "{{break_minutes}}": f"{data.get('break_time_minutes', 60)}分",
            "{{hourly_rate}}": self._format_currency(data.get("hourly_rate")),
            "{{overtime_rate}}": self._format_currency(data.get("overtime_rate")),
        }

        self._find_and_replace_all(ws, replacements)
        return self._workbook_to_bytes(wb)

    # ========================================
    # 6. 契約書 (KEIYAKUSHO)
    # ========================================

    def generate_keiyakusho(self, data: Dict[str, Any]) -> bytes:
        """
        Generate 契約書 (Labor Contract).

        Employment contract between dispatch company and worker.

        Args:
            data: Contract data

        Returns:
            Excel file as bytes
        """
        wb = TemplateManager.get_template("keiyakusho")
        ws = wb.active

        dispatch_co = self._get_dispatch_company_info()

        replacements = {
            "{{contract_date}}": self._format_date_japanese(
                data.get("contract_date", date.today())
            ),
            "{{employee_name}}": data.get("employee_name", ""),
            "{{employee_address}}": data.get("employee_address", ""),
            "{{dispatch_company}}": dispatch_co["name"],
            "{{dispatch_address}}": dispatch_co["address"],
            "{{manager_name}}": dispatch_co["manager_name"],
            "{{employment_start}}": self._format_date_japanese(
                data.get("employment_start_date")
            ),
            "{{employment_end}}": self._format_date_japanese(
                data.get("employment_end_date")
            ),
            "{{hourly_rate}}": self._format_currency(data.get("hourly_rate")),
        }

        self._find_and_replace_all(ws, replacements)
        return self._workbook_to_bytes(wb)

    # ========================================
    # BATCH GENERATION
    # ========================================

    def generate_all_documents(
        self, data: Dict[str, Any]
    ) -> Dict[str, bytes]:
        """
        Generate all documents for a contract.

        Args:
            data: Complete contract data

        Returns:
            Dict mapping document name to bytes
        """
        results = {}

        try:
            results["kobetsu_keiyakusho"] = self.generate_kobetsu_keiyakusho(data)
        except Exception as e:
            results["kobetsu_keiyakusho_error"] = str(e)

        try:
            results["tsuchisho"] = self.generate_tsuchisho(data)
        except Exception as e:
            results["tsuchisho_error"] = str(e)

        try:
            results["hakenmoto_daicho"] = self.generate_hakenmoto_daicho(data)
        except Exception as e:
            results["hakenmoto_daicho_error"] = str(e)

        try:
            results["shugyo_joken"] = self.generate_shugyo_joken(data)
        except Exception as e:
            results["shugyo_joken_error"] = str(e)

        return results
