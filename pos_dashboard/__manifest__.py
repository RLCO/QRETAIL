# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Point of Sale Dashboard',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'summary': 'Point Of Sale Dashboard ',
    'description': """

=======================

Point of Sale Dashboard

""",
    'depends': ['point_of_sale'],
    'data': [
        'views/views.xml',
        'views/templates.xml'
    ],
    'qweb': [
        'static/src/xml/pos_dashboard.xml',
    ],
    'installable': True,
    'website': 'https://www.odoo.com/page/point-of-sale',
    'auto_install': False,
}
