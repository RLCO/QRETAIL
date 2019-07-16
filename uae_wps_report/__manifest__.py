# -*- coding: utf-8 -*-
####################################################################################
#    QPR Qatar Pvt. Ltd.
#    Copyright (C) 2018-TODAY
#    Author: Abhishek (<https://www.qpr.qa>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
{
    'name': 'WPS Report Generation for Qatar',
    'version': '11.0.1.0.0',
    'summary': 'Wps Payroll System For Qatar',
    'category': 'Generic Modules/Human Resources',
    'author': 'QPR Qatar',
    'website': 'https://www.qpr.qa',
    'maintainer': 'QPR',
    'company': 'QPR Qatar',
    'website': 'https://www.qpr.qa',
    'depends': [
        'base',
        'hr',
        'report_xlsx',
        'hr_payroll',
        'hr_holidays',
        ],
    'data': [
        'views/view.xml',
        'wizard/wizard.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
