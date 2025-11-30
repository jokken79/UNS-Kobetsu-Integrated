#!/usr/bin/env python3
"""
Generate Contract PDF - 個別契約書 (Individual Dispatch Contract)

Generates a professional PDF contract for labor dispatch workers
complying with 労働者派遣法第26条 (Dispatch Workers Law Article 26).

Usage:
    python3 generate_contract_pdf.py
"""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from datetime import datetime
import os

# ============================================================
# CONTRACT DATA - 高雄工業 本社工場 (Kaohsiung)
# ============================================================

CONTRACT_DATA = {
    "contract_number": "KOB-202504-0001",
    "contract_date": "2025年4月10日",
    "dispatch_start_date": "2025年4月15日",
    "dispatch_end_date": "2025年9月30日",

    # Company Info (派遣元 - Dispatch Source)
    "dispatch_company": "株式会社UNS企画",
    "dispatch_company_address": "愛知県春日井市○○町1-2-3",
    "dispatch_company_phone": "0568-00-0000",
    "dispatch_responsible": {
        "department": "営業部",
        "position": "取締役",
        "name": "ブウ ティ サウ",
        "phone": "052-938-8840"
    },

    # Client Company Info (派遣先 - Dispatch Destination)
    "client_company": "高雄工業株式会社",
    "client_company_address": "愛知県弥富市楠三丁目13番地2",
    "client_company_phone": "0567-68-8110",
    "client_responsible": {
        "department": "愛知事業所",
        "position": "部長",
        "name": "安藤 忍",
        "phone": "0567-68-8110"
    },

    # Work Details (業務内容)
    "worksite_name": "高雄工業株式会社 本社工場",
    "worksite_address": "愛知県弥富市楠三丁目13番地2",
    "work_content": "鋳造材料の工場内加工ラインへの供給作業。リフトを操作して材料を運搬し、各加工ラインへ供給。在庫管理を含む。",
    "responsibility_level": "通常業務",
    "organizational_unit": "製作部",

    # Supervisor (指揮命令者)
    "supervisor": {
        "department": "第一営業部本社営業課",
        "position": "係長",
        "name": "坂上 舞",
        "phone": "0567-68-8110"
    },

    # Work Schedule (就業条件)
    "work_days": "月曜日～金曜日",
    "day_shift": "07時00分～15時30分",
    "night_shift": "19時00分～03時30分",
    "break_time": "45分",
    "holidays": "土曜日・日曜日・年末年始(12月29日～1月5日)・GW(4月27日～5月4日)・夏季休暇(8月10日～8月17日)",

    # Compensation (給与条件)
    "hourly_rate": "1,750",
    "overtime_rate": "2,187.50",
    "night_shift_rate": "2,100",
    "holiday_rate": "2,625",
    "time_unit": "15分単位",

    # Overtime (時間外労働)
    "overtime_max_day": "3時間/日",
    "overtime_max_month": "42時間/月",
    "overtime_max_year": "320時間/年",
    "overtime_special": "特別条項申請時：80時間/月、720時間/年迄延長可能（年6回迄）",

    # Non-working day labor (休日労働)
    "holiday_work": "1ヶ月に2日の範囲内で命ずることができる。",

    # Safety (安全衛生)
    "safety_measures": "派遣先の安全衛生規程に従い、必要な保護具を着用すること。作業中の負傷、事故発生時は即座に報告すること。",

    # Complaint Contacts (苦情処理)
    "complaint_haken_moto": {
        "department": "営業部",
        "position": "取締役部長",
        "name": "中山 欣英",
        "phone": "052-938-8840"
    },
    "complaint_haken_saki": {
        "department": "人事広報管理部",
        "position": "部長",
        "name": "山田 茂",
        "phone": "0567-68-8110"
    },

    # Managers (責任者)
    "manager_haken_moto": {
        "department": "営業部",
        "position": "取締役",
        "name": "ブウ ティ サウ",
        "license": "派23-123456",
        "phone": "052-938-8840"
    },
    "manager_haken_saki": {
        "department": "愛知事業所",
        "position": "部長",
        "name": "安藤 忍",
        "license": "愛-001",
        "phone": "0567-68-8110"
    },

    # Employee Info
    "employee_number": "EMP0847",
    "employee_name": "グエン ティ タン",
    "nationality": "ベトナム",
    "date_of_birth": "1995年6月20日",
    "gender": "男性",

    # Welfare (福利厚生)
    "welfare": "食堂、更衣室、休憩室、駐車場",

    # Termination (解除時の措置)
    "termination_measures": "30日前までに書面にて通知。派遣労働者の雇用安定に努める。",

    # Special Items
    "is_kyotei_taisho": "該当（労使協定方式対象）",
    "is_direct_hire_prevention": "該当",
    "number_of_workers": "1名"
}


def create_contract_pdf(output_path="/app/outputs/KOB-202504-0001.pdf"):
    """Generate contract PDF."""

    # Create outputs directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Create PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=10*mm,
        bottomMargin=10*mm
    )

    # Container for elements
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#333333'),
        spaceAfter=6,
        alignment=1,  # Center
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.HexColor('#000000'),
        spaceAfter=3,
        spaceBefore=6,
        fontName='Helvetica-Bold',
        borderPadding=5,
        backColor=colors.HexColor('#f0f0f0')
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        alignment=0
    )

    # ============================================================
    # TITLE & HEADER
    # ============================================================

    elements.append(Paragraph("個別労働者派遣契約書", title_style))
    elements.append(Spacer(1, 6))

    # Contract info table
    header_data = [
        ["契約番号", CONTRACT_DATA["contract_number"], "契約締結日", CONTRACT_DATA["contract_date"]],
        ["派遣開始日", CONTRACT_DATA["dispatch_start_date"], "派遣終了日", CONTRACT_DATA["dispatch_end_date"]]
    ]

    header_table = Table(header_data, colWidths=[25*mm, 40*mm, 25*mm, 40*mm])
    header_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8))

    # ============================================================
    # SECTION 1: 派遣元・派遣先情報 (Dispatch Companies)
    # ============================================================

    elements.append(Paragraph("1. 派遣元および派遣先の情報", heading_style))

    company_data = [
        ["項目", "派遣元（労働者派遣事業者）", "派遣先（受け入れ企業）"],
        ["会社名", CONTRACT_DATA["dispatch_company"], CONTRACT_DATA["client_company"]],
        ["所在地", CONTRACT_DATA["dispatch_company_address"], CONTRACT_DATA["client_company_address"]],
        ["電話番号", CONTRACT_DATA["dispatch_company_phone"], CONTRACT_DATA["client_company_phone"]],
        ["責任者\n部署・役職・氏名",
         f"{CONTRACT_DATA['dispatch_responsible']['department']}\n{CONTRACT_DATA['dispatch_responsible']['position']} {CONTRACT_DATA['dispatch_responsible']['name']}",
         f"{CONTRACT_DATA['client_responsible']['department']}\n{CONTRACT_DATA['client_responsible']['position']} {CONTRACT_DATA['client_responsible']['name']}"
        ]
    ]

    company_table = Table(company_data, colWidths=[20*mm, 60*mm, 60*mm])
    company_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#cccccc')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(company_table)
    elements.append(Spacer(1, 6))

    # ============================================================
    # SECTION 2: 業務内容 (Work Content - Item 1)
    # ============================================================

    elements.append(Paragraph("2. 業務内容（第26条第1号）", heading_style))

    elements.append(Paragraph("■派遣先事業所：", normal_style))
    elements.append(Paragraph(f"　{CONTRACT_DATA['worksite_name']}", normal_style))
    elements.append(Paragraph(f"　{CONTRACT_DATA['worksite_address']}", normal_style))
    elements.append(Spacer(1, 3))

    elements.append(Paragraph("■業務内容：", normal_style))
    elements.append(Paragraph(f"　{CONTRACT_DATA['work_content']}", normal_style))
    elements.append(Spacer(1, 3))

    elements.append(Paragraph("■責任の程度（第26条第2号）：", normal_style))
    elements.append(Paragraph(f"　{CONTRACT_DATA['responsibility_level']}", normal_style))
    elements.append(Spacer(1, 6))

    # ============================================================
    # SECTION 3: 指揮命令者 (Supervisor - Item 4)
    # ============================================================

    elements.append(Paragraph("3. 指揮命令者（第26条第4号）", heading_style))

    supervisor_data = [
        ["部署", CONTRACT_DATA["supervisor"]["department"]],
        ["役職", CONTRACT_DATA["supervisor"]["position"]],
        ["氏名", CONTRACT_DATA["supervisor"]["name"]],
        ["電話", CONTRACT_DATA["supervisor"]["phone"]]
    ]

    supervisor_table = Table(supervisor_data, colWidths=[25*mm, 75*mm])
    supervisor_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(supervisor_table)
    elements.append(Spacer(1, 6))

    # ============================================================
    # SECTION 4: 就業条件 (Employment Conditions - Items 5-6)
    # ============================================================

    elements.append(Paragraph("4. 就業条件（第26条第5号・6号）", heading_style))

    work_condition_data = [
        ["項目", "内容"],
        ["勤務日", CONTRACT_DATA["work_days"]],
        ["勤務時間\n昼勤", CONTRACT_DATA["day_shift"]],
        ["勤務時間\n夜勤", CONTRACT_DATA["night_shift"]],
        ["休憩時間", CONTRACT_DATA["break_time"]],
        ["休日", CONTRACT_DATA["holidays"]]
    ]

    work_table = Table(work_condition_data, colWidths=[25*mm, 75*mm])
    work_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#cccccc')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(work_table)
    elements.append(Spacer(1, 6))

    # ============================================================
    # SECTION 5: 給与条件 (Compensation)
    # ============================================================

    elements.append(Paragraph("5. 給与条件", heading_style))

    salary_data = [
        ["給与種別", "金額（円）"],
        ["基本時給", CONTRACT_DATA["hourly_rate"]],
        ["時間外単価", CONTRACT_DATA["overtime_rate"]],
        ["深夜単価", CONTRACT_DATA["night_shift_rate"]],
        ["休日単価", CONTRACT_DATA["holiday_rate"]],
        ["時間単位", CONTRACT_DATA["time_unit"]]
    ]

    salary_table = Table(salary_data, colWidths=[40*mm, 40*mm])
    salary_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#cccccc')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(salary_table)
    elements.append(Spacer(1, 6))

    # ============================================================
    # SECTION 6: 時間外労働 (Overtime - Item 12)
    # ============================================================

    elements.append(Paragraph("6. 時間外労働（第26条第12号）", heading_style))

    elements.append(Paragraph("■通常時：", normal_style))
    elements.append(Paragraph(f"　{CONTRACT_DATA['overtime_max_day']}", normal_style))
    elements.append(Paragraph(f"　{CONTRACT_DATA['overtime_max_month']}", normal_style))
    elements.append(Paragraph(f"　{CONTRACT_DATA['overtime_max_year']}", normal_style))
    elements.append(Spacer(1, 3))

    elements.append(Paragraph("■特別条項：", normal_style))
    elements.append(Paragraph(f"　{CONTRACT_DATA['overtime_special']}", normal_style))
    elements.append(Spacer(1, 6))

    # ============================================================
    # SECTION 7: 安全衛生 (Safety - Item 7)
    # ============================================================

    elements.append(Paragraph("7. 安全衛生（第26条第7号）", heading_style))
    elements.append(Paragraph(f"　{CONTRACT_DATA['safety_measures']}", normal_style))
    elements.append(Spacer(1, 6))

    # ============================================================
    # SECTION 8: 苦情処理 (Complaint Handling - Item 8)
    # ============================================================

    elements.append(Paragraph("8. 苦情処理（第26条第8号）", heading_style))

    complaint_data = [
        ["派遣元での苦情処理窓口", "派遣先での苦情処理窓口"],
        [f"部署: {CONTRACT_DATA['complaint_haken_moto']['department']}\n役職: {CONTRACT_DATA['complaint_haken_moto']['position']}\n氏名: {CONTRACT_DATA['complaint_haken_moto']['name']}\nTEL: {CONTRACT_DATA['complaint_haken_moto']['phone']}",
         f"部署: {CONTRACT_DATA['complaint_haken_saki']['department']}\n役職: {CONTRACT_DATA['complaint_haken_saki']['position']}\n氏名: {CONTRACT_DATA['complaint_haken_saki']['name']}\nTEL: {CONTRACT_DATA['complaint_haken_saki']['phone']}"]
    ]

    complaint_table = Table(complaint_data, colWidths=[50*mm, 50*mm])
    complaint_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#cccccc')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(complaint_table)
    elements.append(Spacer(1, 6))

    # ============================================================
    # PAGE BREAK
    # ============================================================

    elements.append(PageBreak())

    # ============================================================
    # SECTION 9: 福利厚生 (Welfare - Item 13)
    # ============================================================

    elements.append(Paragraph("9. 福利厚生（第26条第13号）", heading_style))
    elements.append(Paragraph(f"　施設利用: {CONTRACT_DATA['welfare']}", normal_style))
    elements.append(Spacer(1, 6))

    # ============================================================
    # SECTION 10: 契約解除時の措置 (Termination - Item 9)
    # ============================================================

    elements.append(Paragraph("10. 契約解除時の措置（第26条第9号）", heading_style))
    elements.append(Paragraph(f"　{CONTRACT_DATA['termination_measures']}", normal_style))
    elements.append(Spacer(1, 6))

    # ============================================================
    # SECTION 11: 責任者 (Managers - Items 10-11)
    # ============================================================

    elements.append(Paragraph("11. 派遣元・派遣先の責任者（第26条第10号・11号）", heading_style))

    manager_data = [
        ["区分", "部署・役職", "氏名", "免許番号", "電話"],
        ["派遣元\n責任者",
         f"{CONTRACT_DATA['manager_haken_moto']['department']}\n{CONTRACT_DATA['manager_haken_moto']['position']}",
         CONTRACT_DATA['manager_haken_moto']['name'],
         CONTRACT_DATA['manager_haken_moto']['license'],
         CONTRACT_DATA['manager_haken_moto']['phone']],
        ["派遣先\n責任者",
         f"{CONTRACT_DATA['manager_haken_saki']['department']}\n{CONTRACT_DATA['manager_haken_saki']['position']}",
         CONTRACT_DATA['manager_haken_saki']['name'],
         CONTRACT_DATA['manager_haken_saki']['license'],
         CONTRACT_DATA['manager_haken_saki']['phone']]
    ]

    manager_table = Table(manager_data, colWidths=[15*mm, 30*mm, 15*mm, 15*mm, 20*mm])
    manager_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#cccccc')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(manager_table)
    elements.append(Spacer(1, 6))

    # ============================================================
    # SECTION 12: 特別条項 (Special Items - 14-16)
    # ============================================================

    elements.append(Paragraph("12. 特別条項（第26条第14号・15号・16号）", heading_style))

    special_data = [
        ["項目", "該当"],
        ["労使協定方式対象（Item 15）", CONTRACT_DATA["is_kyotei_taisho"]],
        ["直接雇用化防止措置（Item 14）", CONTRACT_DATA["is_direct_hire_prevention"]]
    ]

    special_table = Table(special_data, colWidths=[50*mm, 50*mm])
    special_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#cccccc')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(special_table)
    elements.append(Spacer(1, 6))

    # ============================================================
    # SECTION 13: 労働者情報 (Worker Information)
    # ============================================================

    elements.append(Paragraph("13. 派遣労働者情報", heading_style))

    worker_data = [
        ["項目", "内容"],
        ["社員番号", CONTRACT_DATA["employee_number"]],
        ["氏名", CONTRACT_DATA["employee_name"]],
        ["生年月日", CONTRACT_DATA["date_of_birth"]],
        ["性別", CONTRACT_DATA["gender"]],
        ["国籍", CONTRACT_DATA["nationality"]],
        ["派遣人数", CONTRACT_DATA["number_of_workers"]]
    ]

    worker_table = Table(worker_data, colWidths=[25*mm, 75*mm])
    worker_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#cccccc')),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(worker_table)
    elements.append(Spacer(1, 12))

    # ============================================================
    # SIGNATURES
    # ============================================================

    elements.append(Paragraph("契約の承認・署名", heading_style))
    elements.append(Spacer(1, 6))

    signature_data = [
        ["派遣元（労働者派遣事業者）", "派遣先（受け入れ企業）"],
        ["\n\n代表者氏名: ___________________\n\n\n署名日: 令和 ___年 ___月 ___日",
         "\n\n代表者氏名: ___________________\n\n\n署名日: 令和 ___年 ___月 ___日"],
        ["派遣労働者", ""],
        ["氏名: ___________________\n\n\n署名日: 令和 ___年 ___月 ___日", ""]
    ]

    sig_table = Table(signature_data, colWidths=[50*mm, 50*mm])
    sig_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 1), colors.HexColor('#f0f0f0')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(sig_table)
    elements.append(Spacer(1, 12))

    # Footer
    elements.append(Paragraph("本契約書は、労働者派遣法第26条に基づく個別労働者派遣契約書です。", normal_style))

    # Build PDF
    doc.build(elements)
    print(f"✅ PDF generated successfully: {output_path}")


if __name__ == "__main__":
    create_contract_pdf()
