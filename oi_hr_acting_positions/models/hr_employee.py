'''
Created on Dec 10, 2018

@author: Zuhair Hammadi
'''
from odoo import models, fields

class Employee(models.Model):
    _inherit = 'hr.employee'
    
    acting_job_ids = fields.Many2many('hr.job', relation='hr_employee_acting_job_rel', string='Acting Job Positions')