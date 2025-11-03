# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import models, fields, api
from odoo.addons.component.core import Component
from math import ceil
from stdnum.eu import vat
import html

_logger = logging.getLogger(__name__)

## Afegim un indicador que és creada des de coopcycle. Ja veurem què en farem però de bones a primeres crec que voldrem poder filtrar
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_coopcycle_import = fields.Boolean("Is this Sale Order created by an Coopcycle Import?", default=False)
    

## A Sale order line afegirem un ID per poder saber quina línia de factura de Coopcycle és la que suposa una importació
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    coopcycle_id = fields.Char("Identificador a Coopcycle")
    