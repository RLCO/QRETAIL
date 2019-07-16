# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    merchant_id = fields.Many2one('res.partner', string="Seller")
    store_id = fields.Many2one('store.database.list', string="Store")
    plan_id = fields.Many2one('saas.plan', string='Plan')

    @api.multi
    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res['store_id'] = self.store_id.id
        return res
