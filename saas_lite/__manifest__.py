# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Saas Lite',
    'version': '1.0',
    'category': 'Saas Lite',
    'sequence': 6,
    'summary': 'Saas Lite',
    'description': """

- Saas Lite
""",
    'depends': ['store_client', 'account'],
    'data': [
        'views/lite_views.xml',
    ],
    'installable': True,
}
