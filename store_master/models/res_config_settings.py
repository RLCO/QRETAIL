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

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    notif_store_create_tmpl = fields.Many2one('mail.template', config_parameter='saas_port.notif_store_create_tmpl')
    notif_email_verification_tmpl = fields.Many2one('mail.template', config_parameter='saas_port.notif_email_verification_tmpl')
    notif_after_store_expire_tmpl = fields.Many2one('mail.template', config_parameter='saas_port.notif_after_store_expire_tmpl')
    notif_store_validity_extend_tmpl = fields.Many2one('mail.template', config_parameter='saas_port.notif_store_validity_extend_tmpl')
    notif_before_store_expire_tmpl = fields.Many2one('mail.template', config_parameter='saas_port.notif_before_store_expire_tmpl')
    plan_change_tmpl = fields.Many2one('mail.template', config_parameter='saas_port.plan_change_tmpl')
    payment_tmpl = fields.Many2one('mail.template', config_parameter='saas_port.payment_tmpl')
    free_trial_days = fields.Integer(string="Free Trial Days", default=15, config_parameter='saas_port.free_trial_days')

