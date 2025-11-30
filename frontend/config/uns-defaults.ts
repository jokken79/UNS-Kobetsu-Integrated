/**
 * UNS企画 デフォルト設定
 *
 * このファイルでUNS企画の連絡先情報を設定してください。
 * 新規契約書作成時に自動的に入力されます。
 *
 * ================================
 * 設定方法:
 * 1. [要設定] の部分を実際の値に置き換えてください
 * 2. 電話番号は XXX-XXXX-XXXX 形式で入力してください
 * ================================
 */

// 会社基本情報
export const UNS_COMPANY = {
  name: '株式会社UNS企画',
  license_number: '派13-123456',  // 派遣事業許可番号
  address: '[要設定] 会社住所',
  phone: '052-XXX-XXXX',
}

// 派遣元苦情処理担当者 (労働者派遣法第26条第1項第9号)
// ⚠️ 本番環境では実際の値に置き換えてください
export const HAKEN_MOTO_COMPLAINT_CONTACT = {
  department: '管理部',
  position: '部長',
  name: '中山　欣英',
  phone: '052-938-8840',
}

// 派遣元責任者 (労働者派遣法第36条)
// ⚠️ 本番環境では実際の値に置き換えてください
export const HAKEN_MOTO_MANAGER = {
  department: '派遣事業部',
  position: '部長',
  name: '中山　欣英',
  phone: '052-938-8840',
  license_number: '',                  // 派遣元責任者講習修了証番号 (任意)
}

// デフォルト就業条件
export const DEFAULT_WORK_CONDITIONS = {
  work_days: ['月', '火', '水', '木', '金'],
  work_start_time: '08:00',
  work_end_time: '17:00',
  break_time_minutes: 60,
  hourly_rate: 1500,
  overtime_rate: 1875,
  responsibility_level: '通常業務',
}
