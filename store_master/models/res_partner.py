# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _default_product_approve(self):
        res = self.env['ir.default'].get('seller.config.settings', 'product_approve')
        if res:
            return res
        return False

    @api.model
    def _default_global_commission(self):
        res = self.env['ir.default'].get('seller.config.settings', 'global_commission')
        if res:
            return res
        return False

    @api.model
    def _default_amount_limit(self):
        res = self.env['ir.default'].get('seller.config.settings', 'amount_limit')
        if res:
            return res
        return False

    @api.model
    def _default_product_count(self):
        res = self.env['ir.default'].get('seller.config.settings', 'product_count')
        if res:
            return res
        return False

    @api.model
    def _default_sale_count(self):
        res = self.env['ir.default'].get('seller.config.settings', 'sale_count')
        if res:
            return res
        return False

    @api.model
    def _default_seller_since(self):
        res = self.env['ir.default'].get('seller.config.settings', 'seller_since')
        if res:
            return res
        return False

    @api.model
    def _default_return_policy(self):
        res = self.env['ir.default'].get('seller.config.settings', 'return_policy')
        if res:
            return res
        return False

    @api.model
    def _default_shipping_policy(self):
        res = self.env['ir.default'].get('seller.config.settings', 'shipping_policy')
        if res:
            return res
        return False

    @api.model
    def _default_terms_condition(self):
        res = self.env['ir.default'].get('seller.config.settings', 'terms_condition')
        if res:
            return res
        return False

    @api.model
    def _default_email_to_seller_button(self):
        res = self.env['ir.default'].get('seller.config.settings', 'email_to_seller_button')
        if res:
            return res
        return False

    is_merchant = fields.Boolean(string='Is Merchant')
    temporary_password = fields.Char("Temporary Password", invisible=True, copy=False)
    product_approve = fields.Boolean(string="Auto Product Approve", default=_default_product_approve)
    global_commission = fields.Float(string="Global Commission(%)", default=_default_global_commission)
    amount_limit = fields.Float(string="Amount Limit", default=_default_amount_limit)
    product_count = fields.Boolean(string="Show Product Count On Website", default=_default_product_count)
    sale_count = fields.Boolean(string="Show Sale Count On Website", default=_default_sale_count)

    show_seller_since = fields.Boolean(string="Show Seller Since", default=_default_seller_since)
    show_return_policy = fields.Boolean(string="Show Return Policy On Website", default=_default_return_policy)
    show_shipping_policy = fields.Boolean(string="Show Shipping Policy On Website", default=_default_shipping_policy)

    show_terms_condition = fields.Boolean(string="Show Terms & Conditions On Website", default=_default_terms_condition)
    email_to_seller_button = fields.Boolean(string="Show 'Email to Seller' button on website.", default=_default_email_to_seller_button)

    return_policy = fields.Html(string="Return Policy")
    shipping_policy = fields.Html(string="Shipping Policy")
    terms_condition = fields.Html(string="Terms & Condition")
    seller_since = fields.Datetime(string="Seller Since")
    is_store_owner = fields.Boolean()

    state = fields.Selection([('draft', 'Draft'), ('pending', 'Pending'), ('approved', 'Approved'), ('denied', 'Denied')], default='draft')

    @api.one
    def send_contact_info_email(self):
        if not self.email:
            return False
        contact_template = self.env.ref('store_master.contact_email')
        if contact_template:
            contact_template.sudo().send_mail(self.id, force_send=True)
        return True

    @api.multi
    def seller_approve(self):
        self.state = 'approved'
        group_id = self.env.ref('store_master.group_seller').id
        user = self.user_ids[0]
        user.write({'groups_id': [(6, 0, [group_id])]})

    @api.multi
    def seller_to_reject(self):
        self.state = 'denied'

    @api.multi
    def seller_set_pending(self):
        self.state = 'pending'

    @api.multi
    def seller_request_to_approve(self):
        self.sudo().state = 'pending'
        res = self.env['ir.default'].get('seller.config.settings', 'new_seller_notif_admin')
        if res:
            tmpl_id = self.env['ir.default'].get('seller.config.settings', 'new_seller_notif_admin_tmpl')
            template = self.env['mail.template'].browse(tmpl_id)
            template.send_mail(self.env.user.partner_id.id, force_send=True, raise_exception=False)
