from odoo import models, fields

class AppointmentSlot(models.Model):
    _inherit = "appointment.slot"

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    payment_amount = fields.Float(string="Payment Amount")
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('online', 'Online'),
    ], string="Payment Method")