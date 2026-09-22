# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    customer_advance_account_id = fields.Many2one(
        'account.account',
        string='Customer Advance Account',
        domain="[('account_type', '=', 'liability_current'), ('reconcile', '=', True)]",
        help="حساب التزام (Current Liabilities) للدفعات المقدمة من العملاء. "
             "يجب أن يكون قابلاً للتسوية (Allow Reconciliation).",
    )
    customer_advance_journal_id = fields.Many2one(
        'account.journal',
        string='Advance Settlement Journal',
        domain="[('type', '=', 'general')]",
        help="دفتر اليومية المستخدم لقيود تسوية الدفعات المقدمة. "
             "إن تُرك فارغاً يُستخدم دفتر يومية الفاتورة.",
    )


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    customer_advance_account_id = fields.Many2one(
        related='company_id.customer_advance_account_id',
        string='Customer Advance Account',
        readonly=False,
    )
    customer_advance_journal_id = fields.Many2one(
        related='company_id.customer_advance_journal_id',
        string='Advance Settlement Journal',
        readonly=False,
    )
