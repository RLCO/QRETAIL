# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Saas Pro',
    'version': '1.0',
    'category': 'Saas Pro',
    'sequence': 6,
    'summary': 'Saas Pro',
    'description': """

- Saas Pro
""",
    'depends': ['store_client', 'account'],
    'data': [
        'views/pro_views.xml',
    ],
    'installable': True,
}
