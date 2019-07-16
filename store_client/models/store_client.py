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

import json
import time
import logging
import odoo
from odoo import fields, api, models, SUPERUSER_ID, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


MASTER_DB = 'eze'


class ResCompany(models.Model):
    _inherit = 'res.company'

    store_url = fields.Char('Store URL')
    favicon = fields.Binary('Favicon', attachment=True)
    domain_confirm = fields.Boolean(compute='has_domain_change', string="Domain Confirm", store=True)
    domain_old = fields.Char()

    @api.depends('store_url', 'domain_old')
    @api.multi
    def has_domain_change(self):
        for c in self:
            if c.store_url != c.domain_old:
                c.domain_confirm = False
            else:
                c.domain_confirm = True

    @api.multi
    def on_domain_confirm(self):
        for c in self:
            c.domain_old = c.store_url
            tmpl = self.env.ref('store_client.confirm_domain')
            tmpl.send_mail(c.id, force_send=True, raise_exception=False)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    temporary_password = fields.Char("Temporary Password", invisible=True, copy=False)


class StoreMaster(models.Model):
    _name = 'store.master'
    _inherit = 'mail.thread'

    name = fields.Char(string='Store Name', index=True)
    database_size = fields.Char(compute='_get_database_size', string='Database Size')
    db_name = fields.Char(string="Database name", readonly=True)
    last_update = fields.Datetime(string="Last Activity in DB")
    access_url = fields.Char('Access Url')

    note = fields.Text('Note')
    color = fields.Integer()
    state = fields.Selection(
        [('new', 'New'), ('in_progress', 'In Progress'), ('renew', 'Renew'), ('close', 'Closed'), ('cancel', 'cancelled')],
        required=True, default='new')

    exp_date = fields.Date('Expiry Date', track_visibility='onchange')
    start_date = fields.Datetime(string="Start Date", default=time.strftime('%Y-%m-%d'))
    expired = fields.Boolean('Expired')
    exp_period = fields.Selection([('free_trail', 'Free Trail'), ('monthly', '1 Month'), ('quaterly', '3 Months'), ('half-yearly', '6 Months'), ('yearly', '12 Months')], string="EXP Periods", track_visibility='onchange')
    partner_name = fields.Char(string="Partner Name")
    subscription_line_ids = fields.One2many('store.subscription.line', 'store_id', string="Subscription Line")
    recurring_total = fields.Float(compute='_get_reccuring_amount', string="Recurring Amount", store=True)
    currency_id = fields.Many2one('res.currency', string="Currency")
    uuid = fields.Char('Account UUID')
    description = fields.Text(string="Description")
    payment_tx_ids = fields.One2many('store.payment.transaction', 'store_id', string="Payments")
    modules_to_display = fields.Text(readonly=True, string="Technicals")
    user_limit = fields.Integer(string="User Limit", readonly=True)

    @api.multi
    def _get_no_of_users(self):
        for store in self:
            store.no_of_users = self.env['res.users'].search_count([])

    @api.multi
    def _get_database_size(self):
        self.ensure_one()

        self.env.cr.execute("select pg_database_size('%s')" % self.db_name)
        db_storage = self.env.cr.fetchone()[0]

        db_storage = int(db_storage / (1024*1024))
        mbsize = str(db_storage) + " MB"
        size_total = mbsize
        self.database_size = size_total

    @api.multi
    @api.depends('subscription_line_ids')
    def _get_reccuring_amount(self):
        for store in self:
            total = 0
            for line in store.subscription_line_ids:
                total += line.price_subtotal
            store.recurring_total = total

    @api.model
    def check_enterprise_code(self, enterprise_code):
        config_param = self.env['ir.config_parameter'].sudo()
        registry = self.registry(MASTER_DB)
        res = {}
        store_id = config_param.get_param('master.store.id')
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            res = env['store.database.list'].sudo()._is_valid_enterprise_code(int(store_id), enterprise_code)
            if res.get('valid'):
                store = env['store.database.list'].browse(int(store_id))
                store.sudo().write({'start_date': res.get('start_date'), 'exp_date': res.get('exp_date')})
        if res and res.get('valid'):
            #config_param.set_param('database.secret.key', enterprise_code)
            config_param.set_param('database.expire.date', res.get('exp_date'))
            return {'exp_date': res.get('exp_date')}
        return False

    @api.model
    def send_activation_mail(self):
        config_param = self.env['ir.config_parameter'].sudo()
        registry = self.registry(MASTER_DB)
        store_id = config_param.get_param('master.store.id')
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            store = env['store.database.list'].browse(int(store_id))
            store.send_activation_mail()
        return True

    @api.model
    def remove_store(self):
        config_param = self.env['ir.config_parameter'].sudo()
        registry = self.registry(MASTER_DB)
        store_id = config_param.get_param('master.store.id')
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            store = env['store.database.list'].browse(int(store_id))
            store.remove_store()
        return True

    def registry(self, db, new=False, **kwargs):
        m = odoo.modules.registry.Registry
        return m.new(db, **kwargs)


class StoreSubscriptionLine(models.Model):
    _name = 'store.subscription.line'

    name = fields.Text(string='Description')
    quantity = fields.Float(string="Quantity")
    price_unit = fields.Float('Unit Price')
    discount = fields.Float('Discount (%)')
    price_subtotal = fields.Float(compute='_amount_line', string='Sub Total')
    store_id = fields.Many2one('store.master', string="Store")

    @api.multi
    def _amount_line(self):
        for line in self:
            line.price_subtotal = line.quantity * line.price_unit * (100.0 - line.discount) / 100.0


class StorePaymentTransaction(models.Model):
    _name = 'store.payment.transaction'

    name = fields.Char(string="Transaction Reference")
    payment_method = fields.Char(string="Payment Method")
    create_date = fields.Datetime('Transaction Date', readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('pending', 'Pending'),
             ('done', 'Done'), ('error', 'Error'),
             ('cancel', 'Canceled')
             ], 'Status', required=True,
            track_visibility='onchange', copy=False)
    acquirer_reference = fields.Char('Acquirer Reference', help='Reference of the TX as stored in the acquirer database')
    store_id = fields.Many2one('store.master', string="Store")
    partner_name = fields.Char('Partner Name')
    amount = fields.Float('Amount', required=True, digits=(16, 2), track_visibility='always', help='Amount')


# class ResUsers(models.Model):
#     _inherit = 'res.users'

#     @api.model
#     def create(self, vals):
#         # check if user reach to it's limit
#         limit = self.env.ref('store_client.store_client_demo').user_limit
#         users_count = self.sudo().search_count([('active', '=', True)])
#         if limit <= users_count:
#             raise UserError(_('You are not allowed to create a users more than your limit \n your store limit of creating user is up to %s \n if you need more user than you can contact to ezeselling.') % (limit))
#         return super(ResUsers, self).create(vals)

#     @api.multi
#     def write(self, vals):
#         res = super(ResUsers, self).write(vals)
#         if ('login' in vals or 'password' in vals) and not self.env.context.get('no_update'):
#             config_param = self.env['ir.config_parameter'].sudo()
#             registry = self.registry(MASTER_DB)
#             store_id = config_param.get_param('master.store.id')
#             with registry.cursor() as cr:
#                 env = api.Environment(cr, SUPERUSER_ID, {})
#                 store = env['store.database.list'].with_context(no_update=True).browse(int(store_id))
#                 user = store.partner_id.user_ids[0]
#                 if vals.get('login'):
#                     user.login = vals['login']
#                 if vals.get('password'):
#                     user.password = vals['password']
#         return res


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    backend_favicon = fields.Binary(string="Backend Favicon")

    @api.multi
    def set_backend_favicon(self):
        backend_favicon = self.backend_favicon
        res = self.env['ir.default'].sudo().get('res.config.settings', 'backend_favicon', backend_favicon)
        return res


# class IrModuleModule(models.Model):
#     _inherit = 'ir.module.module'

#     @api.model
#     def search(self, args, offset=0, limit=None, order=None, count=False):
#         if self.env.context.get('custom_app'):
#             client = self.env.ref('store_client.store_client_demo')
#             if client.modules_to_display:
#                 m_list = json.loads(client.modules_to_display)
#                 args += [['name', 'in', m_list]]
#         res = super(IrModuleModule, self).search(args, offset=0, limit=None, order=order, count=False)
#         return res

#     @api.multi
#     def button_install(self):
#         m_list = self.env.ref('store_client.store_client_demo').modules_to_display
#         if m_list:
#             m_list = json.loads(m_list)
#             if self.name not in m_list:
#                 raise UserError(_('You are not allowed to install this feature'))

#         res = super(IrModuleModule, self).button_install()
#         return res
