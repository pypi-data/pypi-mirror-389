from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    coopcycle_product = fields.Many2one(
        comodel_name='product.product',
        string='Default Coopcycle Product',
    )

    coopcycle_tax = fields.Many2one(
        comodel_name='account.tax',
        string='Default Coopcycle Tax',
    )

    coopcycle_user = fields.Char(
        string='Coopcycle API Username',
    )

    coopcycle_password = fields.Char(
        string='Coopcycle API Password',
        password=True,
    )

    coopcycle_instance = fields.Char(
        string='Coopcycle Instance URL',
        placeholder='https://my_company.coopcycle.org/api',
    )

    coopcycle_sync_max_days = fields.Integer(
        string='Coopcycle Sync Max Days',
        help='Maximum number of past days to sync Coopcycle orders.',
    )