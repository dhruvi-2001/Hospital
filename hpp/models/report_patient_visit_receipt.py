from odoo import models, fields, api

class PatientVisitReport(models.AbstractModel):
    _name = 'report.hpp.report_patient_visit_receipt'
    _description = 'Patient Visit Receipt Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['patient.visit'].with_context(allowed_company_ids=[]).browse(docids)

        # Ensure portal users can only access their own visits
        if self.env.user.has_group('base.group_portal'):
            docs = docs.filtered(lambda d: d.patient_id == self.env.user.partner_id)
            if not docs:
                raise AccessError(_("You don't have access to this report."))

        return {
            'doc_ids': docs.ids,
            'doc_model': 'patient.visit',
            'docs': docs.sudo(),
            'data': data,
        }