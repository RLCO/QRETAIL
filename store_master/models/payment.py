# -*- coding: utf-8 -*-
from odoo import models, fields, api, SUPERUSER_ID


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    merchant_id = fields.Many2one(related="sale_order_ids.merchant_id", string="Seller")
    store_id = fields.Many2one('store.database.list', string="Store")

    @api.multi
    def write(self, vals):
        res = super(PaymentTransaction, self).write(vals)
        if 'state' in vals:
            for t in self.filtered(lambda t: t.store_id):
                if vals['state'] == 'done':
                    t.store_id.extend_store_validity()
                    t.store_id.send_mail_to_client('validity_extend')
                val = {'state': t.state}
                t.update_client_transaction(val)
        return res

    def update_client_transaction(self, vals):
        registry = self.store_id.registry()
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            TX = env['store.payment.transaction'].sudo().search([('name', '=', self.reference)], limit=1)
            TX.write(vals)

    def _transfer_form_validate(self, data):
        #_logger.info('Validated transfer payment for tx %s: set as pending' % (self.reference))
        try:
            self._set_transaction_done()
            self._reconcile_after_transaction_done()
        except odoo.exceptions.UserError:
            pass
        return True