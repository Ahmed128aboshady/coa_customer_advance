# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round


class AdvanceSettleWizard(models.TransientModel):
    _name = 'advance.settle.wizard'
    _description = 'معالج تسوية الدفعة المقدمة'

    invoice_id = fields.Many2one(
        'account.move', string='Invoice', required=True, readonly=True,
    )
    currency_id = fields.Many2one(
        related='invoice_id.currency_id', string='Currency',
    )
    invoice_residual = fields.Monetary(
        related='invoice_id.amount_residual', string='Invoice Due',
        currency_field='currency_id',
    )
    line_ids = fields.One2many(
        'advance.settle.wizard.line', 'wizard_id', string='Advance Payments',
    )
    total_to_settle = fields.Monetary(
        string='Total to Settle', compute='_compute_total_to_settle',
        currency_field='currency_id',
    )

    @api.depends('line_ids.amount_to_settle')
    def _compute_total_to_settle(self):
        for wiz in self:
            wiz.total_to_settle = sum(wiz.line_ids.mapped('amount_to_settle'))

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        invoice = self.env['account.move'].browse(
            self.env.context.get('default_invoice_id')
        )
        if not invoice:
            return res
        payments = invoice._get_customer_advance_payments()
        residual = invoice.amount_residual
        lines = []
        for pay in payments:
            if float_compare(residual, 0.0,
                             precision_rounding=invoice.currency_id.rounding) <= 0:
                suggested = 0.0
            else:
                suggested = min(pay.advance_residual, residual)
                residual -= suggested
            lines.append((0, 0, {
                'payment_id': pay.id,
                'available_amount': pay.advance_residual,
                'amount_to_settle': float_round(
                    suggested, precision_rounding=invoice.currency_id.rounding),
            }))
        res['line_ids'] = lines
        return res

    def action_settle(self):
        self.ensure_one()
        invoice = self.invoice_id
        rounding = invoice.currency_id.rounding
        for line in self.line_ids:
            if not line.payment_id:
                continue
            amount = line.amount_to_settle
            if float_compare(amount, 0.0, precision_rounding=rounding) <= 0:
                continue
            if float_compare(amount, line.available_amount,
                             precision_rounding=rounding) > 0:
                raise UserError(_(
                    "المبلغ المطلوب تسويته من الدفعة %(p)s يتجاوز المتاح.",
                    p=line.payment_id.name,
                ))
            if float_compare(amount, invoice.amount_residual,
                             precision_rounding=rounding) > 0:
                raise UserError(_(
                    "إجمالي التسوية يتجاوز المبلغ المستحق على الفاتورة."
                ))
            invoice._settle_advance(line.payment_id, amount)
        return {'type': 'ir.actions.act_window_close'}


class AdvanceSettleWizardLine(models.TransientModel):
    _name = 'advance.settle.wizard.line'
    _description = 'سطر تسوية الدفعة المقدمة'

    wizard_id = fields.Many2one('advance.settle.wizard', required=True, ondelete='cascade')
    payment_id = fields.Many2one('account.payment', string='Advance Payment', required=True)
    currency_id = fields.Many2one(related='wizard_id.currency_id')
    available_amount = fields.Monetary(string='Available', currency_field='currency_id')
    amount_to_settle = fields.Monetary(string='Amount to Settle', currency_field='currency_id')
