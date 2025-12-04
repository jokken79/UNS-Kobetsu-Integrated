"""Generate test documents using KobetsuExcelGenerator."""
from app.services.kobetsu_excel_generator import KobetsuExcelGenerator

# Datos de prueba
test_data = {
    'client_company_name': 'TEST COMPANY株式会社',
    'factory_name': 'Test Factory',
    'organizational_unit': 'Test Department',
    'line': 'Test Line',
    'hourly_rate': 1500,
    'dispatch_start_date': '2025-01-01',
    'dispatch_end_date': '2025-12-31',
    'work_content': 'テスト作業',
}

print('Generando documentos con fix de definedNames...')

# 1. Kobetsu
data = KobetsuExcelGenerator.generate(test_data)
with open('/tmp/01_個別契約書.xlsx', 'wb') as f:
    f.write(data)
print(f'1. 個別契約書: OK - {len(data)} bytes')

# 2. Tsuchisho
data = KobetsuExcelGenerator.generate_tsuchisho(test_data)
with open('/tmp/02_通知書.xlsx', 'wb') as f:
    f.write(data)
print(f'2. 通知書: OK - {len(data)} bytes')

# 3. DAICHO
data = KobetsuExcelGenerator.generate_daicho(test_data)
with open('/tmp/03_DAICHO.xlsx', 'wb') as f:
    f.write(data)
print(f'3. DAICHO: OK - {len(data)} bytes')

# 4. Hakenmoto
data = KobetsuExcelGenerator.generate_hakenmoto_daicho(test_data)
with open('/tmp/04_派遣元管理台帳.xlsx', 'wb') as f:
    f.write(data)
print(f'4. 派遣元管理台帳: OK - {len(data)} bytes')

# 5. Shugyo Joken
data = KobetsuExcelGenerator.generate_shugyo_joken(test_data)
with open('/tmp/05_就業条件明示書.xlsx', 'wb') as f:
    f.write(data)
print(f'5. 就業条件明示書: OK - {len(data)} bytes')

# 6. Keiyakusho
data = KobetsuExcelGenerator.generate_keiyakusho(test_data)
with open('/tmp/06_契約書.xlsx', 'wb') as f:
    f.write(data)
print(f'6. 契約書: OK - {len(data)} bytes')

print()
print('TODOS LOS DOCUMENTOS GENERADOS!')
