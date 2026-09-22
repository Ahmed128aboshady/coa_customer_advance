# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    advance_settled_amount = fields.Monetary(
        string='Settled from Advances',
        compute='_compute_advance_settled_amount',
        currency_field='currency_id',
        help="إجمالي ما تمت تسويته من الدفعات المقدمة مقابل هذه الفاتورة.",
    )
    available_advance_amount = fields.Monetary(
        string='Available Customer Advances',
        compute='_compute_available_advance_amount',
        currency_field='currency_id',
        help="إجمالي الدفعات المقدمة غير المسوَّاة المتاحة لهذا العميل.",
    )

    def _get_customer_advance_payments(self):
        """الدفعات المقدمة غير المسوَّاة بالكامل لنفس العميل والعملة والشركة."""
        self.ensure_one()
        if self.move_type != 'out_invoice':
            return self.env['account.payment']
        return self.env['account.payment'].search([
            ('is_customer_advance', '=', True),
            ('state', 'not in', ('draft', 'canceled', 'rejected')),
            ('partner_id', '=', self.commercial_partner_id.id),
            ('company_id', '=', self.company_id.id),
            ('currency_id', '=', self.currency_id.id),
            ('advance_residual', '>', 0.0),
        ])

    @api.depends('line_ids.matched_debit_ids', 'line_ids.matched_credit_ids')
    def _compute_advance_settled_amount(self):
        for move in self:
            adv_account = move.company_id.customer_advance_account_id
            lines = move.line_ids.filtered(
                lambda l: l.account_id == adv_account
            )
            move.advance_settled_amount = abs(sum(lines.mapped('balance')))

    @api.depends('commercial_partner_id', 'company_id', 'currency_id',
                 'state', 'move_type', 'amount_residual')
    def _compute_available_advance_amount(self):
        for move in self:
            if move.move_type != 'out_invoice':
                move.available_advance_amount = 0.0
                continue
            payments = move._get_customer_advance_payments()
            move.available_advance_amount = sum(
                payments.mapped('advance_residual')
            )

    def action_open_advance_settle_wizard(self):
        self.ensure_one()
        if self.state != 'posted':
            raise UserError(_("يجب ترحيل الفاتورة أولاً قبل تسوية الدفعة المقدمة."))
        if self.move_type != 'out_invoice':
            raise UserError(_("التسوية متاحة لفواتير العملاء فقط."))
        if not self._get_customer_advance_payments():
            raise UserError(_("لا توجد دفعات مقدمة متاحة لهذا العميل."))
        return {
            'name': _('تسوية الدفعة المقدمة'),
            'type': 'ir.actions.act_window',
            'res_model': 'advance.settle.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_invoice_id': self.id},
        }

    def _settle_advance(self, payment, amount):
        """
        ينشئ قيد تسوية: من ح/ الالتزام (مدين) إلى ح/ الذمم AR (دائن)،
        ثم يطابق سطر الالتزام مع سطر الدفعة، وسطر AR مع الفاتورة.
        """
        self.ensure_one()
        company = self.company_id
        adv_account = company.customer_advance_account_id
        ar_line_inv = self.line_ids.filtered(
            lambda l: l.account_id.account_type == 'asset_receivable'
            and not l.reconciled
        )
        if not ar_line_inv:
            raise UserError(_("لا يوجد سطر ذمم مدينة مفتوح في الفاتورة."))
        ar_account = ar_line_inv[0].account_id

        adv_pay_line = payment.move_id.line_ids.filtered(
            lambda l: l.account_id == adv_account and not l.reconciled
        )
        if not adv_pay_line:
            raise UserError(_("لا يوجد سطر التزام مفتوح في الدفعة المقدمة."))

        settle_journal = company.customer_advance_journal_id \
            or self.journal_id

        settle_move = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': settle_journal.id,
            'date': fields.Date.context_today(self),
            'ref': _('تسوية دفعة مقدمة: %(pay)s ← %(inv)s',
                     pay=payment.name, inv=self.name),
            'line_ids': [
                (0, 0, {
                    'name': _('تسوية الدفعة المقدمة'),
                    'account_id': adv_account.id,
                    'partner_id': self.commercial_partner_id.id,
                    'debit': amount,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'name': _('تسوية الدفعة المقدمة'),
                    'account_id': ar_account.id,
                    'partner_id': self.commercial_partner_id.id,
                    'debit': 0.0,
                    'credit': amount,
                }),
            ],
        })
        settle_move.action_post()

        # مطابقة سطر الالتزام في قيد التسوية مع سطر الدفعة المقدمة
        settle_adv_line = settle_move.line_ids.filtered(
            lambda l: l.account_id == adv_account
        )
        (settle_adv_line + adv_pay_line).reconcile()

        # مطابقة سطر AR في قيد التسوية مع سطر الفاتورة
        settle_ar_line = settle_move.line_ids.filtered(
            lambda l: l.account_id == ar_account
        )
        (settle_ar_line + ar_line_inv).reconcile()

        return settle_move
