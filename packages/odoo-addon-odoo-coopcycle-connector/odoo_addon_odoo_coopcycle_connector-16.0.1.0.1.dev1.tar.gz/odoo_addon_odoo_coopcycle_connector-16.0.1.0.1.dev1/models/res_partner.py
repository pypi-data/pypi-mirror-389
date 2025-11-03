# Copyright 2013-2019 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import models, fields, api
from odoo.addons.component.core import Component
from math import ceil
from datetime import datetime, timedelta
from stdnum.eu import vat
import html

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    coopcycle_bind_id = fields.Integer(
        string="Coopcycle Partner ID",
        company_dependent=True,
        tracking=True
    )

    @api.model
    def import_batch(self, backend, comp):
        token = backend.connect(comp)
        tomorrow = datetime.today() + timedelta(days=1)
        tomorrow.strftime('%Y-%m-%d')
        dateAfter = datetime.today() - timedelta(days=int(comp.coopcycle_sync_max_days))
        dateAfter.strftime('%Y-%m-%d')
        params = {
            'state[]': ['new', 'accepted', 'fullfilled'],
            'date[after]': dateAfter,
            'date[before]': tomorrow,
            'page': 1,
            'itemsPerPage': 10,
        }

        self.update_partners_list(backend, params, token, comp)
        _logger.info('Partners list updated')
        rsps = self.env['res.partner'].with_company(comp.id).search([('coopcycle_bind_id', '!=', False)])
        for partner in rsps:
            partner.get_unprocessed_order_lines(params, backend, token, comp)

    @api.model
    def update_partners_list(self, backend, params, token, comp):
        result2 = backend.get_invoice_line_items_grouped_by_organization(comp, params, token)
        for organization in result2.json()['hydra:member']:
            sID = organization['storeId']
            rsp = self.env['res.partner'].with_company(comp.id).search([('coopcycle_bind_id', '=', sID)])
            if not rsp:
                name = organization['organizationLegalName']
                rsp = self.env['res.partner'].search([('name', '=', name)])
                if rsp:
                    if comp.id != rsp.company_id.id:
                        rsp.company_id=False
                    rsp.with_company(comp.id).coopcycle_bind_id = organization['storeId']
            if not rsp:
                self.env['res.partner'].with_company(comp.id).create([{
                    'coopcycle_bind_id': organization['storeId'],
                    'name': organization['organizationLegalName']
                }])

    def get_unprocessed_order_lines(self,params, backend, token, comp):
        params['store'] = self.with_company(comp.id).coopcycle_bind_id
        result = backend.get_all_invoice_line_items(comp, params, token)
        uom = self.env.ref('uom.product_uom_unit')
        lis = []
        for lineitem in result.json()['hydra:member']:
            iDs = lineitem['@id'].split('/')[-1].split('-')[1:3]
            iD = iDs[0] + '-' + iDs[1]
            sol = self.env['sale.order.line'].search([('coopcycle_id', '=', iD)])
            price = lineitem['Total products (excl. VAT)']

            if not sol:
                lis.append((0, 0, {'name': lineitem['Description'], 
                                   'product_id': comp.coopcycle_product.id,
                                   'tax_id': [(4,comp.coopcycle_tax.id)],
                                   'price_unit': price,
                                   'coopcycle_id': iD,
                                   'product_uom': uom.id,
                                   'product_uom_qty': 1,}))
                _logger.info('Sale order line created for partner %s with id %s', self.name, iD)
                
        if lis:        
            self.env['sale.order'].create({
                'name': self.env['ir.sequence'].next_by_code('coopcycle.sale.order'),
                'company_id': comp.id,
                'partner_id': self.id,
                'is_coopcycle_import': True,
                'order_line': lis
            })

        _logger.info('Unprocessed order lines from partner %s', self.name)