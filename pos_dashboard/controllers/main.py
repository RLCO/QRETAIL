# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import calendar

from odoo import http, fields
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class WebSettingsDashboard(http.Controller):

    @http.route('/pos_dashboard/data', type='json', auth='user')
    def pos_dashboard_data(self, filter_condition=None, **kw):
        if not request.env.user.has_group('point_of_sale.group_pos_manager'):
            raise AccessError("Access Denied")

        pos_dom = []
        if filter_condition.get('pos_filter'):
            pos_dom += [('config_id', '=', filter_condition.pop('pos_filter'))]

        domain = self._prepare_order_domain(filter_condition)

        orders = self._get_orders(domain + pos_dom)
        new_customer = self._get_new_customer(domain)
        repeat_customer = self._get_repeat_customer(domain, orders)
        total_transaction = self._get_total_transactions(orders)
        sales_data = self._prepare_sales(orders, pos_dom)
        top_item = self._prepare_top_item(orders)
        sales_by_payment_method = self._get_sales_by_payment_method(orders)
        sales_by_hour = self._get_sales_by_hour(orders)

        res = {
            'custome': {
                'new_customer': new_customer,
                'repeat_customer': repeat_customer,
                'total_sales': sales_data.get('total_sales'),
                'total_transaction': total_transaction,
            },
            'pos_gage': {
                'total_sales': sales_data.get('total_sales'),
                'sales_by_pos': sales_data.get('sales_by_pos'),
                'sales_target': sales_data.get('sales_target'),
            },
            'top_item': {
                'top_product': top_item.get('top_product'),
                'top_cat': top_item.get('top_cat'),
            },
            'payment_method': sales_by_payment_method,
            'sales_by_hour': sales_by_hour,
        }
        return res

    def _get_sales_by_payment_method(self, orders):
        methods = request.env['account.journal'].search([('journal_user', '=', True)])
        data = {}
        for m in methods:
            data[m.id] = [m.name, 0]

        for o in orders:
            for st in o.statement_ids:
                amount = round(st.amount)
                data[st.statement_id.journal_id.id][1] += amount
        temp = sorted(data.items(), key=lambda e: e[1][1], reverse=True)
        return temp

    def _get_orders(self, domain):
        return request.env['pos.order'].search(domain)

    def _get_new_customer(self, domain):
        if domain:
            domain = [('create_date', '>=', domain[0][2]), ('create_date', '<=', domain[1][2])]
        return request.env['res.partner'].search_count(domain)

    def _get_repeat_customer(self, domain, orders):
        if domain:
            domain = [('create_date', '>=', domain[0][2]), ('create_date', '<=', domain[1][2])]
        repeat_customer = 0
        for o in orders:
            if o.partner_id and o.partner_id and o.partner_id.create_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT) <= domain[0][2]:
                repeat_customer += 1
        return repeat_customer

    def _get_total_transactions(self, orders):
        return len(orders)

    def _prepare_sales(self, orders, pos_dom):
        data = {
            'total_sales': 0,
            'sales_by_pos': {},
            'sales_target': 0
        }
        pos = request.env['pos.config'].search([])
        for p in pos:
            data['sales_by_pos'][p.id] = [p.name, 0, p.stock_location_id.display_name]
            if pos_dom and p.id == pos_dom[0][2]:
                data['sales_target'] += p.target_for_today
            if not pos_dom:
                data['sales_target'] += p.target_for_today

        total = 0
        for o in orders:
            amount = round(o.amount_total)
            data['sales_by_pos'][o.config_id.id][1] += amount
            total += amount
        data['total_sales'] = total
        temp = sorted(data['sales_by_pos'].items(), key=lambda e: e[1][1], reverse=True)
        data['sales_by_pos'] = temp
        return data

    def _prepare_top_item(self, orders):
        data = {
            'top_product': {},
            'top_cat': {}
        }
        lines = request.env['pos.order.line'].search([('order_id', 'in', orders.ids)])
        for line in lines:
            amount = round(line.price_subtotal)
            if not data['top_product'].get(line.product_id.id):
                data['top_product'][line.product_id.id] = [line.product_id.name, amount, line.product_id.default_code]
            else:
                data['top_product'][line.product_id.id][1] += amount

            if not data['top_cat'].get(line.product_id.pos_categ_id.id):
                data['top_cat'][line.product_id.pos_categ_id.id] = [line.product_id.pos_categ_id.display_name, amount]
            else:
                data['top_cat'][line.product_id.pos_categ_id.id][1] += amount

        temp_product = data['top_product']
        temp_cat = data['top_cat']
        temp_product = sorted(temp_product.items(), key=lambda e: e[1][1], reverse=True)
        temp_cat = sorted(temp_cat.items(), key=lambda e: e[1][1], reverse=True)
        data['top_product'] = temp_product
        data['top_cat'] = temp_cat

        return data

    def _get_sales_by_hour(self, orders):

        graph_data = [
            {'label': '0-1A', 'value': 0},
            {'label': '1-2A', 'value': 0},
            {'label': '2-3A', 'value': 0},
            {'label': '3-4A', 'value': 0},
            {'label': '4-5A', 'value': 0},
            {'label': '5-6A', 'value': 0},
            {'label': '6-7A', 'value': 0},
            {'label': '7-8A', 'value': 0},
            {'label': '8-9A', 'value': 0},
            {'label': '9-10A', 'value': 0},
            {'label': '10-11A', 'value': 0},
            {'label': '11-12A', 'value': 0},
            {'label': '0-1P', 'value': 0},
            {'label': '1-2P', 'value': 0},
            {'label': '2-3P', 'value': 0},
            {'label': '3-4P', 'value': 0},
            {'label': '4-5P', 'value': 0},
            {'label': '5-6P', 'value': 0},
            {'label': '6-7P', 'value': 0},
            {'label': '7-8P', 'value': 0},
            {'label': '8-9P', 'value': 0},
            {'label': '9-10P', 'value': 0},
            {'label': '10-11P', 'value': 0},
            {'label': '11-12P', 'value': 0}
        ]
        values = {
            '0-1A': 0,
            '1-2A': 0,
            '2-3A': 0,
            '3-4A': 0,
            '4-5A': 0,
            '5-6A': 0,
            '6-7A': 0,
            '7-8A': 0,
            '8-9A': 0,
            '9-10A': 0,
            '10-11A': 0,
            '11-12A': 0,
            '0-1P': 0,
            '1-2P': 0,
            '2-3P': 0,
            '3-4P': 0,
            '4-5P': 0,
            '5-6P': 0,
            '6-7P': 0,
            '7-8P': 0,
            '8-9P': 0,
            '9-10P': 0,
            '10-11P': 0,
            '11-12P': 0
        }

        for o in orders:
            date = o._convert_date_to_user_tz()
            date = date[11:]
            amount = round(o.amount_total)

            if date >= '00:00:00' and date <= "00:59:59":
                values['0-1A'] = values['0-1A'] + amount

            elif date >= '01:00:00' and date <= "01:59:59":
                values['1-2A'] = values['1-2A'] + amount

            elif date >= '02:00:00' and date <= "02:59:59":
                values['2-3A'] = values['2-3A'] + amount

            elif date >= '03:00:00' and date <= "03:59:59":
                values['3-4A'] = values['3-4A'] + amount

            elif date >= '04:00:00' and date <= "04:59:59":
                values['4-5A'] = values['4-5A'] + amount

            elif date >= '05:00:00' and date <= "05:59:59":
                values['5-6A'] = values['5-6A'] + amount

            elif date >= '06:00:00' and date <= "06:59:59":
                values['6-7A'] = values['6-7A'] + amount

            elif date >= '07:00:00' and date <= "07:59:59":
                values['7-8A'] = values['7-8A'] + amount

            elif date >= '08:00:00' and date <= "08:59:59":
                values['8-9A'] = values['8-9A'] + amount

            elif date >= '09:00:00' and date <= "09:59:59":
                values['9-10A'] = values['9-10A'] + amount

            elif date >= '10:00:00' and date <= "10:59:59":
                values['10-11A'] = values['10-11A'] + amount

            elif date >= '11:00:00' and date <= "11:59:59":
                values['10-12A'] = values['11-12A'] + amount

            elif date >= '12:00:00' and date <= "12:59:59":
                values['0-1P'] = values['0-1P'] + amount

            elif date >= '13:00:00' and date <= "13:59:59":
                values['1-2P'] = values['1-2P'] + amount

            elif date >= '14:00:00' and date <= "14:59:59":
                values['2-3P'] = values['2-3P'] + amount

            elif date >= '15:00:00' and date <= "15:59:59":
                values['3-4P'] = values['3-4P'] + amount

            elif date >= '16:00:00' and date <= "16:59:59":
                values['4-5P'] = values['4-5P'] + amount

            elif date >= '17:00:00' and date <= "17:59:59":
                values['5-6P'] = values['5-6P'] + amount

            elif date >= '18:00:00' and date <= "18:59:59":
                values['6-7P'] = values['6-7P'] + amount

            elif date >= '19:00:00' and date <= "19:59:59":
                values['7-8P'] = values['7-8P'] + amount

            elif date >= '20:00:00' and date <= "20:59:59":
                values['8-9P'] = values['8-9P'] + amount

            elif date >= '21:00:00' and date <= "21:59:59":
                values['9-10P'] = values['9-10P'] + amount

            elif date >= '21:00:00' and date <= "22:59:59":
                values['10-11P'] = values['10-11P'] + amount

            else:
                values['11-12P'] = values['11-12P'] + amount

        for val in graph_data:
            val['value'] = values[val['label']]

        graph_data = [{'key': 'Sales By Hour', 'values': graph_data}]
        #print "\n?date", graph_data

        return graph_data

    @http.route('/pos/dashboard/update', type='json', auth='user')
    def pos_dashboard_update(self, filter_condition=None, **kw):
        data = self.pos_dashboard_data(filter_condition)
        return data

    def _prepare_order_domain(self, filter_condition):
        domain = []
        if filter_condition:
            today_date = datetime.utcnow().date()

            if filter_condition.get('date_filter') == 'year':
                yearrange = self.get_year_range(today_date)
                today_start = yearrange[0].strftime(DEFAULT_SERVER_DATETIME_FORMAT)  # get the midnight of the current utc day
                today_end = (yearrange[1] + relativedelta(hours=23, minutes=59, seconds=59)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                domain += [('date_order', '>=', today_start), ('date_order', '<=', today_end)]

            elif filter_condition.get('date_filter') == 'month':
                monthrange = self.get_month_range(today_date)
                month_start = monthrange[0].strftime(DEFAULT_SERVER_DATETIME_FORMAT)  # get the midnight of the current utc day
                month_end = (monthrange[1] + relativedelta(hours=23, minutes=59, seconds=59)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                domain += [('date_order', '>=', month_start), ('date_order', '<=', month_end)]

            elif filter_condition.get('date_filter') == 'week':
                weekrange = self.get_week_range(today_date)
                week_start = weekrange[0].strftime(DEFAULT_SERVER_DATETIME_FORMAT)  # get the midnight of the current utc day
                week_end = (weekrange[1] + relativedelta(hours=23, minutes=59, seconds=59)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                domain += [('date_order', '>=', week_start), ('date_order', '<=', week_end)]

            else:
                today_start = today_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)  # get the midnight of the current utc day
                today_end = (today_date + relativedelta(hours=23, minutes=59, seconds=59)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                domain += [('date_order', '>=', today_start), ('date_order', '<=', today_end)]

        return domain

    def get_month_range(self, start_date=None):
        days_in_month = calendar.monthrange(start_date.year, start_date.month)
        month_start_date = date(start_date.year, start_date.month, days_in_month[0])
        month_end_date = date(start_date.year, start_date.month, days_in_month[1])
        return (month_start_date, month_end_date)

    def get_week_range(self, date=None):
        weekday = calendar.weekday(date.year, date.month, date.day)
        week_start_date = date - timedelta(weekday)
        week_end_date = week_start_date + timedelta(days=6)
        return (week_start_date, week_end_date)

    def get_year_range(self, start_date=None):
        year_start_date = date(start_date.year, 1, 1)
        year_end_date = date(start_date.year, 12, 31)
        return (year_start_date, year_end_date)
