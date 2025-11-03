from odoo import models, fields, api
import hashlib
import logging
import requests
import json
import os

IMPORT_DELTA_BUFFER = 30  # seconds

_logger = logging.getLogger(__name__)

class CoopcycleBackend(models.Model):
    _name = 'coopcycle.backend'
    _inherit = 'connector.backend'
    app_name = fields.Char('Name', required=True)
    url = fields.Char('URL', required=True)
    verbose = fields.Boolean()
    session_token = fields.Char('Session Token')
    language = fields.Char('Language')
    notify_on_save = fields.Boolean('Notify On Save')
    import_partners_from_date = fields.Datetime(
        string='Import partners from date',
    )

    def connect(self, comp):
        params = {
            '_username': comp.coopcycle_user,
            '_password': comp.coopcycle_password,
        }
        result = requests.post(comp.coopcycle_instance+'/login_check', data=params)
        session_token = result.json()['token']
        _logger.info('Connected to backend: %s', comp.coopcycle_instance)
        return session_token

    def get_all_invoice_line_items(self, comp, params=None, token=None, ):
        params = params or {}
        headers = {"Authorization": f"Bearer {token}"}

        result = requests.get(comp.coopcycle_instance+'/invoice_line_items/export', params=params, headers=headers)
        return result
    
    def get_invoice_line_items_grouped_by_organization(self, comp, params=None, token=None):
        params = params or {}
        headers = {"Authorization": f"Bearer {token}"}

        result = requests.get(comp.coopcycle_instance+'/invoice_line_items/grouped_by_organization', params=params, headers=headers)
        return result

    def import_sale_orders(self, comp):
        backend = self

        self.env['res.partner'].import_batch(backend, comp)
        return True

    @api.model
    def cron_import_sale_orders(self):
        companies = self.env['res.company'].search([])
        for comp in companies:
            if comp.coopcycle_instance and comp.coopcycle_user and comp.coopcycle_password and comp.coopcycle_product and comp.coopcycle_tax and comp.coopcycle_sync_max_days:
                backend = self.create([{
                    'app_name': 'ODOO Coopcycle Connector',
                    'url': comp.coopcycle_instance
                }])
                _logger.info('Backend created with instance: %s', comp.coopcycle_instance)
                backend.import_sale_orders(comp)
