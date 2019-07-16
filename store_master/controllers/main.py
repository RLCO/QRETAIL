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
import uuid
from datetime import date
from dateutil.relativedelta import relativedelta
import random

import odoo
from odoo import api, http, SUPERUSER_ID, _
from odoo.http import request
from werkzeug.exceptions import NotFound
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.tools import config
from odoo.addons.website.controllers.main import Website
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
#import openerp.addons.auth_signup.controllers.main


def random_password():
    # the passaword has an entropy of about 120 bits (6 bits/char * 20 chars)
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    return ''.join(random.SystemRandom().choice(chars) for i in xrange(20))


class StoreMaster(http.Controller):

    @http.route(['/shop/client/<model("res.partner"):partner>/info/send'], type='http', auth="public", website=True, methods=['POST'])
    def send_client_info(self, partner=False, **post):
        if partner:
            partner.send_contact_info_email()
        return request.redirect('/')

    def _prepare_data(self, data):
        plan = request.env['saas.plan'].sudo().search([('template_db', '=', data.get('plan_id'))], limit=1)
        return {
            'name': data.get('store_name'),
            'db_name': data.get('store_name'),
            'exp_period': data.get('exp_period'),
            'partner_id': data.get('partner_id'),
            'plan_id': plan.id,
            #'display_modules_ids': [(4, m_id) for m_id in service.display_modules_ids.ids],
            'max_user': plan.max_users,
            'exp_date': self._get_expire_date(data.get('exp_period')),
            'template_id': request.env['store.template'].sudo().search([('exp_period', '=', data.get('exp_period'))], limit=1).id,
            'owner_user_id': data.get('user_id'),
        }

    def _prepare_client_store_data(self, data):
        return {
            'name': data.get('store_name'),
            'db_name': data.get('store_name'),
            'exp_period': data.get('exp_period'),
            'exp_date': self._get_expire_date(data.get('exp_period')),
        }

    def _get_db_to_duplicate(self, service_type):
        st = request.env['crm.team'].sudo().search([('service_type', '=', service_type)], limit=1)
        return st.demo_database

    def _get_expire_date(self, period='free_trail'):

        # Free Trial Database will be expire in 15 Days
        if period == 'free_trail':
            free_days = request.env['ir.config_parameter'].sudo().get_param('saas_port.free_trial_days') or 15
            exp_date = date.today() + relativedelta(days=+int(free_days))
            return exp_date.strftime('%Y-%m-%d')

        return date.today().strftime('%Y-%m-%d')

    @http.route(['/store/create'], type='http', auth="public", website=True)
    def store_creation(self, **post):
        return request.render('store_master.store_create')

    @http.route(['/check/client/exist'], type='json', auth="public", website=True)
    def check_client_exist(self, email, store, **post):
        store = store in http.db_list()
        user = request.env['res.users'].sudo().search_count([('login', '=', email)])
        return {'store': store, 'user': user}

    @http.route(['/client/database/create'], type='http', auth="public", website=True, mthods=['POST'])
    def create_client_database(self, **post):
        dbname = post.get('store_name', False)
        token = uuid.uuid4().hex
        values = {
            'name': post.get('email'),
            'email': post.get('email'),
            'is_store_owner': True,
        }
        partner = request.env['res.partner'].sudo().create(values)

        #create a portal user in
        post.update(partner_id=partner.id)

        values = {
            'login': post.get('email'),
            'email': post.get('email'),
            'password': post.get('password') or random_password(),
            'partner_id': partner.id
        }
        user = request.env['res.users'].sudo()._signup_create_user(values)
        post['user_id'] = user.id
        vals = self._prepare_data(post)
        dbl = request.env['store.database.list'].sudo().create(vals)
        registry = dbl.registry()

        with registry.cursor() as cr:
            client_env = api.Environment(cr, SUPERUSER_ID, {})
            user = client_env['res.users']
            owner_data = dbl._prepare_owner_user_data()
            owner_data.update(
                action_id=client_env.ref('pos_dashboard.pos_dashboard_action').id,
                password=values['password'],
                groups_id=[(4, client_env.ref('base.group_system').id, 0), (4, client_env.ref('point_of_sale.group_pos_manager').id, 0)]
            )
            user.create(owner_data)
            store_url = "http://%s:%s" % (dbname, config.get('xmlrpc_port'))
            user.company_id.sudo().write({'store_url': store_url})
            cr.commit()

        if vals.get('exp_period') != 'free_trail':
            request.env.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
            request.session.authenticate(request.session.db, post.get('email'), post.get('password'))
            return request.redirect('/my/store/contract/'+str(dbl.id)+'/'+dbl.client_id + '?store_create=True')
        dbl.send_mail_to_client('activation')
        url = 'http://' + dbl.db_name + ':8069'
        return request.redirect(url)
        return request.render('store_master.store_create_success', {'store': dbl, 'token': token, 'login': post.get('email')})
        #return request.render('store_master.store_create_failure')

    @http.route(['/shop/email/verfication'], type='http', auth="public", website=True)
    def verifiy_email_address(self, store_code, activation_code, **post):
        if not store_code or not activation_code:
            raise NotFound()
        store = request.env['store.database.list'].sudo().search([('uuid', '=', store_code)], limit=1)
        if store and store.activation_code == activation_code:
            store.is_email_verified = True
            registry = store.registry()
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                config = env['ir.config_parameter'].sudo()
                configs = config.search([('key', '=', 'verify.email')])
                configs.write({'value': 'verified'})
                url = 'http://'+store.db_name+'.ezeselling.com'
                return request.redirect(url)
        else:
            raise NotFound()


class AuthSignupHomeStore(odoo.addons.web.controllers.main.Home):

    def get_auth_signup_qcontext(self):
        res = super(AuthSignupHomeStore, self).get_auth_signup_qcontext()
        term_and_condition = request.env['ir.values'].get_default('seller.config.settings', 'term_condition')
        res.update(terms=term_and_condition)
        return res

    def do_signup(self, qcontext):
        """ Shared helper that creates a res.partner out of a token """
        values = dict((key, qcontext.get(key)) for key in ('login', 'name', 'password', 'is_seller'))
        assert any([k for k in values.values()]), "The form was not properly filled in."
        assert values.get('password') == qcontext.get('confirm_password'), "Passwords do not match; please retype them."
        supported_langs = [lang['code'] for lang in request.registry['res.lang'].search_read(request.cr, openerp.SUPERUSER_ID, [], ['code'])]
        if request.lang in supported_langs:
            values['lang'] = request.lang
        self._signup_with_values(qcontext.get('token'), values)
        request.cr.commit()


class StoreContract(http.Controller):

    @http.route(['/my/store'], type='http', auth="user", website=True)
    def my_store(self, **kw):
        store = request.env['store.database.list'].sudo().search([('partner_id', '=', request.env.user.partner_id.id)], limit=1)
        return request.render("store_master.portal_my_store", {'store': store, 'user': request.env.user})

    @http.route(['/my/store/contract/<int:store_id>/',
                 '/my/store/contract/<int:store_id>/<string:uuid>',
                 '/my/store/contract/<int:store_id>/<string:uuid>/<string:order_id>'], type='http', auth="user", website=True)
    def store_contract(self, store_id, uuid='', order_id=False, tx_id=False, **kw):
        store_obj = request.env['store.database.list']
        if uuid:
            store = store_obj.sudo().browse(store_id)
            if uuid != store.client_id or store.state == 'cancelled':
                raise NotFound()
            if request.uid == store.partner_id.user_id.id:
                store = store_obj.browse(store_id)
        else:
            store = store_obj.browse(store_id)

        values = {}
        values['acquirers'] = list(request.env['payment.acquirer'].sudo().search([('website_published', '=', True)]))
        extra_context = {
            'submit_class': 'btn btn-primary',
            'submit_txt': _('Pay & Confirm')
        }
        values['buttons'] = {}
        for acquirer in values['acquirers']:
            values['buttons'][acquirer.id] = acquirer.with_context(**extra_context).render(
                '/',
                store.recurring_total,
                store.currency_id.id,
                values={
                    'return_url': '/store/%s/%s' % (store.id, uuid) if uuid else '/store/%s' % store.id,
                    'type': 'form',
                    'alias_usage': _('If we store your payment information on our server, subscription payments will be made automatically.'),
                    'partner_id': store.partner_id.id,
                })

        values['store'] = store
        values['user'] = request.env.user
        values['is_store_create'] = kw.get('store_create') and True or False
        values['last_orders'] = request.env['sale.order'].sudo().search([('store_id', '=', store.id)])
        values['order_id'] = order_id or request.env['sale.order'].sudo().search([('store_id', '=', store.id), ('state', 'in', ['draft', 'sent'])], limit=1).id or False
        if tx_id:
            tx = request.env['payment.transaction'].sudo().browse(tx_id)
            values['tx'] = tx
            # if payment is succesfull then extend the expire date of the database
            if tx.state == 'done' and store.exp_period != 'free_trail':
                store.extend_store_validity()
                store.sudo().on_change_expire_date()
                store.send_mail_to_client('payment')

        return request.render("store_master.store_contract", values)

    # note dbo: website_sale code
    @http.route(['/store/<int:store_id>/transaction/<int:acquirer_id>'], type='json', auth="public", website=True)
    def payment_transaction(self, acquirer_id, store_id):
        return self.payment_transaction_token(acquirer_id, store_id, None)

    @http.route(['/store/<int:store_id>/transaction/<int:acquirer_id>/<token>'], type='json', auth="public", website=True)
    def payment_transaction_token(self, acquirer_id, store_id, token):
        """ Json method that creates a payment.transaction, used to create a
        transaction when the user clicks on 'pay now' button. After having
        created the transaction, the event continues and the user is redirected
        to the acquirer website.

        :param int acquirer_id: id of a payment.acquirer record. If not set the
                                user is redirected to the checkout page
        """
        PaymentTransaction = request.env['payment.transaction'].sudo()
        Store = request.env['store.database.list'].sudo().browse(store_id)
        if not Store or acquirer_id is None:
            return request.redirect("/store/%s" % Store.id)

        Order = request.env['sale.order'].sudo().search([('store_id', '=', Store.id), ('state', 'in', ['draft', 'sent'])], limit=1)

        # find an already existing transaction
        Transaction = PaymentTransaction.sudo().search([('reference', '=', Order.name)])
        if Transaction:
            if Transaction.sale_order_id != Order or Transaction.state in ['error', 'cancel'] or Transaction.acquirer_id.id != acquirer_id:
                Transaction = False
            elif Transaction.state == 'draft':
                Transaction.write({
                    'amount': Order.amount_total,
                })
        if not Transaction:
            vals = {
                'acquirer_id': acquirer_id,
                'type': 'form',
                'amount': Order.amount_total,
                'currency_id': Order.pricelist_id.currency_id.id,
                'partner_id': Order.partner_id.id,
                'partner_country_id': Order.partner_id.country_id.id,
                'reference': PaymentTransaction.get_next_reference(Order.name),
                'sale_order_id': Order.id,
                'store_id': store_id,
            }
            Transaction = PaymentTransaction.sudo().create(vals)
            request.session['store_%s_transaction_id' % Order.id] = Transaction.id
            self._create_client_transaction(Store, {
                'name': vals['reference'],
                'payment_method': Transaction.reference,
                'state': Transaction.state,
                'partner_name': Order.partner_id.name,
                'amount': Order.amount_total
                })
            # update quotation
            Order.write({
                'payment_acquirer_id': acquirer_id,
                'payment_tx_id': Transaction.id
            })

        # confirm the quotation
        if Transaction.acquirer_id.auto_confirm == 'at_pay_now':
            Order.sudo().with_context(send_email=True).action_confirm()
        return Transaction.acquirer_id.with_context(
            submit_class='btn btn-primary',
            submit_txt=_('Pay & Confirm')).render(
            Transaction.reference,
            Order.amount_total,
            Order.pricelist_id.currency_id.id,
            values={
                'return_url': '/store/contract/payment/%s/%s/%s' % (Transaction.id, store_id, token),
                'type': 'form',
                'alias_usage': _('If we store your payment information on our server, subscription payments will be made automatically.'),
                'partner_id': Order.partner_shipping_id.id or Order.partner_invoice_id.id,
                'billing_partner_id': Order.partner_invoice_id.id,
            })

    def _create_client_transaction(self, store, vals):
        registry = store.registry()
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            store_id = env['store.master'].search([('db_name', '=', store.db_name)], limit=1)
            vals.update(store_id=store_id.id)
            env['store.payment.transaction'].sudo().create(vals)

    @http.route(['/store/contract/payment/<int:tx_id>/<int:store_id>/<string:uuid>', '/store/contract/payment/<int:store_id>/<string:uuid>'], type='http', auth="public", website=True)
    def store_contract_payment(self, tx_id=False, store_id=False, uuid=False, **kw):
        if not tx_id:
            order = request.env['sale.order'].sudo().search([('store_id', '=', store_id), ('state', 'not in', ['done'])], order="id desc", limit=1)
            tx_id = order.payment_tx_id.id
        return self.store_contract(store_id, uuid, False, tx_id, **kw)

    @http.route(['/my/store/contract/change/<int:store_id>/<string:uuid>'], type='http', auth="public", website=True)
    def change_store_contract(self, store_id, uuid=None, **kw):
        store_obj = request.env['store.database.list']
        if uuid:
            store = store_obj.sudo().browse(store_id)
            if uuid != store.client_id or store.state == 'cancelled':
                raise NotFound()
            if request.uid == store.partner_id.user_id.id:
                store = store_obj.browse(store_id)
        else:
            store = store_obj.browse(store_id)
        if kw.get('new_template_id'):
            new_template_id = int(kw.get('new_template_id'))
            msg_before = [store.sudo().template_id.name,
                          str(store.recurring_total),
                          str(store.exp_period)]

            store.sudo().write({'template_id': new_template_id, 'state': 'renew',  'need_payment': True})
            store.on_change_template()
            msg_after = [store.sudo().template_id.name,
                         str(store.recurring_total),
                         str(store.exp_period)]

            msg_body = request.env['ir.ui.view'].render_template(['store_master.chatter_change_contract'],
                                                             values={'msg_before': msg_before, 'msg_after': msg_after})
            store.message_post(body=msg_body)
            store.send_mail_to_client('plan_change')
            self._update_order(store)
            Order = request.env['sale.order'].sudo().search([('store_id', '=', store.id), ('state', 'in', ['draft', 'sent'])], limit=1)
            return request.redirect('/my/store/contract/%s/%s/%s' % (store.id, store.client_id, Order.id))

        domain = [('allow_online', '=', True)]
        if store.exp_period != 'free_trial':
            domain += [('plan_id', 'in', [store.plan_id.id, False])]
        store_templates = request.env['store.template'].sudo().search([('allow_online', '=', True)])
        if store.exp_period != 'free_trial':
            store_templates = store_templates.filtered(lambda s: s.exp_period != 'free_trail')
        values = {
            'store': store,
            'store_templates': store_templates.filtered(lambda t: t.id != store.template_id.id),
            'user': request.env.user,
        }
        return request.render("store_master.store_template", values)

    def _update_order(self, Store):
        #search if already Exist or not
        Order = request.env['sale.order'].sudo().search([('store_id', '=', Store.id), ('state', 'in', ['draft', 'sent'])], limit=1)
        if not Order:
            Order = request.env['sale.order'].sudo().create({
                    'partner_id': Store.partner_id.id,
                    'store_id': Store.id,
                    'plan_id': Store.plan_id.id,
                    'order_line': [(0, 0, {'product_id': l.product_id.id, 'product_uom_qty': l.quantity, 'price_unit': l.price_unit, 'discount': l.discount}) for l in Store.subscription_line_ids]
                })
            Order.force_quotation_send()
        else:
            Order.order_line.unlink()
            Order.order_line = [(0, 0, {'product_id': l.product_id.id, 'product_uom_qty': l.quantity, 'price_unit': l.price_unit, 'discount': l.discount}) for l in Store.subscription_line_ids]


class Website(Website):

    @http.route(['/typo'], type='http', auth="public", website=True)
    def typo(self, **post):
        return request.render('store_master.store_domain_not_found1')


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        Store = request.env['store.database.list']
        store_count = Store.sudo().search_count([
            ('partner_id', '=', partner.id)])

        values.update({
            'store_count': store_count,
        })
        return values

    @http.route(['/my/stores', '/my/stores/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_stores(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        partner = request.env.user.partner_id
        Store = request.env['store.database.list'].sudo()

        domain = [
            ('partner_id', '=', partner.id)
        ]

        # count for pager
        store_count = Store.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/stores",
            total=store_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        stores = Store.search(domain, limit=self._items_per_page, offset=pager['offset'])

        values = {
            'stores': stores.sudo(),
            'page_name': 'Retail Store',
            'pager': pager,
            'default_url': '/my/stores',
        }
        return request.render("store_master.portal_my_store", values)
