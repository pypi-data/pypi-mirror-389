# -*- coding: utf-8 -*-
{
    'name': 'Coopcycle Connector',
    'version': '16.0.1.0.1',
    'category': 'Connector',
    'depends': [
        'connector',
        'sale'
    ],
    'author': 'Coopdevs Treball SCCL',
    'license': 'LGPL-3',
    'description': """
        Coopcycle Connector
        
        Connect Odoo to Coopcycle API.
        
        Features:
        
         - Synchronize contacts.
     """,
     'data': [
         'data/default_coopcycle_product.xml',
         'data/ir_cron.xml',
         'data/ir_sequence_data.xml',
         'views/res_company.xml',
         'views/res_partner.xml',
         'views/sale_order.xml'
     ],
     'installable': True,
}
