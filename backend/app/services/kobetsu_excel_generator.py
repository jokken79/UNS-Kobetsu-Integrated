"""
Kobetsu Excel Generator - Generates standalone Japanese dispatch documents.

This service creates completely independent Excel documents by:
1. Loading the original template with multiple sheets
2. Extracting a specific sheet (1-6)
3. Replacing ALL formulas with static values from contract data
4. Removing external references ([1]!TBKaishaInfo)
5. Preserving formatting through XML manipulation

Supported document types:
- 個別契約書 (Individual Contract) - Sheet 1
- 通知書 (Notification) - Sheet 2
- DAICHO (Registry) - Sheet 3
- 派遣元管理台帳 (Dispatch Origin Registry) - Sheet 4
- 就業条件明示書 (Employment Conditions) - Sheet 5
- 契約書 (Employment Contract) - Sheet 6

The generated document can be opened and printed without any external dependencies.
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
import copy
import shutil

from app.core.config import settings


class KobetsuExcelGenerator:
    """
    Generates standalone Japanese dispatch contract documents.

    All formulas are replaced with static values from the contract data,
    creating documents that work independently without external data sources.
    """

    ORIGINAL_TEMPLATE = "/app/ExcelKobetsukeiyakusho.xlsx"

    # Sheet configurations: sheet_number -> (sheet_name, japanese_title, print_area)
    # print_area format: (start_col, start_row, end_col, end_row)
    # Column numbers: A=1, B=2, ..., Z=26, AA=27, AB=28, etc.
    SHEET_INFO = {
        1: ("sheet1.xml", "個別契約書", (1, 1, 27, 64)),    # A1:AA64
        2: ("sheet2.xml", "通知書", (8, 1, 16, 60)),        # H1:P60 (starts at H!)
        3: ("sheet3.xml", "DAICHO", (1, 1, 57, 78)),        # A1:BE78
        4: ("sheet4.xml", "派遣元管理台帳", (1, 1, 28, 71)), # A1:AB71
        5: ("sheet5.xml", "就業条件明示書", (1, 1, 27, 56)), # A1:AA56
        6: ("sheet6.xml", "契約書", (1, 1, 18, 54)),        # A1:R54
    }

    # Cell mapping: cell_ref -> (data_key, value_type, default)
    # This maps every cell that needs data to its source field
    CELL_MAP = {
        # === Control cells (column AD) - these drive formulas ===
        'AD1': ('company_name', 'text', ''),           # 派遣先
        'AD2': ('factory_name', 'text', ''),           # 工場名
        'AD3': ('department', 'text', ''),             # 配属先
        'AD4': ('line', 'text', ''),                   # ライン
        'AD5': ('hourly_rate', 'number', 0),           # 時給単価
        'AD7': ('dispatch_start_date', 'date', None),  # 派遣開始日

        # === Row 4: 派遣先事業所 (Client company info) ===
        'I4': ('company_name', 'text', ''),            # 名称
        'Q4': ('company_address', 'text', ''),         # 所在地

        # === Row 5: 就業場所 (Work location) ===
        'I5': ('worksite_name', 'text', ''),           # 就業場所名
        'Q5': ('worksite_address', 'text', ''),        # 就業場所住所

        # === Row 6: 組織単位 (Organization unit) ===
        'H6': ('organizational_unit', 'text', ''),     # 組織単位名
        'Q6': ('restriction_date', 'text', ''),        # 抵触日

        # === Row 7: 指揮命令者 (Supervisor) ===
        'J7': ('supervisor_department', 'text', ''),   # 部署
        'Q7': ('supervisor_position', 'text', ''),     # 役職
        'W7': ('supervisor_name', 'text', ''),         # 氏名

        # === Row 8: 製造業務専門派遣先責任者 ===
        'J8': ('mfg_manager_department', 'text', ''),  # 部署
        'Q8': ('mfg_manager_position', 'text', ''),    # 役職
        'W8': ('mfg_manager_name', 'text', ''),        # 氏名

        # === Row 9: 苦情処理担当者 (Complaint handler - client) ===
        'J9': ('complaint_handler_dept', 'text', ''),  # 部署
        'Q9': ('complaint_handler_pos', 'text', ''),   # 役職
        'W9': ('complaint_handler_name', 'text', ''),  # 氏名

        # === Row 10: 製造業務専門派遣元責任者 (Our responsible person) ===
        'J10': ('our_mfg_manager_dept', 'text', 'ユニバーサル企画株式会社'),
        'Q10': ('our_mfg_manager_pos', 'text', '代表取締役'),
        'W10': ('our_mfg_manager_name', 'text', '松尾章子'),

        # === Row 11: 苦情処理担当者 (Our complaint handler) ===
        'J11': ('our_complaint_dept', 'text', 'ユニバーサル企画株式会社'),
        'Q11': ('our_complaint_pos', 'text', '代表取締役'),
        'W11': ('our_complaint_name', 'text', '松尾章子'),

        # === Row 15: 業務内容 (Work content) ===
        'H15': ('work_content', 'text', ''),           # 業務内容

        # === Row 16: 派遣期間 (Dispatch period) ===
        'H16': ('dispatch_start_date', 'date', None),  # 開始日
        'P16': ('dispatch_end_date', 'date', None),    # 終了日
        'X16': ('num_workers', 'number', 1),           # 人数

        # === Row 17: 就業日 (Work days) ===
        'H17': ('work_days_text', 'text', '月曜日から金曜日まで'),

        # === Row 18: 就業時間 (Work hours) ===
        'H18': ('work_hours_text', 'text', ''),        # 就業時間テキスト

        # === Row 22: 休憩時間 (Break time) ===
        'H22': ('break_time_text', 'text', ''),        # 休憩時間テキスト

        # === Row 26-27: 時間外労働 (Overtime) ===
        'H26': ('overtime_outside_days', 'text', '有'),  # 就業日外労働
        'H27': ('overtime_text', 'text', ''),            # 時間外労働詳細

        # === Row 29-30: 派遣料金 (Dispatch fee) ===
        'K29': ('hourly_rate', 'number', 0),           # 基本時給
        'Q29': ('overtime_rate_25', 'number', 0),      # 25%割増
        'K30': ('overtime_rate_35', 'number', 0),      # 35%割増
        'N30': ('night_rate', 'number', 0),            # 深夜割増

        # === Row 32-33: 支払い条件 (Payment terms) ===
        'K32': ('payment_deadline', 'text', '月末締め'),  # 締日
        'Q32': ('payment_date', 'text', '翌月25日払い'),  # 支払日
        'J33': ('bank_info', 'text', '十八銀行/南部支店/普通/1055579'),  # 振込先
    }

    # Cell mapping for Sheet 2: 通知書 (Notification)
    TSUCHISHO_CELL_MAP = {
        # Header info
        'B2': ('dispatch_date_text', 'text', ''),         # 通知日
        'J3': ('company_name', 'text', ''),               # 派遣先会社名

        # Dispatch details
        'D6': ('dispatch_start_date', 'date', None),      # 派遣開始日
        'H6': ('dispatch_end_date', 'date', None),        # 派遣終了日
        'D8': ('worksite_name', 'text', ''),              # 就業場所
        'D10': ('work_content', 'text', ''),              # 業務内容
        'D12': ('supervisor_name', 'text', ''),           # 指揮命令者
        'D14': ('num_workers', 'number', 1),              # 派遣人数

        # Work schedule
        'D16': ('work_days_text', 'text', ''),            # 就業日
        'D18': ('work_hours_text', 'text', ''),           # 就業時間
        'D20': ('break_time_text', 'text', ''),           # 休憩時間

        # Company info (our company)
        'B26': ('our_company_name', 'text', 'ユニバーサル企画株式会社'),
        'B27': ('our_company_address', 'text', '長崎県佐世保市田原町13-6'),
        'B28': ('our_company_rep', 'text', '代表取締役 松尾章子'),
    }

    # Cell mapping for Sheet 3: DAICHO (Registry)
    DAICHO_CELL_MAP = {
        # Header
        'A1': ('title', 'text', '派遣先管理台帳'),
        'L2': ('created_date', 'date', None),             # 作成日

        # Employee info
        'B4': ('employee_name', 'text', ''),              # 派遣労働者氏名
        'H4': ('employee_katakana', 'text', ''),          # フリガナ
        'B6': ('employee_number', 'text', ''),            # 社員番号
        'H6': ('employee_dob', 'date', None),             # 生年月日
        'B8': ('employee_gender', 'text', ''),            # 性別

        # Assignment info
        'B10': ('company_name', 'text', ''),              # 派遣先名称
        'B12': ('worksite_name', 'text', ''),             # 就業場所
        'B14': ('organizational_unit', 'text', ''),       # 組織単位
        'B16': ('work_content', 'text', ''),              # 業務内容

        # Period
        'B18': ('dispatch_start_date', 'date', None),     # 派遣開始日
        'H18': ('dispatch_end_date', 'date', None),       # 派遣終了日

        # Contact info
        'B20': ('supervisor_name', 'text', ''),           # 指揮命令者
        'H20': ('supervisor_position', 'text', ''),       # 役職
        'B22': ('complaint_handler_name', 'text', ''),    # 苦情処理担当者

        # Work schedule
        'B24': ('work_days_text', 'text', ''),            # 就業日
        'B26': ('work_hours_text', 'text', ''),           # 就業時間
        'H26': ('break_time_text', 'text', ''),           # 休憩時間
    }

    # Cell mapping for Sheet 4: 派遣元管理台帳 (Dispatch Origin Registry)
    HAKENMOTO_DAICHO_CELL_MAP = {
        # Header
        'A1': ('title', 'text', '派遣元管理台帳'),
        'L2': ('created_date', 'date', None),

        # Employee info
        'B4': ('employee_name', 'text', ''),
        'H4': ('employee_katakana', 'text', ''),
        'B6': ('employee_address', 'text', ''),
        'B8': ('employee_phone', 'text', ''),

        # Dispatch destination
        'B10': ('company_name', 'text', ''),
        'B12': ('factory_name', 'text', ''),
        'B14': ('worksite_address', 'text', ''),
        'B16': ('work_content', 'text', ''),

        # Period and fee
        'B18': ('dispatch_start_date', 'date', None),
        'H18': ('dispatch_end_date', 'date', None),
        'B20': ('hourly_rate', 'number', 0),

        # Schedule
        'B22': ('work_days_text', 'text', ''),
        'B24': ('work_hours_text', 'text', ''),

        # Responsible persons
        'B26': ('our_manager_name', 'text', '松尾章子'),
        'B28': ('our_complaint_handler', 'text', '松尾章子'),
    }

    # Cell mapping for Sheet 5: 就業条件明示書 (Employment Conditions)
    SHUGYO_JOKEN_CELL_MAP = {
        # Header
        'A1': ('title', 'text', '就業条件明示書'),
        'K2': ('issue_date', 'date', None),
        'B4': ('employee_name', 'text', ''),

        # Dispatch destination
        'B6': ('company_name', 'text', ''),
        'B8': ('factory_name', 'text', ''),
        'B10': ('worksite_address', 'text', ''),
        'B12': ('organizational_unit', 'text', ''),

        # Work details
        'B14': ('work_content', 'text', ''),
        'B16': ('supervisor_name', 'text', ''),

        # Period
        'B18': ('dispatch_start_date', 'date', None),
        'G18': ('dispatch_end_date', 'date', None),

        # Schedule
        'B20': ('work_days_text', 'text', ''),
        'B22': ('work_hours_text', 'text', ''),
        'B24': ('break_time_text', 'text', ''),

        # Overtime
        'B26': ('overtime_text', 'text', ''),

        # Holidays
        'B28': ('holidays_text', 'text', ''),

        # Wage
        'B30': ('hourly_rate', 'number', 0),
        'B32': ('payment_date', 'text', ''),

        # Safety and welfare
        'B34': ('safety_health_text', 'text', ''),
        'B36': ('welfare_text', 'text', ''),

        # Complaint handling
        'B38': ('client_complaint_handler', 'text', ''),
        'B40': ('our_complaint_handler', 'text', '松尾章子'),
    }

    # Cell mapping for Sheet 6: 契約書 (Employment Contract)
    KEIYAKUSHO_CELL_MAP = {
        # Header
        'A1': ('title', 'text', '雇用契約書'),
        'K2': ('contract_date', 'date', None),

        # Employee info
        'B4': ('employee_name', 'text', ''),
        'H4': ('employee_address', 'text', ''),

        # Contract type
        'B6': ('contract_type', 'text', '有期雇用'),
        'H6': ('employment_type', 'text', '派遣労働者'),

        # Period
        'B8': ('contract_start_date', 'date', None),
        'H8': ('contract_end_date', 'date', None),

        # Work location
        'B10': ('work_location', 'text', ''),
        'B12': ('work_content', 'text', ''),

        # Schedule
        'B14': ('work_hours_text', 'text', ''),
        'B16': ('break_time_text', 'text', ''),
        'B18': ('work_days_text', 'text', ''),
        'B20': ('holidays_text', 'text', ''),

        # Wage
        'B22': ('wage_type', 'text', '時給'),
        'H22': ('hourly_rate', 'number', 0),
        'B24': ('payment_method', 'text', '銀行振込'),
        'H24': ('payment_date', 'text', '翌月25日'),

        # Social insurance
        'B26': ('health_insurance', 'text', '加入'),
        'H26': ('pension', 'text', '加入'),
        'B28': ('employment_insurance', 'text', '加入'),
        'H28': ('workers_comp', 'text', '加入'),

        # Other
        'B30': ('retirement_benefit', 'text', 'なし'),
        'B32': ('bonus', 'text', 'なし'),
        'B34': ('renewal_conditions', 'text', ''),

        # Company signature
        'B38': ('our_company_name', 'text', 'ユニバーサル企画株式会社'),
        'B39': ('our_company_address', 'text', '長崎県佐世保市田原町13-6'),
        'B40': ('our_company_rep', 'text', '代表取締役 松尾章子'),
    }

    # Map document types to their cell mappings
    CELL_MAPS = {
        1: 'CELL_MAP',              # 個別契約書
        2: 'TSUCHISHO_CELL_MAP',    # 通知書
        3: 'DAICHO_CELL_MAP',       # DAICHO
        4: 'HAKENMOTO_DAICHO_CELL_MAP',  # 派遣元管理台帳
        5: 'SHUGYO_JOKEN_CELL_MAP', # 就業条件明示書
        6: 'KEIYAKUSHO_CELL_MAP',   # 契約書
    }

    # ====================================================================
    # PUBLIC METHODS - Generate specific document types
    # ====================================================================

    @classmethod
    def generate(cls, data: Dict[str, Any]) -> bytes:
        """
        Generate a complete 個別契約書 document with all data filled in.
        This is the main method for generating individual contract documents.

        Args:
            data: Dictionary with contract data. Keys should match CELL_MAP data_keys.

        Returns:
            bytes: The generated xlsx file content
        """
        return cls._generate_from_sheet(1, data, cls.CELL_MAP, hide_control_columns=True)

    @classmethod
    def generate_tsuchisho(cls, data: Dict[str, Any]) -> bytes:
        """
        Generate 通知書 (Notification) document - Sheet 2.

        Args:
            data: Dictionary with notification data.

        Returns:
            bytes: The generated xlsx file content
        """
        return cls._generate_from_sheet(2, data, cls.TSUCHISHO_CELL_MAP)

    @classmethod
    def generate_daicho(cls, data: Dict[str, Any]) -> bytes:
        """
        Generate DAICHO (派遣先管理台帳 - Dispatch Destination Registry) document - Sheet 3.

        Args:
            data: Dictionary with employee assignment data.

        Returns:
            bytes: The generated xlsx file content
        """
        return cls._generate_from_sheet(3, data, cls.DAICHO_CELL_MAP)

    @classmethod
    def generate_hakenmoto_daicho(cls, data: Dict[str, Any]) -> bytes:
        """
        Generate 派遣元管理台帳 (Dispatch Origin Registry) document - Sheet 4.

        Args:
            data: Dictionary with dispatch origin data.

        Returns:
            bytes: The generated xlsx file content
        """
        return cls._generate_from_sheet(4, data, cls.HAKENMOTO_DAICHO_CELL_MAP)

    @classmethod
    def generate_shugyo_joken(cls, data: Dict[str, Any]) -> bytes:
        """
        Generate 就業条件明示書 (Employment Conditions Statement) document - Sheet 5.

        Args:
            data: Dictionary with employment conditions data.

        Returns:
            bytes: The generated xlsx file content
        """
        return cls._generate_from_sheet(5, data, cls.SHUGYO_JOKEN_CELL_MAP)

    @classmethod
    def generate_keiyakusho(cls, data: Dict[str, Any]) -> bytes:
        """
        Generate 契約書 (Employment Contract) document - Sheet 6.

        Args:
            data: Dictionary with employment contract data.

        Returns:
            bytes: The generated xlsx file content
        """
        return cls._generate_from_sheet(6, data, cls.KEIYAKUSHO_CELL_MAP)

    # ====================================================================
    # GENERIC GENERATOR - Core method that all specific generators use
    # ====================================================================

    @classmethod
    def _generate_from_sheet(
        cls,
        sheet_number: int,
        data: Dict[str, Any],
        cell_map: Dict[str, Tuple[str, str, Any]],
        hide_control_columns: bool = False
    ) -> bytes:
        """
        Generate a document from a specific sheet of the original template.

        Args:
            sheet_number: Sheet number (1-6)
            data: Dictionary with data to fill in
            cell_map: Cell mapping for this document type
            hide_control_columns: Whether to hide control columns (only for sheet 1)

        Returns:
            bytes: The generated xlsx file content
        """
        template_path = Path(cls.ORIGINAL_TEMPLATE)
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {cls.ORIGINAL_TEMPLATE}")

        if sheet_number not in cls.SHEET_INFO:
            raise ValueError(f"Invalid sheet number: {sheet_number}. Must be 1-6.")

        sheet_filename, sheet_title, print_area = cls.SHEET_INFO[sheet_number]

        # Prepare computed values
        prepared_data = cls._prepare_data(data)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Extract the xlsx
            with zipfile.ZipFile(template_path, 'r') as z:
                z.extractall(temp_path)

            # Process the target sheet
            sheet_path = temp_path / 'xl' / 'worksheets' / sheet_filename
            if not sheet_path.exists():
                raise FileNotFoundError(f"Sheet {sheet_filename} not found in template")

            sheet_content = sheet_path.read_text(encoding='utf-8')

            # Replace ALL formulas with static values
            sheet_content = cls._replace_all_formulas(sheet_content, prepared_data)

            # Set the cells with data from the mapping
            for cell_ref, (data_key, value_type, default) in cell_map.items():
                value = prepared_data.get(data_key, default)
                if value is not None:
                    sheet_content = cls._set_cell_value(
                        sheet_content, cell_ref, value, value_type
                    )

            # Write modified sheet
            sheet_path.write_text(sheet_content, encoding='utf-8')

            # Remove external links if any
            cls._remove_external_links(temp_path)

            # NOTE: _clean_outside_print_area was causing XML corruption in sheets 4,5,6
            # Disabled for now - documents will have extra content outside print area
            # but will at least open without errors. Print areas are still set correctly.
            # TODO: Fix the regex patterns that break XML structure
            # sheet_content = sheet_path.read_text(encoding='utf-8')
            # sheet_content = cls._clean_outside_print_area(sheet_content, print_area)
            # sheet_path.write_text(sheet_content, encoding='utf-8')

            # Hide control columns if needed (only for sheet 1)
            if hide_control_columns:
                sheet_content = sheet_path.read_text(encoding='utf-8')
                sheet_content = cls._hide_control_columns(sheet_content)
                sheet_path.write_text(sheet_content, encoding='utf-8')

            # Clean up problematic files that cause Excel repair warnings
            cls._cleanup_problematic_files(temp_path)

            # Keep only the target sheet, rename it appropriately
            cls._keep_only_target_sheet(temp_path, sheet_number, sheet_title)

            # Repackage xlsx
            output = BytesIO()
            with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zout:
                for item in temp_path.rglob('*'):
                    if item.is_file():
                        arcname = str(item.relative_to(temp_path)).replace('\\', '/')
                        zout.write(item, arcname)

            return output.getvalue()

    @classmethod
    def _prepare_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare and compute derived values from input data.
        """
        result = dict(data)

        # Compute worksite name from factory info
        if not result.get('worksite_name'):
            parts = []
            if result.get('company_name'):
                parts.append(result['company_name'])
            if result.get('factory_name'):
                parts.append(result['factory_name'])
            result['worksite_name'] = ' '.join(parts) if parts else ''

        # Compute worksite address from factory address
        if not result.get('worksite_address'):
            result['worksite_address'] = result.get('factory_address', result.get('company_address', ''))

        # Compute organizational unit
        if not result.get('organizational_unit'):
            parts = []
            if result.get('department'):
                parts.append(result['department'])
            if result.get('line'):
                parts.append(result['line'])
            result['organizational_unit'] = ' '.join(parts) if parts else ''

        # Compute overtime rates from hourly rate
        hourly = result.get('hourly_rate', 0) or 0
        if hourly:
            result['overtime_rate_25'] = int(hourly * 0.0125 * 100)  # 25% markup
            result['overtime_rate_35'] = int(hourly * 0.0135 * 100)  # 35% markup
            result['night_rate'] = int(hourly * 0.0025 * 100)        # Night markup

        # Format work hours text
        if not result.get('work_hours_text'):
            start = result.get('work_start_time', '08:00')
            end = result.get('work_end_time', '17:00')
            result['work_hours_text'] = f'{start} ～ {end}'

        # Format break time text
        if not result.get('break_time_text'):
            break_min = result.get('break_duration_minutes', 60)
            result['break_time_text'] = f'{break_min}分'

        # Format overtime text
        if not result.get('overtime_text'):
            max_day = result.get('overtime_hours_per_day', 4)
            max_month = result.get('overtime_hours_per_month', 45)
            result['overtime_text'] = f'1日{max_day}時間、1ヶ月{max_month}時間を限度とする'

        return result

    @classmethod
    def _replace_all_formulas(cls, sheet_xml: str, data: Dict[str, Any]) -> str:
        """
        Replace ALL formula cells with static values.

        This removes all <f>...</f> tags and replaces them with computed values.
        """
        # Pattern to find cells with formulas
        # <c r="J4" s="123"><f>formula</f><v>value</v></c>
        # or <c r="J4" s="123" t="s"><f>formula</f><v>index</v></c>

        def replace_formula(match):
            """Replace a formula cell with a static value."""
            full_match = match.group(0)
            cell_ref = match.group(1)
            attrs_after_ref = match.group(2)  # Everything after r="XX" before >
            formula = match.group(3)

            # Get the value for this cell from our mapping
            cell_mapping = cls.CELL_MAP.get(cell_ref)
            if cell_mapping:
                data_key, value_type, default = cell_mapping
                value = data.get(data_key, default)
            else:
                # For cells not in our map, try to compute from formula
                value = cls._compute_formula_value(cell_ref, formula, data)

            if value is None:
                value = ''

            # Format the value appropriately
            if isinstance(value, (date, datetime)):
                # Convert to Excel serial number
                excel_value = cls._date_to_excel_serial(value)
                return f'<c r="{cell_ref}"{attrs_after_ref}><v>{excel_value}</v></c>'
            elif isinstance(value, (int, float, Decimal)):
                return f'<c r="{cell_ref}"{attrs_after_ref}><v>{value}</v></c>'
            else:
                # String value - use inline string
                str_value = str(value)
                str_value = str_value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                # Remove any existing type attribute
                attrs_clean = re.sub(r'\s*t="[^"]*"', '', attrs_after_ref)
                return f'<c r="{cell_ref}"{attrs_clean} t="inlineStr"><is><t>{str_value}</t></is></c>'

        # Pattern: <c r="XX"...><f>...</f>...</c>
        pattern = r'<c r="([A-Z]+[0-9]+)"([^>]*)><f[^>]*>([^<]*)</f>(?:<v>[^<]*</v>)?</c>'
        sheet_xml = re.sub(pattern, replace_formula, sheet_xml)

        # Also handle ArrayFormula patterns
        pattern2 = r'<c r="([A-Z]+[0-9]+)"([^>]*)><f[^>]*/></c>'
        sheet_xml = re.sub(pattern2, replace_formula, sheet_xml)

        return sheet_xml

    @classmethod
    def _compute_formula_value(cls, cell_ref: str, formula: str, data: Dict[str, Any]) -> Any:
        """
        Compute the value for a formula cell based on the formula content.

        This handles formulas not explicitly mapped in CELL_MAP.
        """
        # Named cell references in the original Excel
        if '派遣先' in formula and 'XLOOKUP' not in formula.upper():
            return data.get('company_name', '')
        if '工場名' in formula and 'XLOOKUP' not in formula.upper():
            return data.get('factory_name', '')
        if '配属先' in formula and 'XLOOKUP' not in formula.upper():
            return data.get('department', '')
        if 'ライン' in formula and 'XLOOKUP' not in formula.upper():
            return data.get('line', '')
        if 'AD5' in formula:
            return data.get('hourly_rate', 0)
        if 'DateStart' in formula or 'AD7' in formula:
            return data.get('dispatch_start_date')

        # XLOOKUP formulas - these need specific handling
        if 'XLOOKUP' in formula.upper() or '[1]!TBKaishaInfo' in formula:
            # Determine what the XLOOKUP is looking for
            if '派遣先住所' in formula:
                return data.get('company_address', '')
            if '工場住所' in formula:
                return data.get('worksite_address', data.get('factory_address', ''))
            if '派遣先責任者' in formula or '指揮命令者' in formula:
                return data.get('supervisor_name', '')
            if '就業日' in formula:
                return data.get('work_days_text', '月曜日から金曜日まで')
            if '開始時間' in formula:
                return data.get('work_start_time', '08:00')
            if '終了時間' in formula:
                return data.get('work_end_time', '17:00')
            if '休憩時間' in formula:
                return data.get('break_time_text', '60分')
            if '業務内容' in formula:
                return data.get('work_content', '')
            if '時間外' in formula or '残業' in formula:
                return data.get('overtime_text', '')

        # Title cells
        if cell_ref == 'J1':
            return '人材派遣個別契約書'
        if cell_ref == 'AJ1':
            company = data.get('company_name', '')
            return f'{company}（以下、「甲」という）とユニバーサル企画株式会社（以下、「乙」という）間で締結された労働者派遣基本契約書の定めに従い、次の派遣要件に基づき労働者派遣契約書を締結する。'

        # Default: return empty string
        return ''

    @classmethod
    def _set_cell_value(cls, sheet_xml: str, cell_ref: str, value: Any, value_type: str) -> str:
        """
        Set a cell value, creating the cell if it doesn't exist.
        """
        if value is None:
            return sheet_xml

        if value_type == 'date':
            if isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    return sheet_xml
            if isinstance(value, (date, datetime)):
                excel_value = cls._date_to_excel_serial(value)
                # Must remove t="s" attribute if present, otherwise Excel tries to use date as string index
                def replace_with_date(match):
                    attrs = match.group(1)
                    # Remove t="..." attribute (especially t="s" for shared strings)
                    attrs = re.sub(r'\s*t="[^"]*"', '', attrs)
                    return f'<c r="{cell_ref}"{attrs}><v>{excel_value}</v></c>'
                pattern = rf'<c r="{cell_ref}"([^>]*)>(?:<f>[^<]*</f>)?<v>[^<]*</v></c>'
                sheet_xml = re.sub(pattern, replace_with_date, sheet_xml)

        elif value_type == 'number':
            numeric = float(value) if value else 0
            # Must remove t="s" attribute if present, otherwise Excel tries to use numeric as string index
            def replace_with_number(match):
                attrs = match.group(1)
                # Remove t="..." attribute (especially t="s" for shared strings)
                attrs = re.sub(r'\s*t="[^"]*"', '', attrs)
                return f'<c r="{cell_ref}"{attrs}><v>{numeric}</v></c>'
            pattern = rf'<c r="{cell_ref}"([^>]*)>(?:<f>[^<]*</f>)?<v>[^<]*</v></c>'
            sheet_xml = re.sub(pattern, replace_with_number, sheet_xml)

        else:  # text
            str_value = str(value) if value else ''
            str_value = str_value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            def replace_with_inline(match):
                attrs = match.group(1)
                attrs = re.sub(r'\s*t="[^"]*"', '', attrs)
                return f'<c r="{cell_ref}"{attrs} t="inlineStr"><is><t>{str_value}</t></is></c>'

            pattern = rf'<c r="{cell_ref}"([^>]*)>(?:<f>[^<]*</f>)?<v>[^<]*</v></c>'
            sheet_xml = re.sub(pattern, replace_with_inline, sheet_xml)

        return sheet_xml

    @classmethod
    def _clean_outside_print_area(
        cls,
        sheet_xml: str,
        print_area: Tuple[int, int, int, int]
    ) -> str:
        """
        Remove all content outside the print area.

        Args:
            sheet_xml: The sheet XML content
            print_area: Tuple of (start_col, start_row, end_col, end_row)
                       Column numbers: A=1, B=2, ..., Z=26, AA=27, etc.

        Returns:
            Modified XML with content only in print area
        """
        start_col, start_row, end_col, end_row = print_area

        def col_num_to_letter(n: int) -> str:
            """Convert column number to letter (1=A, 27=AA, etc.)"""
            result = ""
            while n > 0:
                n, remainder = divmod(n - 1, 26)
                result = chr(65 + remainder) + result
            return result

        def letter_to_col_num(letters: str) -> int:
            """Convert column letter to number (A=1, AA=27, etc.)"""
            result = 0
            for char in letters.upper():
                result = result * 26 + (ord(char) - ord('A') + 1)
            return result

        def is_in_print_area(cell_ref: str) -> bool:
            """Check if a cell reference is within the print area."""
            match = re.match(r'^([A-Z]+)(\d+)$', cell_ref)
            if not match:
                return False
            col_letters, row_str = match.groups()
            col = letter_to_col_num(col_letters)
            row = int(row_str)
            return (start_col <= col <= end_col) and (start_row <= row <= end_row)

        # Remove cells outside print area
        def filter_cell(match):
            cell_ref = match.group(1)
            if is_in_print_area(cell_ref):
                return match.group(0)  # Keep the cell
            return ''  # Remove the cell

        # Pattern to match cells: <c r="XX"...>...</c>
        cell_pattern = r'<c r="([A-Z]+\d+)"[^>]*>.*?</c>'
        sheet_xml = re.sub(cell_pattern, filter_cell, sheet_xml, flags=re.DOTALL)

        # Also handle self-closing cells: <c r="XX".../>
        cell_pattern_self = r'<c r="([A-Z]+\d+)"[^/]*/>'
        sheet_xml = re.sub(cell_pattern_self, filter_cell, sheet_xml)

        # Remove empty rows (rows with no cells left)
        def filter_row(match):
            row_content = match.group(0)
            # Check if row has any cells
            if re.search(r'<c r="[A-Z]+\d+"', row_content):
                return row_content
            # Keep the row but empty
            row_num = match.group(1)
            spans = match.group(2) or ''
            return f'<row r="{row_num}"{spans}></row>'

        row_pattern = r'<row r="(\d+)"([^>]*)>(.*?)</row>'
        sheet_xml = re.sub(row_pattern, filter_row, sheet_xml, flags=re.DOTALL)

        # Update dimensions to match print area
        start_col_letter = col_num_to_letter(start_col)
        end_col_letter = col_num_to_letter(end_col)
        new_dimension = f'{start_col_letter}{start_row}:{end_col_letter}{end_row}'
        sheet_xml = re.sub(
            r'<dimension ref="[^"]*"/>',
            f'<dimension ref="{new_dimension}"/>',
            sheet_xml
        )

        # Update column definitions to only include columns in print area
        def filter_cols(match):
            cols_content = match.group(1)
            filtered_cols = []

            # Find all col elements
            col_pattern = r'<col min="(\d+)" max="(\d+)"([^/]*)/?>'
            for col_match in re.finditer(col_pattern, cols_content):
                min_col = int(col_match.group(1))
                max_col = int(col_match.group(2))
                attrs = col_match.group(3)

                # Only include if overlaps with print area
                if max_col >= start_col and min_col <= end_col:
                    # Clamp to print area
                    new_min = max(min_col, start_col)
                    new_max = min(max_col, end_col)
                    filtered_cols.append(f'<col min="{new_min}" max="{new_max}"{attrs}/>')

            if filtered_cols:
                return '<cols>' + ''.join(filtered_cols) + '</cols>'
            return '<cols></cols>'

        sheet_xml = re.sub(r'<cols>(.*?)</cols>', filter_cols, sheet_xml, flags=re.DOTALL)

        return sheet_xml

    @classmethod
    def _cleanup_problematic_files(cls, temp_path: Path) -> None:
        """
        Remove files that cause Excel repair warnings.
        This includes:
        - calcChain.xml (formula calculation chain)
        - printerSettings (often corrupted)
        - drawings (may reference external content)
        - definedNames (named ranges that reference deleted sheets)
        - ctrlProps (ActiveX control properties)
        - comments (cell comments)
        - threadedComments (threaded comment system)
        - persons (person metadata for comments)
        """
        import shutil

        # Remove calcChain.xml (formula calculation chain - not needed without formulas)
        calc_chain = temp_path / 'xl' / 'calcChain.xml'
        if calc_chain.exists():
            calc_chain.unlink()

        # Remove printerSettings folder (often corrupted)
        printer_settings = temp_path / 'xl' / 'printerSettings'
        if printer_settings.exists():
            shutil.rmtree(printer_settings)

        # Remove drawings folder entirely
        drawings = temp_path / 'xl' / 'drawings'
        if drawings.exists():
            shutil.rmtree(drawings)

        # Remove drawings/_rels folder if exists
        drawings_rels = temp_path / 'xl' / 'drawings' / '_rels'
        if drawings_rels.exists():
            shutil.rmtree(drawings_rels)

        # Remove ctrlProps folder (ActiveX control properties - causes errors in sheets 4,5)
        ctrl_props = temp_path / 'xl' / 'ctrlProps'
        if ctrl_props.exists():
            shutil.rmtree(ctrl_props)

        # Remove comments XML files
        for comments_file in (temp_path / 'xl').glob('comments*.xml'):
            comments_file.unlink()

        # Remove threadedComments folder
        threaded_comments = temp_path / 'xl' / 'threadedComments'
        if threaded_comments.exists():
            shutil.rmtree(threaded_comments)

        # Remove persons folder (metadata for comment authors)
        persons = temp_path / 'xl' / 'persons'
        if persons.exists():
            shutil.rmtree(persons)

        # Update Content_Types.xml to remove references to deleted files
        content_types = temp_path / '[Content_Types].xml'
        if content_types.exists():
            content = content_types.read_text(encoding='utf-8')
            # Remove printerSettings references
            content = re.sub(r'<Override[^>]*printerSettings[^>]*/>', '', content)
            # Remove calcChain reference
            content = re.sub(r'<Override[^>]*calcChain[^>]*/>', '', content)
            # Remove drawings references
            content = re.sub(r'<Override[^>]*drawings[^>]*/>', '', content)
            content = re.sub(r'<Default[^>]*vmlDrawing[^>]*/>', '', content)
            # Remove ctrlProps references
            content = re.sub(r'<Override[^>]*ctrlProps[^>]*/>', '', content)
            content = re.sub(r'<Default[^>]*ActiveX[^>]*/>', '', content)
            # Remove comments references
            content = re.sub(r'<Override[^>]*comments[^>]*/>', '', content)
            # Remove threadedComments references
            content = re.sub(r'<Override[^>]*threadedComments[^>]*/>', '', content)
            # Remove persons references
            content = re.sub(r'<Override[^>]*persons[^>]*/>', '', content)
            content_types.write_text(content, encoding='utf-8')

        # Update workbook.xml - remove definedNames and calcChain references
        workbook_xml = temp_path / 'xl' / 'workbook.xml'
        if workbook_xml.exists():
            content = workbook_xml.read_text(encoding='utf-8')
            # Remove entire definedNames section (named ranges)
            content = re.sub(r'<definedNames>.*?</definedNames>', '', content, flags=re.DOTALL)
            # Also remove empty definedNames tag if present
            content = re.sub(r'<definedNames\s*/>', '', content)
            workbook_xml.write_text(content, encoding='utf-8')

        # Update workbook.xml.rels
        wb_rels = temp_path / 'xl' / '_rels' / 'workbook.xml.rels'
        if wb_rels.exists():
            content = wb_rels.read_text(encoding='utf-8')
            # Remove calcChain relationship
            content = re.sub(r'<Relationship[^>]*calcChain[^>]*/>', '', content)
            wb_rels.write_text(content, encoding='utf-8')

        # Update sheet rels to remove printerSettings, drawing, comment, and control references
        sheets_rels = temp_path / 'xl' / 'worksheets' / '_rels'
        if sheets_rels.exists():
            for rels_file in sheets_rels.glob('*.rels'):
                content = rels_file.read_text(encoding='utf-8')
                content = re.sub(r'<Relationship[^>]*printerSettings[^>]*/>', '', content)
                content = re.sub(r'<Relationship[^>]*drawing[^>]*/>', '', content)
                content = re.sub(r'<Relationship[^>]*vmlDrawing[^>]*/>', '', content)
                # Remove comment relationships
                content = re.sub(r'<Relationship[^>]*comments[^>]*/>', '', content)
                # Remove ctrlProp relationships
                content = re.sub(r'<Relationship[^>]*ctrlProp[^>]*/>', '', content)
                # Remove threadedComment relationships
                content = re.sub(r'<Relationship[^>]*threadedComment[^>]*/>', '', content)
                # Remove persons relationships
                content = re.sub(r'<Relationship[^>]*person[^>]*/>', '', content)
                rels_file.write_text(content, encoding='utf-8')

        # Remove drawing and control references from sheet XML files
        worksheets_dir = temp_path / 'xl' / 'worksheets'
        if worksheets_dir.exists():
            for sheet_file in worksheets_dir.glob('sheet*.xml'):
                content = sheet_file.read_text(encoding='utf-8')
                # Remove <drawing> element
                content = re.sub(r'<drawing[^>]*/>', '', content)
                # Remove <legacyDrawing> element
                content = re.sub(r'<legacyDrawing[^>]*/>', '', content)
                # Remove <controls> section (ActiveX controls)
                content = re.sub(r'<controls>.*?</controls>', '', content, flags=re.DOTALL)
                # Remove empty controls tag
                content = re.sub(r'<controls\s*/>', '', content)
                sheet_file.write_text(content, encoding='utf-8')

    @classmethod
    def _keep_only_sheet1(cls, temp_path: Path) -> None:
        """
        Remove all sheets except sheet1 (個別契約書X).
        This creates a clean single-sheet workbook.
        """
        import shutil

        worksheets_dir = temp_path / 'xl' / 'worksheets'

        # Remove sheets 2-6
        for i in range(2, 10):
            sheet_file = worksheets_dir / f'sheet{i}.xml'
            if sheet_file.exists():
                sheet_file.unlink()

        # Remove corresponding rels files
        rels_dir = worksheets_dir / '_rels'
        if rels_dir.exists():
            for i in range(2, 10):
                rels_file = rels_dir / f'sheet{i}.xml.rels'
                if rels_file.exists():
                    rels_file.unlink()

        # Update workbook.xml to reference only sheet1
        workbook_xml = temp_path / 'xl' / 'workbook.xml'
        if workbook_xml.exists():
            content = workbook_xml.read_text(encoding='utf-8')
            # Keep only the first sheet reference
            # Remove all <sheet> tags except the first one
            sheets_pattern = r'(<sheets>).*?(</sheets>)'

            def keep_first_sheet(match):
                sheets_section = match.group(0)
                # Find first sheet tag
                first_sheet_match = re.search(r'<sheet[^>]*name="[^"]*"[^>]*/>', sheets_section)
                if first_sheet_match:
                    first_sheet = first_sheet_match.group(0)
                    # Rename to 個別契約書
                    first_sheet = re.sub(r'name="[^"]*"', 'name="個別契約書"', first_sheet)
                    return f'<sheets>{first_sheet}</sheets>'
                return match.group(0)

            content = re.sub(sheets_pattern, keep_first_sheet, content, flags=re.DOTALL)
            workbook_xml.write_text(content, encoding='utf-8')

        # Update workbook.xml.rels to keep only sheet1 relationship
        wb_rels = temp_path / 'xl' / '_rels' / 'workbook.xml.rels'
        if wb_rels.exists():
            content = wb_rels.read_text(encoding='utf-8')
            # Remove relationships to sheets 2-6
            for i in range(2, 10):
                content = re.sub(rf'<Relationship[^>]*sheet{i}\.xml[^>]*/>', '', content)
            wb_rels.write_text(content, encoding='utf-8')

        # Update [Content_Types].xml
        content_types = temp_path / '[Content_Types].xml'
        if content_types.exists():
            content = content_types.read_text(encoding='utf-8')
            # Remove overrides for sheets 2-6
            for i in range(2, 10):
                content = re.sub(rf'<Override[^>]*sheet{i}\.xml[^>]*/>', '', content)
            content_types.write_text(content, encoding='utf-8')

    @classmethod
    def _keep_only_target_sheet(cls, temp_path: Path, sheet_number: int, sheet_title: str) -> None:
        """
        Keep only the target sheet and remove all others.
        Renames the target sheet to sheet1.xml for a clean single-sheet workbook.

        Args:
            temp_path: Path to the extracted xlsx directory
            sheet_number: The sheet number to keep (1-6)
            sheet_title: The Japanese title for the sheet
        """
        worksheets_dir = temp_path / 'xl' / 'worksheets'
        rels_dir = worksheets_dir / '_rels'

        # If target sheet is not sheet1, rename it
        if sheet_number != 1:
            target_sheet = worksheets_dir / f'sheet{sheet_number}.xml'
            target_rels = rels_dir / f'sheet{sheet_number}.xml.rels'
            sheet1_path = worksheets_dir / 'sheet1.xml'
            sheet1_rels = rels_dir / 'sheet1.xml.rels'

            # Remove original sheet1 if it exists
            if sheet1_path.exists():
                sheet1_path.unlink()
            if sheet1_rels.exists():
                sheet1_rels.unlink()

            # Rename target sheet to sheet1
            if target_sheet.exists():
                target_sheet.rename(sheet1_path)
            if target_rels.exists():
                target_rels.rename(sheet1_rels)

        # Remove all other sheets (2-9)
        for i in range(2, 10):
            sheet_file = worksheets_dir / f'sheet{i}.xml'
            if sheet_file.exists():
                sheet_file.unlink()

            rels_file = rels_dir / f'sheet{i}.xml.rels'
            if rels_file is not None and rels_file.exists():
                rels_file.unlink()

        # Update workbook.xml to reference only sheet1 with the correct title
        workbook_xml = temp_path / 'xl' / 'workbook.xml'
        if workbook_xml.exists():
            content = workbook_xml.read_text(encoding='utf-8')

            # Find the sheets section and replace with only our target sheet
            sheets_pattern = r'(<sheets>).*?(</sheets>)'

            def replace_sheets(match):
                # Create a single sheet reference with rId1
                return f'<sheets><sheet name="{sheet_title}" sheetId="1" r:id="rId1"/></sheets>'

            content = re.sub(sheets_pattern, replace_sheets, content, flags=re.DOTALL)
            workbook_xml.write_text(content, encoding='utf-8')

        # Update workbook.xml.rels - keep only sheet1 relationship
        wb_rels = temp_path / 'xl' / '_rels' / 'workbook.xml.rels'
        if wb_rels.exists():
            content = wb_rels.read_text(encoding='utf-8')

            # Remove all sheet relationships except rId1 (which should point to sheet1)
            for i in range(2, 10):
                content = re.sub(rf'<Relationship[^>]*sheet{i}\.xml[^>]*/>', '', content)

            # Make sure rId1 points to sheet1.xml
            # First remove any existing sheet1 reference that might have wrong rId
            content = re.sub(r'<Relationship[^>]*Target="worksheets/sheet1\.xml"[^>]*/>', '', content)

            # Add the correct relationship if not present
            if 'worksheets/sheet1.xml' not in content:
                insert_pos = content.find('</Relationships>')
                if insert_pos > 0:
                    new_rel = '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
                    content = content[:insert_pos] + new_rel + content[insert_pos:]

            wb_rels.write_text(content, encoding='utf-8')

        # Update [Content_Types].xml
        content_types = temp_path / '[Content_Types].xml'
        if content_types.exists():
            content = content_types.read_text(encoding='utf-8')
            # Remove overrides for sheets 2-9
            for i in range(2, 10):
                content = re.sub(rf'<Override[^>]*sheet{i}\.xml[^>]*/>', '', content)
            content_types.write_text(content, encoding='utf-8')

    @classmethod
    def _hide_control_columns(cls, sheet_xml: str) -> str:
        """
        Hide control columns (AB onwards) so they don't appear in the document.
        The print area is A1:AA64, columns AB-AJ are for internal calculations only.
        """
        # Find the <cols> section and add hidden="1" to columns AB (28) onwards
        # Excel columns: A=1, B=2, ..., Z=26, AA=27, AB=28, AC=29, ...

        # First, check if there's already a <cols> section
        if '<cols>' in sheet_xml:
            # Add hidden columns after existing cols
            cols_end = sheet_xml.find('</cols>')
            if cols_end > 0:
                # Insert hidden columns before </cols>
                hidden_cols = ''
                for col_num in range(28, 40):  # AB=28 to AM=39 (covers all control columns)
                    hidden_cols += f'<col min="{col_num}" max="{col_num}" hidden="1" />'

                sheet_xml = sheet_xml[:cols_end] + hidden_cols + sheet_xml[cols_end:]
        else:
            # Create a new <cols> section
            # Find where to insert it (after <sheetData> opening or before first <row>)
            worksheet_end = sheet_xml.find('<sheetData')
            if worksheet_end > 0:
                hidden_cols = '<cols>'
                for col_num in range(28, 40):  # AB=28 to AM=39
                    hidden_cols += f'<col min="{col_num}" max="{col_num}" hidden="1" />'
                hidden_cols += '</cols>'

                sheet_xml = sheet_xml[:worksheet_end] + hidden_cols + sheet_xml[worksheet_end:]

        return sheet_xml

    @classmethod
    def _remove_external_links(cls, temp_path: Path) -> None:
        """
        Remove external link references from the workbook.
        """
        # Remove externalLinks folder if exists
        ext_links = temp_path / 'xl' / 'externalLinks'
        if ext_links.exists():
            import shutil
            shutil.rmtree(ext_links)

        # Update workbook.xml.rels to remove external link references
        rels_path = temp_path / 'xl' / '_rels' / 'workbook.xml.rels'
        if rels_path.exists():
            content = rels_path.read_text(encoding='utf-8')
            # Remove external link relationships
            content = re.sub(
                r'<Relationship[^>]*Target="externalLinks[^"]*"[^>]*/>',
                '',
                content
            )
            rels_path.write_text(content, encoding='utf-8')

        # Update workbook.xml to remove externalReferences
        wb_path = temp_path / 'xl' / 'workbook.xml'
        if wb_path.exists():
            content = wb_path.read_text(encoding='utf-8')
            # Remove externalReferences section
            content = re.sub(
                r'<externalReferences>.*?</externalReferences>',
                '',
                content,
                flags=re.DOTALL
            )
            wb_path.write_text(content, encoding='utf-8')

    @classmethod
    def _date_to_excel_serial(cls, d: date) -> int:
        """Convert Python date to Excel serial number."""
        excel_epoch = date(1899, 12, 30)
        if isinstance(d, datetime):
            d = d.date()
        return (d - excel_epoch).days

    @classmethod
    def _format_japanese_date(cls, d: Optional[date]) -> str:
        """Format date in Japanese era format (令和X年X月X日)."""
        if not d:
            return ""

        if isinstance(d, datetime):
            d = d.date()

        reiwa_start = date(2019, 5, 1)
        if d >= reiwa_start:
            year = d.year - 2018
            era = "令和"
        else:
            year = d.year - 1988
            era = "平成"

        return f"{era}{year}年{d.month}月{d.day}日"
