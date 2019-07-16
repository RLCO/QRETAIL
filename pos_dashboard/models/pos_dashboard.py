# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.multi
    def _convert_date_to_user_tz(self):
        date = fields.Datetime.from_string(self.date_order)
        return fields.Datetime.to_string(fields.Datetime.context_timestamp(self, date))


class PosConfig(models.Model):
    _inherit = 'pos.config'

    target_for_today = fields.Float(string="Set target for today")
