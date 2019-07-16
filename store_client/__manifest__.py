# -*- coding: utf-8 -*-
#################################################################################
# Author      : Efficiencie Solutions Pvt. Ltd. (<www.efficiencie.com>)
# Copyright(c): 2015-Present Efficiencie Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
# You should have received a copy of the License along with this program.
#################################################################################


{
    'name': 'Store For Client',
    'version': '1.0',
    'category': 'Website',
    'sequence': 6,
    'summary': 'Store For Cleint',
    'description': """

=======================

Client Store

""",
    'depends': ['mail', 'uppercrust_backend_theme'],
    'data': [
        'security/security.xml',
        #'security/ir.model.access.csv',
        #'views/store_client_views.xml',
        'views/store_menu.xml',
        'views/templates.xml',
        'data/data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'qweb': [
        'static/src/xml/client.xml',
        'static/src/xml/saas_dashboard.xml',
    ]
}
