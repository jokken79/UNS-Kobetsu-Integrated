"""
人材派遣個別契約書 - Exact PDF Replication Service V2
Generates PDFs that exactly match the reference format from TodaLasCosasDeKobetsu.pdf

This is an improved version with correct table structure matching the reference.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import date
from typing import Dict, Any, List


class JinzaiHakenExactServiceV2:
    """
    Service for generating exact replicas of the reference PDF format.
    Version 2 with improved table structure.
    """

    # Colors - All black for official documents
    TITLE_COLOR = colors.black  # Black for official documents
    BLACK = colors.black

    # Font sizes - Reduced to fit in A4 (90% of page)
    TITLE_SIZE = 10
    BODY_SIZE = 5
    SMALL_SIZE = 4.5

    def __init__(self):
        """Initialize with Japanese TTF fonts."""
        # Use IPA Gothic font for proper Japanese rendering
        pdfmetrics.registerFont(TTFont('IPAGothic', '/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf'))
        pdfmetrics.registerFont(TTFont('IPAMincho', '/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf'))
        self.font = 'IPAGothic'

    def _fmt_date(self, d) -> str:
        """Format date Japanese style."""
        if d is None:
            return ''
        if isinstance(d, date):
            return f"{d.year}年{d.month}月{d.day}日"
        return str(d)

    def generate_page1(self, data: Dict[str, Any]) -> bytes:
        """Generate Page 1: 人材派遣個別契約書"""
        buffer = BytesIO()

        # A4 = 210mm x 297mm, use ~90% = margins of ~10mm each side
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=10*mm,
            leftMargin=10*mm,
            topMargin=10*mm,
            bottomMargin=10*mm
        )

        elements = []
        styles = getSampleStyleSheet()

        # Title style with magenta color
        title_style = ParagraphStyle(
            'Title',
            fontName=self.font,
            fontSize=self.TITLE_SIZE,
            textColor=self.TITLE_COLOR,
            alignment=TA_CENTER,
            spaceAfter=2*mm,
        )

        body_style = ParagraphStyle(
            'Body',
            fontName=self.font,
            fontSize=self.BODY_SIZE,
            alignment=TA_LEFT,
            leading=9,
        )

        # Title
        elements.append(Paragraph('人材派遣個別契約書', title_style))

        # Introduction
        intro = (
            f"{data.get('client_company_name', '')}（以下、「甲」という。）と"
            f"ユニバーサル企画株式会社（以下、「乙」という。）間で締結された労働"
            f"者派遣基本契約書の定めに従い、次の派遣要件に基づき労働者派遣契約を締結する。"
        )
        elements.append(Paragraph(intro, body_style))
        elements.append(Spacer(1, 2*mm))

        # Build main table
        main_table = self._build_main_table(data)
        elements.append(main_table)
        elements.append(Spacer(1, 2*mm))

        # Footer
        elements.append(Paragraph(
            "上記契約の証として本書2通を作成し、甲乙記名押印のうえ、各1通を保有する。",
            body_style
        ))

        contract_date = data.get('contract_date', date.today())
        elements.append(Paragraph(self._fmt_date(contract_date), body_style))
        elements.append(Spacer(1, 2*mm))

        # Signature section
        sig_style = ParagraphStyle('Sig', fontName=self.font, fontSize=self.BODY_SIZE, alignment=TA_RIGHT)
        elements.append(Paragraph('（甲）', ParagraphStyle('SigL', fontName=self.font, fontSize=self.BODY_SIZE)))
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph('（乙）', sig_style))
        elements.append(Paragraph('愛知県名古屋市東区徳川2-18-18', sig_style))
        elements.append(Paragraph('ユニバーサル企画株式会社', sig_style))
        elements.append(Paragraph('代表取締役　中山　雅和', sig_style))
        elements.append(Paragraph('許可番号　派　23-303669', sig_style))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    def _build_main_table(self, data: Dict[str, Any]) -> Table:
        """Build the main contract table matching reference format exactly."""

        # Extract data
        supervisor = data.get('supervisor', {})
        haken_saki_mgr = data.get('haken_saki_manager', {})
        haken_saki_comp = data.get('haken_saki_complaint', {})
        haken_moto_mgr = data.get('haken_moto_manager', {})
        haken_moto_comp = data.get('haken_moto_complaint', {})

        is_kyotei = data.get('is_kyotei_taisho', True)
        has_auth = data.get('has_authority', False)

        # Checkbox helper - use ASCII-compatible markers
        def cb(checked, label=''):
            mark = '■' if checked else '□'
            return f"{mark} {label}"

        # Helper to create vertical text (newlines between characters)
        def vtxt(text):
            # Add newlines between each character for vertical effect
            return '\n'.join(list(text.replace(' ', '')))

        # Column widths: section | label | content...
        # Reference has: 派遣先/元/内容 | field label | name/dept | value | address | value | TEL | number

        # Build rows
        rows = []

        # ===== 派遣先 Section (6 rows) =====
        rows.append([
            vtxt('派遣先'),  # Vertical text using Paragraph
            '派遣先事業所',
            f"名称　{data.get('client_company_name', '')}",
            f"所在地　{data.get('client_address', '')}",
            'TEL',
            data.get('client_tel', '')
        ])

        rows.append([
            '',
            '就業場所',
            f"名称　{data.get('worksite_name', '')}",
            f"所在地　{data.get('worksite_address', '')}",
            'TEL',
            data.get('worksite_tel', '')
        ])

        rows.append([
            '',
            '組織単位',
            data.get('organizational_unit', ''),
            f"抵触日　{self._fmt_date(data.get('conflict_date'))}",
            '',
            ''
        ])

        rows.append([
            '',
            '指揮命令者',
            f"部署　{supervisor.get('department', '')}",
            f"役職　{supervisor.get('position', '')}　{supervisor.get('name', '')}",
            'TEL',
            supervisor.get('phone', '')
        ])

        rows.append([
            '',
            '製造業務専門派遣先責任者',
            f"部署　{haken_saki_mgr.get('department', '')}",
            f"役職　{haken_saki_mgr.get('position', '')}　{haken_saki_mgr.get('name', '')}",
            'TEL',
            haken_saki_mgr.get('phone', '')
        ])

        rows.append([
            '',
            '苦情処理担当者',
            f"部署　{haken_saki_comp.get('department', '')}",
            f"役職　{haken_saki_comp.get('position', '')}　{haken_saki_comp.get('name', '')}",
            'TEL',
            haken_saki_comp.get('phone', '')
        ])

        # ===== 派遣元 Section (2 rows) =====
        rows.append([
            vtxt('派遣元'),
            '製造業務専門派遣元責任者',
            f"部署　{haken_moto_mgr.get('department', '')}",
            f"役職　{haken_moto_mgr.get('position', '')}　{haken_moto_mgr.get('name', '')}",
            'TEL',
            haken_moto_mgr.get('phone', '')
        ])

        rows.append([
            '',
            '苦情処理担当者',
            f"部署　{haken_moto_comp.get('department', '')}",
            f"役職　{haken_moto_comp.get('position', '')}　{haken_moto_comp.get('name', '')}",
            'TEL',
            haken_moto_comp.get('phone', '')
        ])

        # ===== 協定/責任 rows =====
        kyotei_text = f"{cb(is_kyotei, '協定対象派遣労働者に限定')}　　{cb(not is_kyotei, '限定なし')}"
        rows.append([
            '',
            '派遣労働者を協定対象労働者\nに限定するか否か',
            kyotei_text,
            '',
            '',
            ''
        ])

        auth_text = f"{cb(not has_auth, '付与される権限なし')}　　{cb(has_auth, '付与される権限あり')}"
        rows.append([
            '',
            '派遣労働者の責任の程度',
            auth_text,
            '',
            '',
            ''
        ])

        # ===== 派遣内容 Section =====
        rows.append([
            vtxt('派遣内容'),
            '業務内容',
            data.get('work_content', ''),
            '',
            '',
            ''
        ])

        # 派遣期間
        period = f"{self._fmt_date(data.get('dispatch_start_date'))}　～　{self._fmt_date(data.get('dispatch_end_date'))}"
        rows.append([
            '',
            '派遣期間',
            period,
            '',
            '人　数',
            str(data.get('number_of_workers', 1))
        ])

        # 就業日
        work_days = data.get('work_days_text', '月～金（祝日、年末年始、夏季休業を除く。）')
        shift = data.get('shift_pattern', '4勤2休シフト　別紙カレンダーの通り')
        rows.append([
            '',
            '就業日',
            f"{work_days}　{shift}",
            '',
            '',
            ''
        ])

        # 就業時間
        day_shift = data.get('day_shift_time', '昼勤：8時00分～17時00分')
        night_shift = data.get('night_shift_time', '')
        actual = data.get('actual_working_hours', '（実働　7時間40分）')
        time_text = f"{day_shift}　・　{night_shift}{actual}" if night_shift else f"{day_shift}{actual}"
        rows.append([
            '',
            '就業時間',
            time_text,
            '',
            '',
            ''
        ])

        # 休憩時間
        break_day = data.get('break_time_day', '昼勤：10時00～10時15分・12時00分～12時50分・15時00分～15時15分')
        break_night = data.get('break_time_night', '夜勤：22時00～22時15・00時00分～00時50分・03時00分～03時15分')
        rows.append([
            '',
            '休憩時間',
            break_day,
            break_night,
            '',
            ''
        ])

        # 就業日外労働
        rows.append([
            '',
            '就業日外労働',
            data.get('holiday_work_rule', '1ヶ月に2日の範囲内で命ずることができる。'),
            '',
            '',
            ''
        ])

        # 時間外労働
        ot = data.get('overtime_rules',
            '5時間/日、45時間/月、360時間/年迄とする。但し、特別条項の申請により、6時間/日、80時間/月、720時間/年迄延長できる。申請は6回/年迄とする。')
        rows.append([
            '',
            '時間外労働',
            ot,
            '',
            '',
            ''
        ])

        # 派遣料金
        basic = data.get('hourly_rate', 1700)
        ot_rate = data.get('overtime_rate', 2125)
        night_rate = data.get('night_shift_rate', 2125)
        holiday = data.get('holiday_rate', 2295)
        premium = data.get('premium_rate', 2550)
        rate_text = (
            f"基本 ¥{basic:,}　　残業(1.25%) ¥{ot_rate:,}　　深夜(1.25%) ¥{night_rate:,}\n"
            f"休日(1.35%) ¥{holiday:,}　　<60時間超> 割増料金(1.5%) ¥{premium:,}\n"
            f"労働時間の計算は　5分単位で計算する。"
        )
        rows.append([
            '',
            '派遣料金',
            rate_text,
            '',
            '',
            ''
        ])

        # 支払い条件
        payment_text = (
            f"締日　{data.get('closing_day', '20日')}　　支払日　{data.get('payment_day', '翌月20日')}　　"
            f"支払方法　{data.get('payment_method', '銀行振込')}\n"
            f"{data.get('bank_info', '振込先　愛知銀行　お知支店　普通2075479　名義人　ユニバーサル企画（株）')}"
        )
        rows.append([
            '',
            '支払い条件',
            payment_text,
            '',
            '',
            ''
        ])

        # 安全・衛生
        safety = data.get('safety_measures',
            '派遣先及び派遣元事業主は、労働者派遣法第44条から第47条の2までの規定により課された各法令を遵守し、自己に課された法令上の責任を負う。なお、派遣就業中の安全及び衛生については、派遣先の安全衛生に関する規定を順守することとし、その他については、派遣元の安全衛生に関する規定を適用する。')
        rows.append([
            '',
            '安全・衛生',
            safety,
            '',
            '',
            ''
        ])

        # 便宜供与
        convenience = data.get('convenience_provisions',
            '派遣先は、派遣労働者に対して利用の機会を与える給食施設、休憩室、及び更衣室については、本契約に基づく派遣労働者に係る派遣労働者に対しても、利用の機会を与えるよう配慮しなければならないこととする。')
        rows.append([
            '',
            '便宜供与',
            convenience,
            '',
            '',
            ''
        ])

        # 苦情処理方法
        complaint = data.get('complaint_method',
            '(1)派遣元事業主における苦情処理担当者が苦情の申し出を受けたときは、ただちに製造業務専門派遣元責任者へ連絡することとし、当該派遣元責任者が中心となって、誠意をもって、遅滞なく、当該苦情の適切かつ迅速な処理を図ることとし、その結果について必ず派遣労働者に通知することとする。\n'
            '(2)派遣先における苦情処理担当者が苦情の申し出を受けたときは、ただちに製造業務専門派遣先責任者へ連絡することとし、当該派遣先責任者が中心となって、誠意をもって、遅滞なく、当該苦情の適切かつ迅速な処理を図ることとし、その結果については必ず派遣労働者に通知することとする。\n'
            '(3)派遣先及び派遣元事業主は、自らでその解決が容易であり、即日に処理した苦情の他は、相互に遅滞なく通知するとともに、密接に連絡調整を行いつつ、その解決を図ることとする。')
        rows.append([
            '',
            '苦情処理方法',
            complaint,
            '',
            '',
            ''
        ])

        # 労働者派遣契約の解除...
        termination = data.get('termination_measures',
            '(1)労働者派遣契約の解除の事前申し入れ　派遣先は、専ら派遣先に起因する事由により、労働者派遣契約の契約期間が満了する前の解除を行おうとする場合には、派遣元の合意を得ることはもとより、あらかじめ相当の猶予期間をもって派遣元に解除の申し入れを行うこととする。\n'
            '(2)就業機会の確保派遣元事業主及び派遣先は、労働者派遣契約の契約期間が満了する前に派遣労働者の責に帰すべき事由によらない労働者派遣契約の解除を行った場合には、派遣先の関連会社での就業をあっせんする等により、当該労働者派遣契約に係る派遣労働者の新たな就業機会の確保を図ることとする。\n'
            '(3)損害賠償等に係る適切な措置派遣先は、派遣先の責に帰すべき事由により労働者派遣契約の契約期間が満了する前に労働者派遣契約の解除を行おうとする場合には、派遣労働者の新たな就業機会の確保を図ることとし、これができないときは、少なくとも当該労働者派遣契約の解除に伴い派遣元が当該労働者派遣契約に係る派遣労働者を休業させること等を余儀なくされたことにより生じた損害の賠償を行わなければならないこととする。\n'
            '(4)労働者派遣契約の解除の理由の明示　派遣先は、労働者派遣契約の契約期間が満了する前に労働者派遣契約の解除を行おうとする場合であって派遣元事業主から請求があったときは、労働者派遣契約の解除を行った理由を派遣元事業主に対して明らかにすることとする。')
        rows.append([
            '',
            '労働者派遣契約の解除に当たって講ずる派遣労働者の雇用の安定を図るための措置',
            termination,
            '',
            '',
            ''
        ])

        # 派遣先が派遣労働者を雇用する場合...
        direct_hire = data.get('direct_hire_prevention',
            '派遣先が派遣終了後に、当該派遣労働者を雇用する場合、その雇用意思を事前に派遣元へ示すこととする。')
        rows.append([
            '',
            '派遣先が派遣労働者を雇用する場合の紛争防止措置',
            direct_hire,
            '',
            '',
            ''
        ])

        # 派遣労働者を無期雇用...
        mukeiko = data.get('mukeiko_60_limit', '無期雇用又は60歳以上に限定しない。')
        rows.append([
            '',
            '派遣労働者を無期雇用派遣労働者又は60歳以上の者に限定するか否かの別',
            mukeiko,
            '',
            '',
            ''
        ])

        # Create table with specific column widths
        # Total width ~190mm (A4=210mm - 10mm margins each side)
        # Reduced widths to fit content properly
        col_widths = [10*mm, 35*mm, 52*mm, 52*mm, 10*mm, 18*mm]

        table = Table(rows, colWidths=col_widths)

        # Apply styles
        style_commands = [
            # Font
            ('FONTNAME', (0, 0), (-1, -1), self.font),
            ('FONTSIZE', (0, 0), (-1, -1), self.BODY_SIZE),

            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, self.BLACK),

            # Alignment - default TOP for content
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Section column centered

            # Section header column - MIDDLE alignment for vertical text
            ('VALIGN', (0, 0), (0, 5), 'MIDDLE'),   # 派遣先
            ('VALIGN', (0, 6), (0, 9), 'MIDDLE'),   # 派遣元
            ('VALIGN', (0, 10), (0, 24), 'MIDDLE'), # 派遣内容

            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),

            # Merge section cells (派遣先 rows 0-5)
            ('SPAN', (0, 0), (0, 5)),
            # Merge 派遣元 rows 6-9
            ('SPAN', (0, 6), (0, 9)),
            # Merge 派遣内容 rows 10-24 (last row is 24, 0-indexed)
            ('SPAN', (0, 10), (0, 24)),

            # Merge content cells for wide rows
            ('SPAN', (2, 8), (5, 8)),   # 協定対象
            ('SPAN', (2, 9), (5, 9)),   # 責任の程度
            ('SPAN', (2, 10), (5, 10)), # 業務内容
            ('SPAN', (2, 12), (5, 12)), # 就業日
            ('SPAN', (2, 13), (5, 13)), # 就業時間
            ('SPAN', (2, 15), (5, 15)), # 就業日外労働
            ('SPAN', (2, 16), (5, 16)), # 時間外労働
            ('SPAN', (2, 17), (5, 17)), # 派遣料金
            ('SPAN', (2, 18), (5, 18)), # 支払い条件
            ('SPAN', (2, 19), (5, 19)), # 安全・衛生
            ('SPAN', (2, 20), (5, 20)), # 便宜供与
            ('SPAN', (2, 21), (5, 21)), # 苦情処理
            ('SPAN', (2, 22), (5, 22)), # 解除措置
            ('SPAN', (2, 23), (5, 23)), # 紛争防止
            ('SPAN', (2, 24), (5, 24)), # 無期/60歳
        ]

        table.setStyle(TableStyle(style_commands))

        return table


# Test data
SAMPLE_DATA = {
    'client_company_name': '高雄工業株式会社',
    'client_address': '愛知県弥富市楠三丁目13番地2',
    'client_tel': '',
    'worksite_name': '高雄工業株式会社 岡山工場',
    'worksite_address': '岡山県岡山市北区御津伊田1028-19',
    'worksite_tel': '',
    'organizational_unit': '製造部',
    'conflict_date': date(2027, 10, 1),

    'supervisor': {
        'department': '製造部',
        'position': '部長',
        'name': '景森 敦士',
        'phone': '',
    },
    'haken_saki_manager': {
        'department': '製造部',
        'position': '部長',
        'name': '景森 敦士',
        'phone': '086-724-3939',
    },
    'haken_saki_complaint': {
        'department': '総務部',
        'position': '課長',
        'name': '山田 太郎',
        'phone': '086-724-3939',
    },
    'haken_moto_manager': {
        'department': '営業部',
        'position': '取締役 部長',
        'name': '中山 欣英',
        'phone': '052-938-8840',
    },
    'haken_moto_complaint': {
        'department': '営業部',
        'position': '取締役 部長',
        'name': '中山 欣英',
        'phone': '052-938-8840',
    },

    'is_kyotei_taisho': True,
    'has_authority': False,
    'work_content': '自動車部品製造業務及びその付随業務',
    'dispatch_start_date': date(2024, 10, 1),
    'dispatch_end_date': date(2024, 12, 31),
    'number_of_workers': 6,
    'contract_date': date(2024, 9, 1),

    'work_days_text': '月～金（祝日、年末年始、夏季休業を除く。）',
    'shift_pattern': '4勤2休シフト　別紙カレンダーの通り',
    'day_shift_time': '昼勤：08時00分～17時00分',
    'night_shift_time': '',
    'actual_working_hours': '（実働 7時間40分）',
    'break_time_day': '昼勤：10時00～10時15分・12時00分～12時50分・15時00分～15時15分',
    'break_time_night': '夜勤：22時00～22時15・00時00分～00時50分・03時00分～03時15分',

    'hourly_rate': 1300,
    'overtime_rate': 1625,
    'night_shift_rate': 1625,
    'holiday_rate': 1755,
    'premium_rate': 1950,

    'closing_day': '20日',
    'payment_day': '翌月20日',
    'payment_method': '銀行振込',
    'bank_info': '愛知銀行　お知支店　普通2075479　名義人　ユニバーサル企画（株）',
}


if __name__ == '__main__':
    service = JinzaiHakenExactServiceV2()
    pdf_bytes = service.generate_page1(SAMPLE_DATA)

    with open('/app/outputs/test_v2.pdf', 'wb') as f:
        f.write(pdf_bytes)
    print(f'Generated PDF: {len(pdf_bytes)} bytes')
