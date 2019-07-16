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
    'name': 'Web Export Current View',
    'version': '11.0.2.0.0',
    'category': 'Web',
    'author': 'QPR Qatar',
    'website': 'https://www.qpr.qa',
    'license': 'AGPL-3',
    'depends': [
        'web',
    ],
    "data": [
        'security/groups.xml',
        'views/web_export_view_view.xml',
    ],
    'qweb': [
        "static/src/xml/web_export_view_template.xml",
    ],

    'installable': True,
    'auto_install': False,
}
