# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    advance_payment_ids = fields.Many2many(
        'account.payment',
        'sale_order_advance_payment_rel',
        'order_id', 'payment_id',
        string='Advance Payments',
        copy=False,
        help="الدفعات المقدمة النقدية المسجلة على هذا الأمر (قيد بنك/التزام).",
    )
    advance_payment_count = fields.Integer(
        compute='_compute_advance_payment_count', string='Advance Payments',
    )
    advance_payment_total = fields.Monetary(
        compute='_compute_advance_payment_count', string='Advance Paid',
        currency_field='currency_id',
    )

    @api.depends('advance_payment_ids', 'advance_payment_ids.state')
    def _compute_advance_payment_count(self):
        for order in self:
            paid = order.advance_payment_ids.filtered(
                lambda p: p.state == 'paid')
            order.advance_payment_count = len(paid)
            order.advance_payment_total = sum(paid.mapped('amount'))

    def action_view_advance_payments(self):
        self.ensure_one()
        return {
            'name': _('الدفعات المقدمة'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.advance_payment_ids.ids)],
        }
