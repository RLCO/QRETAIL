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

from odoo import fields, api, models, SUPERUSER_ID, _
from odoo import exceptions


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_owner = fields.Boolean()
    client_id = fields.Char()

    @api.model
    def create(self, vals):
        max_users = self.env["ir.config_parameter"].sudo().get_param("saas_client.max_users")
        max_users = int(max_users)
        if max_users:
            cur_users = self.env['res.users'].search_count([('share', '=', False), ('id', 'not in', [SUPERUSER_ID])])
            if cur_users >= max_users:
                raise exceptions.Warning(_('Maximum allowed users is %(max_users)s, while you already have %(cur_users)s') % {'max_users': max_users, 'cur_users': cur_users})
        return super(ResUsers, self).create(vals)
