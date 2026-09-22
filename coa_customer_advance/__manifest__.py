# -*- coding: utf-8 -*-
{
    'name': 'COA Customer Advance Payments',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Register customer advance payments, auto-create liability entries, and settle against invoices with one click',
    'description': """
COA Customer Advance Payments
==============================
Register advance/down-payments received from customers before invoicing.
Automatically creates the correct liability journal entry (Dr. Bank / Cr. Advance Liability).
When the invoice is created, a one-click settlement wizard reconciles the advance against
the invoice outstanding credit - no manual journal entries needed.
Full audit trail and multi-currency support included.
    """,
    'author': 'Community of accountants (COA-Egypt)',
    'website': 'https://www.coa-egy.com',
    'support': 'info@coa-egy.com',
    'images': ['static/description/banner.png'],
    'depends': ['account', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'data/account_advance_data.xml',
        'wizard/advance_settle_wizard_views.xml',
        'views/account_payment_views.xml',
        'views/account_move_views.xml',
        'views/sale_advance_payment_inv_views.xml',
        'views/sale_order_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'price': 49.00,
    'currency': 'USD',
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False,
}
