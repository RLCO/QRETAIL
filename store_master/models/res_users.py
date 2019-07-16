# -*- coding: utf-8 -*-
from odoo import models, api, SUPERUSER_ID


class ResUsers(models.Model):
    _inherit = 'res.users'

    def signup(self, cr, uid, values, token=None, context=None):
        """ signup a user, to either:
            - create a new user (no token), or
            - create a user for a partner (with token, but no user for partner), or
            - change the password of a user (with token, and existing user).
            :param values: a dictionary with field values that are written on user
            :param token: signup token (optional)
            :return: (dbname, login, password) for the signed up user
        """
        if token:
            # signup with a token: find the corresponding partner id
            res_partner = self.pool.get('res.partner')
            partner = res_partner._signup_retrieve_partner(
                            cr, uid, token, check_validity=True, raise_exception=False, context=None)
            # invalidate signup token
            partner.write({'signup_token': False, 'signup_type': False, 'signup_expiration': False})

            partner_user = partner.user_ids and partner.user_ids[0] or False

            # avoid overwriting existing (presumably correct) values with geolocation data
            if partner.country_id or partner.zip or partner.city:
                values.pop('city', None)
                values.pop('country_id', None)
            if partner.lang:
                values.pop('lang', None)

            if partner_user:
                # user exists, modify it according to values
                values.pop('login', None)
                values.pop('name', None)
                partner_user.write(values)
                return (cr.dbname, partner_user.login, values.get('password'))
            else:
                # user does not exist: sign up invited user
                values.update({
                    'name': partner.name,
                    'partner_id': partner.id,
                    'email': values.get('email') or values.get('login'),
                })
                if partner.company_id:
                    values['company_id'] = partner.company_id.id
                    values['company_ids'] = [(6, 0, [partner.company_id.id])]
                self._signup_create_user(cr, uid, values, context=context)
        else:
            # no token, sign up an external user
            values['email'] = values.get('email') or values.get('login')
            is_seller = values.pop('is_seller', False)
            uid = self._signup_create_user(cr, uid, values, context=context)
            if uid and is_seller:
                partner = self.pool['res.users'].browse(cr, SUPERUSER_ID, uid, context=context).partner_id
                partner.write({'is_merchant': True})

        return (cr.dbname, values.get('login'), values.get('password'))

    # @api.multi
    # def write(self, vals):
    #     res = super(ResUsers, self).write(vals)
    #     if ('login' in vals or 'password' in vals) and not self.env.context.get('no_update'):
    #         for user in self.filtered(lambda u: u.partner_id.is_store_owner):
    #             store = self.env['store.database.list'].search([('partner_id', '=', user.partner_id.id)], limit=1)
    #             if store:
    #                 registry = store.registry()
    #                 with registry.cursor() as cr:
    #                     env = api.Environment(cr, SUPERUSER_ID, {})
    #                     user = env['res.users'].with_context(no_update=True).browse(SUPERUSER_ID)
    #                     if vals.get('login'):
    #                         user.login = vals['login']
    #                     if vals.get('password'):
    #                         user.password = vals['password']
    #     return res
