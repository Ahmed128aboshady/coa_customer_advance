# COA Customer Advance Payments (`coa_customer_advance`)

## 📌 الوصف العام (Overview)
دفعات مقدمة من العملاء في حساب التزام مستقل مع تسوية تلقائية ودعم مسار Down Payment من أمر البيع

### التفاصيل الوظيفية:

COA Customer Advance Payments
=============================
مساران للدفعة المقدمة:

1. Payment مباشر (Accounting → Payments) مع خيار "Customer Advance":
   القيد: من ح/ البنك إلى ح/ دفعات مقدمة (Liability) — وليس AR.

2. من أمر البيع (Create Invoice → "Down payment (cash / bank)"):
   يفتح نفس الشاشة لكن يسجّل Payment نقدي بقيد بنك/التزام بدل فاتورة،
   ويربطه بأمر البيع، ويظهر كـ Outstanding Credit للتسوية مع الفاتورة.

3. تسوية تدريجية عبر زر "تسوية دفعة مقدمة" على الفاتورة:
   القيد: من ح/ دفعات مقدمة (Liability) إلى ح/ العملاء (AR) + reconcile.

الدفعات في حساب التزام مستقل، فهي مستبعدة تلقائياً من إجمالي الإيراد.
    

---

## 🛠️ معلومات الموديول (Module Metadata)
- **الاسم الفني (Technical Name):** `coa_customer_advance`
- **التصنيف (Category):** `Accounting/Accounting`
- **الإصدار (Version):** `19.0.1.1.0`
- **الاعتماديات (Dependencies):** `account`, `sale_management`

---

## 📦 النماذج البرمجية (Models & Backend)
- **الملف:** `models\account_move.py`
  - **النماذج المعدلة (`_inherit`):** `account.move`
- **الملف:** `models\account_payment.py`
  - **النماذج المعدلة (`_inherit`):** `account.payment`
- **الملف:** `models\res_config_settings.py`
  - **النماذج المعدلة (`_inherit`):** `res.company`, `res.config.settings`
- **الملف:** `models\sale_advance_payment_inv.py`
  - **النماذج المعدلة (`_inherit`):** `sale.advance.payment.inv`
- **الملف:** `models\sale_order.py`
  - **النماذج المعدلة (`_inherit`):** `sale.order`

---

## 🖥️ الواجهات والتقارير (Views & Reports)
- **ملفات الواجهات (`Views`):** `views\account_move_views.xml`, `views\account_payment_views.xml`, `views\res_config_settings_views.xml`, `views\sale_advance_payment_inv_views.xml`, `views\sale_order_views.xml`, `wizard\advance_settle_wizard_views.xml`

---

## 🚀 كيفية الاستخدام والتثبيت (Installation & Usage)
1. قُم بإضافة مجلد الموديول إلى مسار `addons_path` الخاص بالسيرفر.
2. قُم بتحديث قائمة الموديولات في أودو (Update Apps List).
3. البحث عن `COA Customer Advance Payments` أو `coa_customer_advance` والضغط على **تثبيت (Install)**.
