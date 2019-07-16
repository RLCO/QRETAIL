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

from odoo import api, http, SUPERUSER_ID
from odoo.exceptions import AccessError
from odoo.http import request

from odoo.addons.store_client.models.store_client import MASTER_DB
from odoo.addons.web.controllers.main import Database
from odoo.addons.web_settings_dashboard.controllers.main import WebSettingsDashboard


class WebDatabase(Database):

    @http.route()
    def backup(self, master_pwd, name, backup_format='zip', eze_backup=False):
        if eze_backup:
            # We need here strong checking before giving backup ... since it
            # can be call from outside
            master_pwd = self._get_master_password()
        return super(WebDatabase, self).backup(master_pwd, name, backup_format=backup_format)

    def _get_master_password(self):
        registry = request.env['store.master'].registry(MASTER_DB)
        with registry.cursor() as cr:
            # install some modules
            env = api.Environment(cr, SUPERUSER_ID, {})
            return env['ir.config_parameter'].get_param('master.db.secret', False)


class StoreDashboard(http.Controller):

    @http.route('/store_dashboard/data', type='json', auth='user')
    def store_dashboard_data(self, **kw):
        if not request.env.user.has_group('base.group_user'):
            raise AccessError("Access Denied")

        store = request.env['store.master'].search([], limit=1)

        res = {
            'custome': {
                'customer': store.no_of_users,
                'users': store.no_of_users,
                'products': store.no_of_products,
                'total_sales': store.total_sales,
            },
            'store_info': {
                'name': store.name,
                'dbname': store.db_name,
                'exp_date': store.exp_date,
                'exp_period': store.exp_period,
                'start_date': store.start_date,
                'partner_name': store.partner_name,
                'database_size': store.database_size,
            },
            'store_service': {
                'store_data': [{
                    'name': l.name,
                    'quantity': l.quantity,
                    'price_unit': l.price_unit,
                    'discount': l.discount,
                    'price_subtotal': l.price_subtotal} for l in store.subscription_line_ids]
            },
            'store_payment': {
                'store_data': [{
                    'name': l.name,
                    'payment_method': l.payment_method,
                    'create_date': l.create_date,
                    'state': l.state,
                    'acquirer_reference': l.acquirer_reference,
                    'amount': l.amount} for l in store.payment_tx_ids]
            }
        }
        return res


class WebSettingsDashboard(WebSettingsDashboard):

    @http.route()
    def web_settings_dashboard_data(self, **kw):
        res = super(WebSettingsDashboard, self).web_settings_dashboard_data()

        res['company'] = {
            'company_id': request.env.user.company_id.id,
            'company_name': request.env.user.company_id.name
        }

        return res
