import json
import pandas as pd

# ضع هذا السكريبت في نفس مجلد ملفات Excel الثلاثة ثم شغّله: python build_employees_data.py

# 1. قراءة الملفات الثلاثة
df_orig = pd.read_excel('العاملين بنظام الورديات_٠٩٠٨٥٩.xlsx', header=2)
df_badal = pd.read_excel(
    'نموذج البدل الموحد برقم الساب 2026.xlsx', sheet_name='بدل الراحة', header=None
)
df_hudur = pd.read_excel(
    'كشف حضور عمال انتاج وتحضير البودرة خلال الاسبوع من 6 سبتمبر 2025 الى نهاية'
    ' الاسبوع.xlsx',
    sheet_name='ورقة1',
)

processed = {}

# استيراد ملف الورديات الأساسي
for _, row in df_orig.iterrows():
    c = int(row['رقم الموظف'])
    processed[c] = {
        'id': c,
        'name': str(row['اسم']).strip(),
        'schedule_code': str(row['قواعد جداول العمل']).strip(),
        'schedule_desc': str(row['النص:قواعد جداول العمل']).strip(),
        'org_unit': str(row['اسم الوحدة التنظيمية']).strip(),
        'job_title': str(row['الوظفية ']).strip(),
        'department': str(row['القسم ']).strip(),
        'housing': 'غير مسجل',
        'is_priority': 0,
        'badal': None,
        'shift_tag': '',
    }

# دمج وتحديث سكن عمال إنتاج البودرة
for i in range(8, len(df_hudur)):
    row = df_hudur.iloc[i].tolist()
    code, name, org, job, h_val, s_val = row[1], row[2], row[3], row[4], row[5], row[6]
    if pd.notna(code) and str(code).isdigit():
        c = int(code)
        if c in processed:
            processed[c]['housing'] = str(h_val).strip() if pd.notna(h_val) else 'غير مسجل'
            processed[c]['is_priority'] = 1
            if pd.notna(s_val):
                processed[c]['shift_tag'] = f'وردية {s_val}'

# دمج نموذج البدل الموحد
for i in range(11, 42):
    row = df_badal.iloc[i].tolist()
    code, name, s_val, t_from, t_to, hrs, rsn = (
        row[1], row[2], row[3], row[4], row[5], row[6], row[7]
    )
    if pd.notna(code) and str(code).isdigit():
        c = int(code)
        b_data = {
            'shift': str(s_val).strip() if pd.notna(s_val) else '',
            'work_time': f'من {t_from} إلى {t_to}' if pd.notna(t_from) else 'غير محدد',
            'comp_hours': str(hrs) if pd.notna(hrs) else '',
            'reason': str(rsn).strip() if pd.notna(rsn) else '',
        }
        if c in processed:
            processed[c]['is_priority'] = 1
            processed[c]['badal'] = b_data
        else:  # إضافة الموظفين الجدد
            processed[c] = {
                'id': c,
                'name': str(name).strip(),
                'schedule_code': 'EFF17-19',
                'schedule_desc': 'مطوله الاحد - الاربعاء 1',
                'org_unit': 'الإنتاج',
                'job_title': 'مشغل انتاج',
                'department': 'انتاج وتحضير المنظفات',
                'housing': 'غير مسجل',
                'is_priority': 1,
                'badal': b_data,
                'shift_tag': f'وردية {s_val}',
            }

# تجهيز المصفوفة المضغوطة
compact_list = [
    [
        e['id'], e['name'], e['schedule_code'], e['schedule_desc'], e['org_unit'],
        e['job_title'], e['department'], e['housing'], e['is_priority'],
        [e['badal']['shift'], e['badal']['work_time'], e['badal']['comp_hours'], e['badal']['reason']]
        if e['badal'] else None,
        e['shift_tag'],
    ]
    for e in processed.values()
]

# الحفظ: ملف JS للتضمين المباشر + ملف JSON للاستيراد اليدوي
with open('employees-data.js', 'w', encoding='utf-8') as f:
    f.write('window.EMPLOYEES_RAW_DATA = ' + json.dumps(compact_list, ensure_ascii=False) + ';\n')
with open('employees.json', 'w', encoding='utf-8') as f:
    json.dump(compact_list, f, ensure_ascii=False)

print(f'تم الدمج بنجاح: {len(compact_list)} موظفاً')
print('تم إنشاء: employees-data.js و employees.json')
