from odoo import models, fields, api, _
from datetime import datetime

class PatientVisit(models.Model):
    _name = "patient.visit"
    _description = "Patient Visit"
    _order = "visit_date desc"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']



    @api.model
    def _generate_visit_name(self):
        sequence = self.env['ir.sequence'].next_by_code('patient.visit') or _('New')



    name = fields.Char(string="Visit ID", readonly=True)
    patient_id = fields.Many2one('res.partner', string="Patient", required=True, domain=[('is_patient', '=', True)], tracking=True)
    doctor_id = fields.Many2one('res.partner', string="Doctor", related='patient_id.primary_doctor_id', tracking=True)
    visit_date = fields.Datetime(string="Visit Date", required=True, default=fields.Datetime.now, tracking=True)
    notes = fields.Text(string="Notes")
    state = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string="Status", default='scheduled', tracking=True)
    prescription = fields.Text(string="Prescription")
    prescription_line_ids = fields.One2many('prescription.line', 'visit_id', string="Prescription Lines")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    visit_count = fields.Integer(compute='_compute_visit_count', string='Visit Count')

    payment_amount = fields.Float(string="Payment Amount")
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('online', 'Online'),
    ], string="Payment Method")
    payment_date = fields.Date(string='Payment Date', default=fields.Date.today)
    prescription_total = fields.Float(string='Prescription Total', compute='_compute_prescription_total', store=True)
    payable_amount = fields.Float(string='Payable Amount', compute='_compute_payable_amount', store=True)

    payment_ids = fields.One2many('account.payment', 'visit_id', string='Payments')
    payment_count = fields.Integer(compute='_compute_payment_count', string='Payment Count')



    def _compute_payment_count(self):
        payments = self.env['account.payment'].search_read(
            [('visit_id', 'in', self.ids)],
            ['visit_id']
        )
        payment_count = {}
        for payment in payments:
            visit_id = payment['visit_id'][0]
            payment_count[visit_id] = payment_count.get(visit_id, 0) + 1
        for visit in self:
            visit.payment_count = payment_count.get(visit.id, 0)

    def action_view_payments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Visit Payments',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('visit_id', '=', self.id)],
            'context': {'default_visit_id': self.id},
        }



    @api.depends('prescription_line_ids.subtotal')
    def _compute_prescription_total(self):
        for visit in self:
            visit.prescription_total = sum(line.subtotal for line in visit.prescription_line_ids)

    @api.depends('prescription_total', 'payment_amount')
    def _compute_payable_amount(self):
        for visit in self:
            visit.payable_amount = visit.prescription_total - visit.payment_amount

    def print_payment_receipt(self):
        return self.env.ref('hpp.action_report_patient_visit_receipt').report_action(self)

    def get_doctor_name(self):
        """ Safe method to get doctor name that works for portal users """
        return self.doctor_id.sudo().name or ''



    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('patient.visit') or 'New'
        return super(PatientVisit, self).create(vals)

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reschedule(self):
        self.write({'state': 'scheduled'})

    def _compute_visit_count(self):
        for partner in self:
            partner.visit_count = self.env['patient.visit'].search_count([('patient_id', '=', partner.id)])

    def _compute_access_url(self):
        for record in self:
            record.access_url = '/my/visits/%s' % record.id
