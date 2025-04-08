from datetime import date
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = "res.partner"

    is_patient = fields.Boolean(default=True)
    patient_id = fields.Char(string="Patient ID", readonly=True, copy=False)
    age = fields.Integer(string="Age", compute="_compute_age", store=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string="Gender")
    hospital_info = fields.Text(string='Hospital Info')
    blood_type = fields.Selection([
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ], string='Blood Type')
    marital_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed')
    ], string="Marital Status")
    date_of_birth = fields.Date(string='Date of Birth')
    medical_history = fields.Text(string='Medical History')
    emergency_contact = fields.Char(string='Emergency Contact')
    insurance_info = fields.Text(string='Insurance Info')
    is_insured = fields.Boolean(string="Insurance")
    disease_id = fields.Many2many('hospital.disease', string="Disease",
                                  default=lambda self: self._get_default_disease())
    disease_question_ids = fields.One2many('hospital.patient.disease.question', 'patient_id',
                                           string="Disease Questions")
    allergy_ids = fields.Many2many('hospital.allergy',
                                   string="Allergies")
    is_doctor = fields.Boolean(string="Is Doctor", default=False)
    primary_doctor_id = fields.Many2one('res.partner', string="Primary Doctor", domain=[('is_doctor', '=', True)])
    # insurance_company_id = fields.Many2one('res.partner', string="Insurance Provider")
    portal_access = fields.Boolean(string="Portal Access", default=False)
    user_id = fields.Many2one('res.users', string="Related User")
    show_qa_tab = fields.Boolean(string="Show Q&A", compute="_compute_show_qa_tab", store=True)

    payment_amount = fields.Float(string="Payment Amount", readonly=True)
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('online', 'Online'),
    ], string="Payment Method", readonly=True)

    # Add to ResPartner class
    visit_ids = fields.One2many('patient.visit', 'patient_id', string="Visits")
    visit_count = fields.Integer(compute='_compute_visit_count', string='Visit Count')
    payment_count = fields.Integer(compute='_compute_payment_count', string='Payment Count')



    def _grant_portal_access(self, partner):
        """ Automatically grant portal access to a patient. """
        PortalWizard = self.env['portal.wizard'].sudo()
        wizard = PortalWizard.create({'partner_ids': [(6, 0, [partner.id])]})
        for wizard_user in wizard.user_ids:
            try:
                wizard_user.action_grant_access()
                _logger.info(f"Portal access granted to {partner.name} ({partner.email})")
            except UserError as e:
                _logger.error(f"Failed to grant portal access: {e}")

    @api.model
    def create(self, vals):
        if vals.get('is_patient') and not vals.get('email'):
            raise UserError("Please set email")
        partner = super(ResPartner, self).create(vals)
        if partner.is_patient and partner.email:
            self._grant_portal_access(partner)
        return partner

    @api.depends('date_of_birth')
    def _compute_age(self):
        today = date.today()
        for partner in self:
            if partner.date_of_birth:
                partner.age = today.year - partner.date_of_birth.year - (
                        (today.month, today.day) < (partner.date_of_birth.month, partner.date_of_birth.day)
                )
            else:
                partner.age = 0

    @api.model
    def _get_default_disease(self):
        """ Set 'No Disease' as default if it exists. """
        no_disease = self.env['hospital.disease'].search([('name', '=', 'No Disease')], limit=1)
        return [(6, 0, [no_disease.id])] if no_disease else []

    @api.depends('disease_id')
    def _compute_show_qa_tab(self):
        """ Compute whether the Q&A tab should be visible. """
        for record in self:
            record.show_qa_tab = bool(
                record.disease_id and not record.disease_id.filtered(lambda d: d.name == "No Disease"))

    @api.onchange('disease_id')
    def _onchange_disease_id(self):
        """ Update questions dynamically based on selected diseases. """
        if self.disease_id:
            disease_questions = self.env['hospital.disease.question'].search([
                ('disease_id', 'in', self.disease_id.ids)
            ])

            self.disease_question_ids = [(5, 0, 0)]  # Clear old questions
            self.disease_question_ids = [(0, 0, {
                'question': q.question,
                'answer': 'no',
            }) for q in disease_questions]

    def _compute_visit_count(self):
        for partner in self:
            partner.visit_count = self.env['patient.visit'].search_count([('patient_id', '=', partner.id)])

    def action_view_visits(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Patient Visits',
            'res_model': 'patient.visit',
            'view_mode': 'kanban,list,form,pivot',
            'domain': [('patient_id', '=', self.id)],
            # 'domain': [('patient_id', '=', self.id), ('state', '=', 'completed')],
            'context': {'default_patient_id': self.id},
        }

    def action_view_all_payments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Patient Payments',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }

    def _compute_payment_count(self):
        payments = self.env['account.payment'].search_read(
            [('partner_id', 'in', self.ids)],
            ['partner_id']
        )
        payment_count = {}
        for payment in payments:
            partner_id = payment['partner_id'][0]
            payment_count[partner_id] = payment_count.get(partner_id, 0) + 1
        for partner in self:
            partner.payment_count = payment_count.get(partner.id, 0)