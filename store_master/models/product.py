# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    saas_default = fields.Boolean(
        'Is default',
        help='Use as default SaaS product on signup form')
    on_create_email_template = fields.Many2one(
        'mail.template',
        string='credentials mail')
    saas_plan_id = fields.Many2one('saas_portal.plan',
                                   string='Related SaaS Plan',
                                   ondelete='restrict')
