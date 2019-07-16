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
    'name': 'Master Store',
    'version': '1.0',
    'category': 'Website',
    'sequence': 6,
    'summary': 'Store Master',
    'description': """
============
Store Master
============

""",
    'depends': ['auth_signup', 'website', 'sale', 'account_payment', 'artesia',],
    'data': [

        'security/store_security.xml',
        'security/ir.model.access.csv',

        'views/store_master_views.xml',
        'views/store_master.xml',
        'views/store_create.xml',
        'views/saas_plan_views.xml',
        'views/res_config_view.xml',
        'views/report_store.xml',
        'views/website.xml',
        'views/signup_modal.xml',

        'data/data.xml',
    ],

    'installable': True,
    'auto_install': False,
}
