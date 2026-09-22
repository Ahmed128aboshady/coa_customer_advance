# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    # خيار جديد في نفس شاشة Create Invoice: دفعة نقدية (قيد بنك/التزام)
    advance_payment_method = fields.Selection(
        selection_add=[('cash_advance', 'Down payment (cash / bank)')],
        ondelete={'cash_advance': 'cascade'},
    )
    cash_advance_type = fields.Selection(
        [('percentage', 'Percentage'), ('fixed', 'Fixed Amount')],
        string='Cash Advance Type', default='percentage',
    )
    # حقول مبلغ خاصة بالموديول (مستقلة عن حقول الـ wizard القياسية المخفية)
    cash_advance_percentage = fields.Float(
        string='Down Payment %',
        help="النسبة المئوية من إجمالي أمر البيع (شامل الضريبة).",
    )
    cash_advance_fixed = fields.Monetary(
        string='Down Payment Amount',
        currency_field='cash_advance_currency_id',
        help="قيمة الدفعة المقدمة كمبلغ ثابت.",
    )
    cash_advance_currency_id = fields.Many2one(
        'res.currency', string='Currency',
        compute='_compute_cash_advance_currency', store=False,
    )
    advance_journal_id = fields.Many2one(
        'account.journal',
        string='Payment Journal',
        domain="[('type', 'in', ('bank', 'cash'))]",
        help="دفتر يومية البنك/الخزينة الذي ستُحصَّل فيه الدفعة المقدمة.",
    )
    advance_payment_date = fields.Date(
        string='Payment Date', default=fields.Date.context_today,
    )

    @api.depends('advance_payment_method')
    def _compute_cash_advance_currency(self):
        order = self.env['sale.order'].browse(
            self.env.context.get('active_ids', [])[:1])
        for wiz in self:
            wiz.cash_advance_currency_id = (
                order.currency_id or self.env.company.currency_id
            )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'advance_journal_id' in fields_list:
            journal = self.env['account.journal'].search(
                [('type', '=', 'bank'),
                 ('company_id', '=', self.env.company.id)],
                limit=1,
            )
            if journal:
                res.setdefault('advance_journal_id', journal.id)
        return res

    def _get_cash_advance_amount(self, order):
        """يحسب قيمة الدفعة النقدية حسب النسبة أو المبلغ الثابت."""
        self.ensure_one()
        if self.cash_advance_type == 'fixed':
            return self.cash_advance_fixed or 0.0
        return order.amount_total * ((self.cash_advance_percentage or 0.0) / 100.0)

    def _create_cash_advance_payment(self, order):
        """ينشئ دفعة مقدمة نقدية (قيد بنك/التزام) ويربطها بأمر البيع."""
        self.ensure_one()
        company = order.company_id
        if not company.customer_advance_account_id:
            raise UserError(_(
                "حدد حساب الدفعات المقدمة أولاً من "
                "Accounting → Configuration → Settings → Customer Advance Account."
            ))
        if not self.advance_journal_id:
            raise UserError(_("اختر دفتر يومية البنك/الخزينة للدفعة المقدمة."))

        amount = self._get_cash_advance_amount(order)
        if amount <= 0:
            raise UserError(_(
                "قيمة الدفعة المقدمة يجب أن تكون أكبر من صفر. "
                "أدخل النسبة أو المبلغ الثابت."
            ))

        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': order.partner_invoice_id.commercial_partner_id.id,
            'amount': amount,
            'currency_id': order.currency_id.id,
            'journal_id': self.advance_journal_id.id,
            'date': self.advance_payment_date or fields.Date.context_today(self),
            'is_customer_advance': True,
            'memo': _('دفعة مقدمة - %s', order.name),
        })
        payment.action_post()
        order.advance_payment_ids = [(4, payment.id)]
        return payment

    def create_invoices(self):
        """اعتراض الإنشاء: لو الخيار دفعة نقدية، اعمل payment بدل فاتورة."""
        if self.advance_payment_method == 'cash_advance':
            sale_orders = self.env['sale.order'].browse(
                self.env.context.get('active_ids', [])
            )
            payments = self.env['account.payment']
            for order in sale_orders:
                payments |= self._create_cash_advance_payment(order)
            if len(payments) == 1:
                return {
                    'name': _('الدفعة المقدمة'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.payment',
                    'res_id': payments.id,
                    'view_mode': 'form',
                }
            return {
                'name': _('الدفعات المقدمة'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.payment',
                'view_mode': 'list,form',
                'domain': [('id', 'in', payments.ids)],
            }
        return super().create_invoices()
