# -*- coding: utf-8 -*-
import odoo
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.service import db
from odoo.exceptions import UserError


class SaasPlan(models.Model):
    _name = 'saas.plan'
    _description = 'Saas Plan'

    name = fields.Char(required=True)
    module_ids = fields.One2many('service.type.module', 'service_type', string="Apps")
    template_db = fields.Char(string="Template Database")
    color = fields.Integer()
    store_all_count = fields.Integer(compute='_count_all')
    store_renew_count = fields.Integer(compute='_count_all')
    store_inprogress_count = fields.Integer(compute='_count_all')
    store_expire_count = fields.Integer(compute='_count_all')
    display_modules_ids = fields.Many2many('ir.module.module', string='Modules Visible to Clients')
    demo = fields.Boolean('Install Demo Data')
    maximum_allowed_dbs_per_partner = fields.Integer(
        help='maximum allowed non-trial databases per customer', require=True, default=0)
    maximum_allowed_trial_dbs_per_partner = fields.Integer(
        help='maximum allowed trial databases per customer', require=True, default=0)

    max_users = fields.Char('Initial Max users',
                            default='0', help='leave 0 for no limit')
    total_storage_limit = fields.Integer(
        'Total storage limit (MB)', help='leave 0 for no limit')
    block_on_expiration = fields.Boolean(
        'Block clients on expiration', default=False)
    block_on_storage_exceed = fields.Boolean(
        'Block clients on storage exceed', default=False)
    description = fields.Html(string='Plan Description')

    @api.multi
    def _count_all(self):
        Store = self.env['store.database.list']
        for service in self:
            service.store_all_count = Store.search_count([('service_id', '=', service.id)])
            service.store_renew_count = Store.search_count([('service_id', '=', service.id), ('state', '=', 'renew')])
            service.store_inprogress_count = Store.search_count([('service_id', '=', service.id), ('state', '=', 'in_progress')])
            service.store_expire_count = Store.search_count([('service_id', '=', service.id), ('state', '=', 'close')])

    @api.model
    def create(self, vals):
        res = super(SaasPlan, self).create(vals)
        datas = {
            'db_name': vals.get('template_db'),
            'partner_id': self.env.user.partner_id.id,
            'is_template_db': True,
            'name': res.name,
        }
        self.env['store.database.list'].create(datas)
        return res

    def registry(self, db, new=False, **kwargs):
        m = odoo.modules.registry.Registry
        return m.new(db, **kwargs)


class ServiceTypeModule(models.Model):
    _name = 'service.type.module'

    service_type = fields.Many2one('crm.team', string="Service Type")
    module_id = fields.Many2one('ir.module.module', string="Module", required=True)
    state = fields.Selection(related="module_id.state", string="State", readonly=True)
    description = fields.Char(related="module_id.summary", string="Description", readonly=True)
    to_install = fields.Boolean('To install', help="Checked if you want to installe the module in Demo Database of service type")

    @api.onchange('module_id')
    def onchange_module_id(self):
        if self.module_id.dependencies_id:
            name = ''
            for module in self.module_id.dependencies_id:
                name += module.name + '\n'
            raise Warning(_('The following module will automatically installed if you install this module. \n%s') % name)
