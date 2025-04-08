from odoo import models, fields, api

class PrescriptionLine(models.Model):
    _name = "prescription.line"
    _description = "Prescription Line"

    visit_id = fields.Many2one('patient.visit', string="Visit", required=True, ondelete='cascade')
    medicine_id = fields.Many2one('product.product', string="Medicine", required=True, domain=[('type', '=', 'product')])
    dosage = fields.Char(string="Dosage", required=True)
    duration = fields.Char(string="Duration")
    notes = fields.Text(string="Instructions")
    price = fields.Float(string='Price', related='medicine_id.list_price', store=True, readonly=False)
    quantity = fields.Float(string='Quantity', default=1.0)
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)



    @api.depends('price', 'quantity')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.price * line.quantity