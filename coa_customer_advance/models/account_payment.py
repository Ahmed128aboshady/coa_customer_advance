# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    is_customer_advance = fields.Boolean(
        string='Customer Advance',
        help="عند التفعيل: تُرحَّل الدفعة إلى حساب الالتزام (دفعات مقدمة) "
             "بدلاً من حساب العملاء (AR).",
    )
    advance_residual = fields.Monetary(
        string='Advance Remaining',
        compute='_compute_advance_residual',
        store=True,
        currency_field='currency_id',
        help="المتبقي من الدفعة المقدمة الذي لم تتم تسويته بعد.",
    )

    @api.depends('is_customer_advance', 'state', 'amount',
                 'move_id.state',
                 'move_id.line_ids.amount_residual',
                 'move_id.line_ids.matched_debit_ids',
                 'move_id.line_ids.matched_credit_ids')
    def _compute_advance_residual(self):
        for pay in self:
            adv_account = pay.company_id.customer_advance_account_id
            if (not pay.is_customer_advance
                    or pay.state in ('draft', 'canceled', 'rejected')
                    or pay.move_id.state != 'posted'
                    or not adv_account):
                pay.advance_residual = 0.0
                continue
            adv_lines = pay.move_id.line_ids.filtered(
                lambda l: l.account_id == adv_account
            )
            pay.advance_residual = abs(sum(adv_lines.mapped('amount_residual')))

    def _get_advance_account(self):
        self.ensure_one()
        account = self.company_id.customer_advance_account_id
        if not account:
            raise UserError(_(
                "لم يتم تحديد حساب الدفعات المقدمة. اذهب إلى "
                "Accounting → Configuration → Settings → Customer Advance Account."
            ))
        return account

    def _prepare_move_line_default_vals(self, write_off_line_vals=None,
                                        force_balance=None):
        """
        القيد القياسي للدفعة: [0] = سطر السيولة، [1] = سطر الذمم (AR).
        عند الدفعة المقدمة نعيد توجيه سطر الذمم [1] إلى حساب الالتزام.
        الحساب يجب أن يبقى account.reconcile=True حتى تعمل التسوية لاحقاً.
        """
        vals_list = super()._prepare_move_line_default_vals(
            write_off_line_vals=write_off_line_vals,
            force_balance=force_balance,
        )
        for pay in self:
            if not pay.is_customer_advance:
                continue
            if pay.partner_type != 'customer' or pay.payment_type != 'inbound':
                raise UserError(_(
                    "الدفعة المقدمة متاحة فقط لمقبوضات العملاء (Inbound / Customer)."
                ))
            adv_account = pay._get_advance_account()
            if len(vals_list) >= 2:
                vals_list[1]['account_id'] = adv_account.id
        return vals_list
