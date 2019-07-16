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
import uuid
import datetime
import random
from dateutil.relativedelta import relativedelta

import odoo
from odoo.service import db as database
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


def random_password():
    # the passaword has an entropy of about 120 bits (6 bits/char * 20 chars)
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    return ''.join(random.SystemRandom().choice(chars) for i in xrange(20))


class StoreTemplate(models.Model):
    _name = 'store.template'

    name = fields.Char(string='Template Name', required=True, index=True)
    exp_period = fields.Selection([
        ('free_trail', 'Free Trail'),
        ('monthly', '1 Month'),
        ('quaterly', '3 Months'),
        ('half-yearly', '6 Months'),
        ('yearly', '12 Months')], string="EXP Periods")
    manager_id = fields.Many2one('res.users', string="Sales Representative")
    subscription_line_ids = fields.One2many('store.subscription.line', 'store_tmpl_id', string="Subscription Line")
    subscription_line_option_ids = fields.One2many('store.subscription.line.option', 'store_id', string="Subscription Line")
    allow_online = fields.Boolean(string="Allow to Display Online")
    currency_id = fields.Many2one('res.currency', string="Currency")
    plan_id = fields.Many2one('saas.plan', string='Plan')
    total_amount = fields.Integer(compute='_get_total_amount', string="Amount", store=True)

    @api.multi
    @api.depends('subscription_line_ids')
    def _get_total_amount(self):
        for temp in self:
            total = 0
            for line in temp.subscription_line_ids:
                total += line.price_subtotal

            temp.total_amount = total

    @api.multi
    def get_expiry_period(self, exp_date=False):
        self.ensure_one()
        month = 0
        if self.exp_period == 'monthly':
            month = 1
        if self.exp_period == 'quaterly':
            month = 3
        if self.exp_period == 'half-yearly':
            month = 6
        if self.exp_period == 'yearly':
            month = 12
        return exp_date + relativedelta(months=+month)


class StoreDatabaseList(models.Model):
    _name = 'store.database.list'
    _inherit = 'mail.thread'

    @api.model
    def _default_template(self):
        return self.env['store.template'].search([('exp_period', '=', 'free_trail')], limit=1)

    def _get_comapny(self):
        return self.env.user.company_id.id

    def _get_default_expire_date(self):
        return fields.Datetime.from_string(fields.Datetime.now()) + datetime.timedelta(hours=20)

    def _get_note(self):
        res = """
            Testing
        """
        return res

    def generate_client_id(self):
        return str(uuid.uuid1())

    reference = fields.Char(string='Reference')
    name = fields.Char(string='Store Name', index=True)
    total_sales = fields.Integer(string='Total Sales')
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
    start_date = fields.Datetime(string="Start Date", default=fields.Datetime.now)
    is_expired = fields.Boolean('Expired', compute='_compute_is_expired', search='_search_expired_store')
    sale_order_ref = fields.Many2one('sale.order', string='Sale Order Ref.')
    exp_period = fields.Selection([
        ('free_trail', 'Free Trail'),
        ('monthly', '1 Month'),
        ('quaterly', '3 Months'),
        ('half-yearly', '6 Months'), ('yearly', '12 Months')], string="EXP Periods", track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', string="Partner")
    partner_name = fields.Char(related="partner_id.name", string="Partner Name")
    plan_id = fields.Many2one("saas.plan", string="Plan")
    subscription_line_ids = fields.One2many('store.subscription.line', 'store_id', string="Subscription Line")
    recurring_total = fields.Float(compute='_get_reccuring_amount', string="Recurring Amount", store=True)
    currency_id = fields.Many2one(related='company_id.currency_id', relation='res.currency', string="Currency")
    db_uuid = fields.Char('Database UUID', default=generate_client_id, copy=False, required=True)
    client_id = fields.Char('Client UUID', default=generate_client_id, copy=False, required=True)
    is_email_verified = fields.Boolean(string="Is Email Verified")
    website_url = fields.Char('Website URL', compute='_website_url', help='The full URL to access the document through the website.')
    expire_reason = fields.Selection([('trial', 'Trial'), ('renewal', 'Renew'), ('upsell', 'Upsell')], string="Expire Reason", track_visibility='onchange', default='trial')
    description = fields.Text(string="Description", default=_get_note)
    payment_tx_ids = fields.One2many('payment.transaction', 'store_id', string="Payments")
    manager_id = fields.Many2one('res.users', string="Sales Representative")
    template_id = fields.Many2one('store.template', string="Template", default=_default_template)
    subscription_code_ids = fields.One2many('subscription.code', 'store_id', string="Subscription Code")
    need_payment = fields.Boolean(string="Need Payment", default=False)
    company_id = fields.Many2one('res.company', string="Company", default=_get_comapny)
    store_exp_date_verify = fields.Datetime('Expiry Date', track_visibility='onchange', default=_get_default_expire_date)
    is_template_db = fields.Boolean(string='Is Template Database')
    owner_user_id = fields.Many2one('res.users', string='Owner User')

    display_modules_ids = fields.Many2many('ir.module.module', string='Modules Visible to Clients')
    max_user = fields.Integer(string="Maximum User", default=5)

    update_addons_list = fields.Boolean('Update Addon List', default=True)
    update_addons = fields.Char('Update Addons', size=256)
    install_addons = fields.Char('Install Addons', size=256)
    uninstall_addons = fields.Char('Uninstall Addons', size=256)
    show_addons = fields.Char('Display Addons')
    access_owner_add = fields.Char('Grant access to Owner')
    hide_menus = fields.Char('Hide Menus')
    access_remove = fields.Char(
        'Restrict access',
        help='Restrict access for all users except super-user.\nNote, that ')
    param_ids = fields.One2many('saas.config.param', 'store_id', 'Parameters')
    client_db_action = fields.Selection([
        ('params', 'Config Params'),
        ('update_addons', 'Update Addons'),
        ('install_addons', 'Install Addons'),
        ('uninstall_addons', 'Uninstall Addons'),
        ('show_addons', 'Show Addons'),
        ('access_owner_add', 'Grant Access to Owner'),
        ('access_remove', 'Restrict access'),
        ('hide_menus', 'Hide Menus'),
    ], string='Client Database Action')
    is_suspended = fields.Boolean()
    ondelete_removedb = fields.Boolean()

    def _search_expired_store(self, operator, value):
        current_date = fields.Date.context_today(self)
        return [('exp_date', '<', current_date)]

    @api.depends('client_id')
    def _website_url(self):
        for store in self:
            store.website_url = '/my/store/contract/%s/%s' % (store.id, store.client_id)

    @api.multi
    def _compute_is_expired(self):
        for record in self:
            if record.exp_date:
                current_date = fields.Date.context_today(record)
                record.is_expired = record.exp_date < current_date
            else:
                record.is_expired = False

    @api.multi
    def open_website_url(self):
        return {
            'type': 'ir.actions.act_url',
            'url': self.website_url,
            'target': 'self',
        }

    @api.multi
    def registry(self, new=False, **kwargs):
        self.ensure_one()
        m = odoo.modules.registry.Registry
        return m.new(self.db_name, **kwargs)

    @api.multi
    @api.depends('subscription_line_ids')
    def _get_reccuring_amount(self):
        for store in self:
            total = 0
            for line in store.subscription_line_ids:
                total += line.price_subtotal

            store.recurring_total = total

    @api.multi
    @api.onchange('exp_period')
    def on_change_expire_period(self):
        if self.exp_period:
            month = 0
            if self.exp_period == 'monthly':
                month = 1
            if self.exp_period == 'quaterly':
                month = 3
            if self.exp_period == 'half-yearly':
                month = 6
            if self.exp_period == 'yearly':
                month = 12
            self.exp_date = self.exp_date + relativedelta(months=+month)

    @api.multi
    @api.onchange('exp_date')
    def on_change_expire_date(self):
        if self.exp_date:
            # update the client database expirey date
            registry = self.registry()
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                config = env['ir.config_parameter'].sudo()
                configs = config.search([('key', '=', 'database.expire.date')])
                configs.write({'value': self.exp_date})

                if self.exp_date >= time.strftime('%Y-%m-%d'):
                    self.state = 'in_progress'
                    self.update_clinet_info(self.db_name, {'state': 'in_progress', 'exp_date': self.exp_date})

                if self.exp_date < time.strftime('%Y-%m-%d'):
                    self.state = 'renew'
                    self.update_clinet_info(self.db_name, {'state': 'renew', 'exp_date': self.exp_date})

    def update_clinet_info(self, dbname, vals):
        if dbname:
            registry = self.registry()
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                store_client = env.ref('store_client.store_client_demo').sudo()
                store_client.state = vals['state']
                store_client.exp_date = vals['exp_date']

    @api.multi
    @api.onchange('template_id')
    def on_change_template(self):
        if not self.template_id:
            return
        self.currency_id = self.template_id.currency_id.id
        self.manager_id = self.template_id.manager_id.id
        self.exp_period = self.template_id.exp_period
        self.subscription_line_ids = [(6, 0, self.template_id.subscription_line_ids.ids)]

    @api.one
    def compute_client_info(self):
        registry = self.registry()
        #Update Module List Every Time
        module_list = self._get_modules_list()
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            user_count = env['res.users'].search_count([])
            product_count = env['product.template'].search_count([])
            amounts = sum(env['sale.order'].search([]).mapped('amount_total'))

            self.update({
                'no_of_users': user_count,
                'no_of_products': product_count,
                'total_sales': amounts
            })

            # store_client = env.ref('store_client.store_client_demo').sudo()
            # store_client.update({
            #     'modules_to_display': module_list,
            #     'user_limit': self.user_limit
            # })

    @api.multi
    def _get_database_size(self):
        self.ensure_one()
        self.database_size = "50 MB"
        return
        # TODO: should not be in functional field
        if self.db_name:
            registry = self.registry()
            with registry.cursor() as cr:

                cr.execute("select pg_database_size('%s')" % self.db_name)
                db_storage = cr.fetchone()[0]

            db_storage = int(db_storage / (1024*1024))
            mbsize = str(db_storage) + " MB"
            size_total = mbsize
            self.database_size = size_total

    @api.model
    def create(self, vals):
        vals['reference'] = self.env['ir.sequence'].next_by_code('store.database.list')
        if vals.get('exp_period') != 'free_trail':
            vals['state'] = 'renew'
        res = super(StoreDatabaseList, self).create(vals)
        if 'is_template_db' not in vals:
            res.create_client_params()
            if vals.get('exp_period') != 'free_trail':
                res.on_change_template()
                res._create_sale_order()
        res.create_database(template_db=res.plan_id.template_db)
        return res

    @api.multi
    def unlink(self):
        db_to_remove = self.filtered(lambda s: s.ondelete_removedb).mapped('db_name')
        res = super(StoreDatabaseList, self).unlink()
        # if store delete then delete database related to store
        for db_name in db_to_remove:
            database.exp_drop(db_name)
        return res

    @api.multi
    def _create_sale_order(self):
        self.ensure_one()
        order = self.env['sale.order'].sudo().create({
            'partner_id': self.partner_id.id,
            'store_id': self.id,
            'plan_id': self.plan_id.id,
            'order_line': [(0, 0, {'product_id': l.product_id.id, 'product_uom_qty': l.quantity, 'price_unit': l.price_unit, 'discount': l.discount}) for l in self.subscription_line_ids]
        })
        order.force_quotation_send()

    @api.multi
    def create_database(self, template_db=None, demo=False, lang='en_US'):
        self.ensure_one()
        new_db = self.db_name
        res = {}
        if new_db in database.list_dbs():
            raise UserError(_('Database Already Exist!'))
        if template_db:
            database._drop_conn(self.env.cr, template_db)
            database.exp_duplicate_database(template_db, new_db)
        else:
            # password = random_password()
            # res.update({'superuser_password': password})
            database.exp_create_database(
                new_db, demo, lang)
        if not self.is_template_db:
            self.upgrade_database({'params': True})
        _logger.info('Database created Successfully')

        return res

    @api.multi
    def upgrade_database(self, action=None):
        self.ensure_one()
        if action is None:
            action = {}

        obj = self[0]
        payload = {
            # TODO: add configure mail server option here
            'update_addons_list': (obj.update_addons_list or ''),
            'update_addons': obj.update_addons.split(',') if obj.update_addons and (obj.client_db_action == 'update_addons' or action.get('update_addons')) else [],
            'install_addons': obj.install_addons.split(',') if obj.install_addons and (obj.client_db_action == 'install_addons' or action.get('install_addons')) else [],
            'uninstall_addons': obj.uninstall_addons.split(',') if obj.uninstall_addons and (obj.client_db_action == 'uninstall_addons' or action.get('uninstall_addons')) else [],
            'access_owner_add': obj.access_owner_add.split(',') if obj.access_owner_add and (obj.client_db_action == 'access_owner_add' or action.get('access_owner_add')) else [],
            'access_remove': obj.access_remove.split(',') if obj.access_remove and (obj.client_db_action == 'access_remove' or action.get('access_remove')) else [],
            'hide_menus': obj.access_remove.split(',') if obj.access_remove and (obj.client_db_action == 'hide_menus' or action.get('access_remove')) else [],
            'params': [{'key': x.key,
                        'value': x.value,
                        'hidden': x.hidden} for x in obj.param_ids] if action.get('params') or obj.client_db_action == 'params' else [],
            }
        self.upgrade_client_database(payload)

    @api.multi
    def upgrade_client_database(self, payload):
        for record in self:
            with record.registry().cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, record._context)
                return record._upgrade_database(env, payload)

    def create_client_params(self):
        config = self.env['saas.config.param']
        config.create({'key': 'saas_client.max_users', 'value': self.max_user, 'store_id': self.id})
        config.create({'key': 'saas_client.suspended', 'value': str(self.is_suspended), 'store_id': self.id})
        #config.create({'key': 'saas_client.total_storage_limit', 'value': self.total_storage_limit or 1000, 'store_id': self.id})
        config.create({'key': 'saas_client.database.secret.key', 'value': self.db_uuid, 'store_id': self.id})
        config.create({'key': 'saas_client.client_id', 'value': self.client_id, 'store_id': self.id})
        config.create({'key': 'saas_client.verify.email', 'value': str(self.is_email_verified), 'store_id': self.id})
        config.create({'key': 'saas_client.expiration_datetime', 'value': datetime.datetime.strftime(self.exp_date, DEFAULT_SERVER_DATE_FORMAT), 'store_id': self.id})

    @api.multi
    def _upgrade_database(self, client_env, data):
        self.ensure_one()
        # "data" comes from saas_portal/models/wizard.py::upgrade_database
        post = data
        module = client_env['ir.module.module']
        _logger.info(('_upgrade_database', data))
        res = {}

        # 0. Update module list
        update_list = post.get('update_addons_list', False)
        if update_list:
            module.update_list()

        # 1. Update addons
        update_addons = post.get('update_addons', [])
        if update_addons:
            module.search([('name', 'in', update_addons)]
                          ).button_immediate_upgrade()

        # 2. Install addons
        install_addons = post.get('install_addons', [])
        if install_addons:
            module.search([('name', 'in', install_addons)]
                          ).button_immediate_install()

        # 3. Uninstall addons
        uninstall_addons = post.get('uninstall_addons', [])
        if uninstall_addons:
            module.search([('name', 'in', uninstall_addons)]
                          ).button_immediate_uninstall()

        # 5. update parameters
        params = post.get('params', [])
        for obj in params:
            if obj['key'] == 'saas_client.expiration_datetime':
                self.expiration_datetime = obj['value']
            if obj['key'] == 'saas_client.trial' and obj['value'] == 'False':
                self.trial = False
            # groups = []
            # if obj.get('hidden'):
            #     groups = ['saas_client.group_saas_support']
            client_env['ir.config_parameter'].sudo().set_param(
                obj['key'], obj['value'] or ' ')

        # 6. Access rights
        access_owner_add = post.get('access_owner_add', [])
        owner_id = client_env['res.users'].search([('is_owner', '=', True)], limit=1).id or 0
        owner_id = int(owner_id)
        if not owner_id:
            res['owner_id'] = "Owner's user is not found"
        if access_owner_add and owner_id:
            res['access_owner_add'] = []
            for g_ref in access_owner_add:
                g = client_env.ref(g_ref, raise_if_not_found=False)
                if not g:
                    res['access_owner_add'].append(
                        'group not found: %s' % g_ref)
                    continue
                print("\n????owner_id", owner_id)
                g.write({'users': [(4, owner_id, 0)]})
        access_remove = post.get('access_remove', [])
        if access_remove:
            res['access_remove'] = []
            for g_ref in access_remove:
                g = client_env.ref(g_ref, raise_if_not_found=False)
                if not g:
                    res['access_remove'].append('group not found: %s' % g_ref)
                    continue
                users = []
                for u in g.users:
                    if u.id not in (SUPERUSER_ID):
                        users.append((3, u.id, 0))
                g.write({'users': users})

        return res

    @api.multi
    def _prepare_owner_user_data(self):
        """
        Prepare the dict of values to update owner user data in client instalnce. This method may be
        overridden to implement custom values (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        owner_user_data = {
            'login': self.owner_user_id.login,
            'name': self.owner_user_id.name,
            'email': self.owner_user_id.email,
            'password': random_password(),
            'is_owner': True,
            'client_id': self.client_id,
        }
        return owner_user_data

    @api.multi
    def create_client_store(self, vals):
        self.ensure_one()
        vals.update(modules_to_display=self._get_modules_list())
        registry = self.registry()
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            res = env.ref('store_client.store_client_demo').sudo().write(vals)
            if res:
                print("\n\n?client Store Created Successfully")

    def _get_modules_list(self):
        self.ensure_one()
        Module = self.env['ir.module.module']
        for module in self.display_modules_ids:
            mods = module.upstream_dependencies(exclude_states=('uninstallable', 'to remove'))
            Module |= mods
            Module |= module
        module_list = Module.mapped('name')
        return json.dumps(module_list)

    @api.multi
    def generate_sub_code(self):
        view_id = self.env.ref('store_master.subscription_code_view_form').id
        context = self._context.copy()
        context['default_store_id'] = self.id
        return {
            'name': 'Subscription Code',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'res_model': 'subscription.code',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }

    @api.model
    def _is_valid_enterprise_code(self, store_id, enterprise_code):
        store = self.browse(store_id or 1)
        for code in store.subscription_code_ids:
            if code.code == enterprise_code and code.is_active:
                return {'valid': True, 'start_date': code.start_date, 'exp_date': code.end_date}
        return {'valid': False}

    @api.multi
    def send_mail_to_client(self, action):
        self.ensure_one()
        ICP = self.env['ir.config_parameter']
        MailTemplate = self.env['mail.template']
        if action == 'activation':
            tmpl = ICP.get_param('saas_portal.notif_store_create_tmpl')
            if tmpl:
                MailTemplate.browse(tmpl).send_mail(self.id, force_send=True, raise_exception=False)
        elif action == 'payment':
            tmpl = ICP.get_param('saas_portal.payment_tmpl')
            if tmpl:
                MailTemplate.browse(tmpl).send_mail(self.id, force_send=True, raise_exception=False)
        elif action == 'validity_extend':
            tmpl = ICP.get_param('saas_portal.notif_store_validity_extend_tmpl')
            if tmpl:
                MailTemplate.browse(tmpl).send_mail(self.id, force_send=True, raise_exception=False)
        elif action == 'plan_change':
            tmpl = ICP.get_param('saas_portal.plan_change_tmpl')
            if tmpl:
                MailTemplate.browse(tmpl).send_mail(self.id, force_send=True, raise_exception=False)
        elif action == 'extend_yourr_store_validity':
            tmpl = ICP.get_param('saas_portal.notif_before_store_expire_tmpl')
            if tmpl:
                MailTemplate.browse(tmpl).send_mail(self.partner_id.id, force_send=True, raise_exception=False)
        elif action == '5_day_after_expire':
            tmpl = ICP.get_param('saas_portal.notif_after_store_expire_tmpl')
            if tmpl:
                MailTemplate.browse(tmpl).send_mail(self.partner_id.id, force_send=True, raise_exception=False)

    @api.model
    def store_expire_notification(self, cron_mode=True):
        today = datetime.date.today()
        remaining_7_days = self.search([('exp_date', '=', (today + datetime.timedelta(days=8)).strftime('%Y-%m-%d'))])
        remaining_2_days = self.search([('exp_date', '=', (today + datetime.timedelta(days=3)).strftime('%Y-%m-%d'))])
        today_expire = self.search([('exp_date', '=', today.strftime('%Y-%m-%d'))])

        if remaining_7_days:
            remaining_7_days.send_mail_to_client(action='extend_yourr_store_validity')
        elif remaining_2_days:
            remaining_2_days.send_mail_to_client(action='extend_yourr_store_validity')
        elif today_expire:
            today_expire.send_mail_to_client(action='extend_yourr_store_validity')

    @api.multi
    def send_activation_mail(self):
        self.ensure_one()
        tmpl = self.env['ir.values'].get_default('store.config.settings', 'notif_email_verification_tmpl')
        if tmpl:
            tmpl = self.env['mail.template'].browse(tmpl)
            tmpl.send_mail(self.id, force_send=True, raise_exception=False)

    @api.model
    def make_archive_store(self):
        domain = [('store_exp_date_verify', '<=', fields.Datetime.now()), ('is_email_verified', '=', False)]
        stores = self.search(domain)
        stores.remove_store()

    @api.multi
    def remove_store(self):
        return
        for store in self:
            odoo.service.db.exp_drop(store.db_name)
        partners = self.mapped('partner_id')
        users = partners.mapped('user_ids')
        users.unlink()
        if partners:
            partners.write({'active': False})  # partners.active = False
        self.unlink()

    def get_expire_date(self):
        dt = fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(self.store_exp_date_verify)))

        return dt

    @api.multi
    def extend_store_validity(self):
        self.ensure_one()
        start_date = self.exp_date
        exp_date = ''
        if self.exp_period == 'monthly':
            exp_date = start_date + relativedelta(months=+1)
        if self.exp_period == 'quaterly':
            exp_date = start_date + relativedelta(months=+3)
        if self.exp_period == 'half-yearly':
            exp_date = start_date + relativedelta(months=+6)
        if self.exp_period == 'yearly':
            exp_date = start_date + relativedelta(months=+12)
        self.write({'state': 'in_progress', 'need_payment': False, 'exp_date': exp_date, 'start_date': start_date})


class StoreSubscriptionLine(models.Model):
    _name = 'store.subscription.line'
    _description = 'Subscription Line'

    name = fields.Text(string='Description')
    product_id = fields.Many2one('product.product', 'Product', required=True)
    quantity = fields.Float(string="Quantity")
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    price_unit = fields.Float('Unit Price', required=True)
    discount = fields.Float('Discount (%)')
    price_subtotal = fields.Float(compute='_amount_line', string='Sub Total')
    store_id = fields.Many2one('store.database.list', string="Store")
    store_tmpl_id = fields.Many2one('store.template', string="Store Template")

    @api.multi
    def _amount_line(self):
        for line in self:
            line.price_subtotal = line.quantity * line.price_unit * (100.0 - line.discount) / 100.0

    # def update_client_subscription_line(self, vals):
    #     registry = self.store_id.registry()
    #     with registry.cursor() as cr:
    #         env = api.Environment(cr, SUPERUSER_ID, {})
    #         store = env.ref('store_client.store_client_demo').sudo()
    #         vals.update(store_id=store.id)
    #         env['store.subscription.line'].sudo().create(vals)


class StoreSubscriptionLineOption(models.Model):
    _inherit = 'store.subscription.line'
    _name = 'store.subscription.line.option'

    portal_access = fields.Selection(
        string='Portal Access',
        selection=[
            ('invisible', 'Invisible'),
            ('none', 'Restricted'),
            ('upgrade', 'Upgrade only'),
            ('both', 'Upgrade and Downgrade')],
        required=True,
        default='none',
        help="Restricted: The customer must ask a Sales Rep to add or remove this option\n"
             "Upgrade Only: The customer can add the option himself but must ask to remove it\n"
             "Upgrade and Downgrade: The customer can add or remove this option himself\n"
             "Invisible: The customer doesn't see the option; however it gets carried away when switching subscription template")


class SubscriptionCode(models.Model):
    _name = 'subscription.code'
    _description = 'Subscription Code'

    name = fields.Char(string="Subscrrption Name")
    store_id = fields.Many2one('store.database.list', string="Store")
    start_date = fields.Date(string="Valid From")
    end_date = fields.Date(string="Valid To")
    code = fields.Char(string="Subscription Code", default=lambda s: uuid.uuid4())
    is_active = fields.Boolean(compute='_is_code_valid', string="Is Active")

    @api.multi
    def _is_code_valid(self):
        for sc in self:
            if sc.end_date >= time.strftime('%Y-%m-%d'):
                sc.is_active = True

    @api.multi
    def confirm_code(self):
        return True


class SaasConfigParam(models.Model):
    _name = 'saas.config.param'
    _description = 'Saas Config Paramters'

    def _get_keys(self):
        return [
            # this parameter is obsolete.Use access_limit_records_number module
            ('saas_client.max_users', 'Max Users (obsolete)'),
            ('saas_client.suspended', 'Suspended'),
            ('saas_client.total_storage_limit', 'Total storage limit'),
            ('saas_client.database.secret.key', 'DB Secret Key'),
            ('saas_client.expiration_datetime', 'DB Expire Date'),
            ('saas_client.client_id', 'Client ID'),
            ('saas_client.verify.email', 'Email Varified?')
        ]

    key = fields.Selection(selection=_get_keys,
                           string='Key', required=1, size=64)
    value = fields.Char('Value', required=1, size=64)
    store_id = fields.Many2one('store.database.list', 'Config')
    hidden = fields.Boolean('Hidden parameter', default=True)
