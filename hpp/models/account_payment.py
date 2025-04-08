from odoo import models, fields

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    visit_id = fields.Many2one('patient.visit', string='Patient Visit')