# -*- coding: utf-8 -*-
from odoo.addons.appointment.controllers.appointment import AppointmentController
from odoo.http import request, route
from odoo import http


class CustomerAppointmentPortalCustom(AppointmentController):

    @http.route(['/appointment/<int:appointment_type_id>/submit'],
                type='http', auth="public", website=True, methods=["POST"])
    def appointment_form_submit(self, appointment_type_id, datetime_str, duration_str, name, phone, email,
                                staff_user_id=None, available_resource_ids=None, asked_capacity=1,
                                guest_emails_str=None, payment_amount=None, payment_method=None, **kwargs):

        # Convert payment_amount to float
        payment_amount = float(payment_amount) if payment_amount else 0.0

        # Call the parent method to create the appointment
        response = super().appointment_form_submit(
            appointment_type_id, datetime_str, duration_str, name, phone, email,
            staff_user_id, available_resource_ids, asked_capacity,
            guest_emails_str, **kwargs
        )

        # Get the last created event (assuming the appointment creates a calendar event)
        last_event = request.env['calendar.event'].sudo().search([], order="id desc", limit=1)

        if last_event:
            last_event.sudo().write({
                'payment_amount': payment_amount,
                'payment_method': payment_method
            })

            # Update the partner's payment information
            partner = request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)
            if partner:
                partner.write({
                    'payment_amount': payment_amount,
                    'payment_method': payment_method
                })

            # Send confirmation email
            template = request.env.ref('hpp.mail_template_appointment_schedule2')
            if template:
                template.sudo().send_mail(last_event.id, force_send=True)

        return response
