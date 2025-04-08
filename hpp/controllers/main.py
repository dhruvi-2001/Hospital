from odoo import http, fields
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

class PatientPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super(PatientPortal, self)._prepare_home_portal_values(counters)
        if 'visit_count' in counters:
            values['visit_count'] = request.env['patient.visit'].search_count([
                ('patient_id', '=', request.env.user.partner_id.id)
            ])
        return values

    @http.route(['/my/visits', '/my/visits/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_visits(self, page=1, **kw):
        Visit = request.env['patient.visit']
        domain = [('patient_id', '=', request.env.user.partner_id.id)]

        visit_count = Visit.sudo().search_count(domain)
        pager = request.website.pager(
            url="/my/visits",
            total=visit_count,
            page=page,
            step=self._items_per_page
        )
        visits = Visit.sudo().search(domain, limit=self._items_per_page, offset=pager['offset'])

        values = {
            'visits': visits.with_context(allowed_company_ids=request.env.user.company_ids.ids),
            'pager': pager,
            'default_url': '/my/visits',
        }
        return request.render("hpp.portal_my_visits", values)

    @http.route('/my/visits/<int:visit_id>', type='http', auth="user", website=True)
    def portal_my_visit(self, visit_id, **kw):
        visit = request.env['patient.visit'].sudo().browse(visit_id)
        if not visit.exists() or visit.patient_id != request.env.user.partner_id:
            return request.redirect('/my')

        # Ensure default values for payment fields if they're empty
        if not visit.payment_amount and visit.patient_id.payment_amount:
            visit.write({
                'payment_amount': visit.patient_id.payment_amount,
                'payment_method': visit.patient_id.payment_method,
                'payment_date': fields.Date.today()
            })

        values = {
            'visit': visit,
            'page_name': 'visit',
        }
        return request.render("hpp.portal_my_visit_detail", values)

    @http.route(['/my/visits/receipt/<int:visit_id>'], type='http', auth="user", website=True)
    def get_visit_receipt(self, visit_id, **kw):
        # Check if visit exists and belongs to current user
        visit = request.env['patient.visit'].sudo().browse(visit_id)
        if not visit.exists() or visit.patient_id != request.env.user.partner_id:
            return request.redirect('/my')

        # Prepare data with sudo access for related records
        data = {
            'doc_ids': visit.ids,
            'doc_model': 'patient.visit',
            'docs': visit.sudo(),
            'get_doctor_name': lambda doctor_id: request.env['res.partner'].sudo().browse(
                doctor_id).name or 'Not Available'
        }

        # Generate PDF with proper access rights
        pdf = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'hpp.report_patient_visit_receipt',
            visit.ids,
            data=data
        )

        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf[0]))
        ]
        return request.make_response(pdf[0], headers=pdfhttpheaders)