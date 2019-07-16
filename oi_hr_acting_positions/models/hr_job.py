'''
Created on Dec 10, 2018

@author: Zuhair Hammadi
'''
from odoo import models, fields, api

class Job(models.Model):
    _inherit = "hr.job"

    acting_employee_ids = fields.Many2many('hr.employee',  relation='hr_employee_acting_job_rel', string='Acting Employees')
    acting_employee_count = fields.Integer(compute = '_calc_acting_employee_count')
    
    @api.depends('acting_employee_ids')
    def _calc_acting_employee_count(self):
        for record in self:
            record.acting_employee_count = len(record.acting_employee_ids)