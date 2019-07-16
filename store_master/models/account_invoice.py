# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    store_id = fields.Many2one('store.database.list', string="Store")

    @api.multi
    def action_invoice_paid(self):
        res = super(AccountInvoice, self).action_invoice_paid()
        for inv in self.filtered(lambda i: i.store_id):
            inv.store_id.extend_store_validity()
        return res
