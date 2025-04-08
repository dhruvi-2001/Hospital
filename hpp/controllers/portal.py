from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request, route


class CustomerPortalCustom(CustomerPortal):

    def _get_mandatory_fields(self):
        """ This method is there so that we can override the mandatory fields """
        # Removed phone from the required field list for the portal
        return ["name", "marital_status", "date_of_birth", "gender", "email", "street", "city", "country_id"]

    def _get_optional_fields(self):
        """ This method is there so that we can override the optional fields """
        return ["street2", "age", "phone", "zipcode", "state_id", "vat", "company_name", "blood_type",
                "medical_history", "hospital_info", "emergency_contact", "insurance_info", "is_insured",
                "payment_amount", "payment_method"]

    @route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        values = self._prepare_portal_layout_values()

        print("CALLLLLLLLLLLLLLLLLLLLLLLLLLL")
        partner = request.env.user.partner_id
        values.update({
            'error': {},
            'error_message': [],
        })

        if post and request.httprequest.method == 'POST':
            post['is_insured'] = 'is_insured' in post  # Will be True if checked, False otherwise
            if not partner.can_edit_vat():
                post['country_id'] = str(partner.country_id.id)

            error, error_message = self.details_form_validate(post)
            values.update({'error': error, 'error_message': error_message})
            values.update(post)
            if not error:
                values = {key: post[key] for key in self._get_mandatory_fields()}
                values.update({key: post[key] for key in self._get_optional_fields() if key in post})
                for field in set(['country_id', 'state_id']) & set(values.keys()):
                    try:
                        values[field] = int(values[field])
                    except:
                        values[field] = False
                values.update({'zip': values.pop('zipcode', '')})
                self.on_account_update(values, partner)
                partner.sudo().write(values)
                if redirect:
                    return request.redirect(redirect)
                return request.redirect('/my/home')

        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])
        # Get partner record
        partner = request.env.user.partner_id.sudo()

        # Get selection field mappings
        partner_model = request.env['res.partner']
        selection_fields = {
            'gender': dict(partner_model.fields_get(['gender'])['gender']['selection']),
            'marital_status': dict(partner_model.fields_get(['marital_status'])['marital_status']['selection']),
            # 'blood_type': dict(partner_model.fields_get(['blood_type'])['blood_type']['selection']),
        }

        # Convert selection labels to keys before calling super()
        for field, selection_mapping in selection_fields.items():
            if field in post:
                label_value = post[field]
                key_value = next((key for key, label in selection_mapping.items() if label == label_value), None)
                if key_value:
                    post[field] = key_value  # Replace label with key

        values.update({
            'partner': partner,
            'countries': countries,
            'states': states,
            'has_check_vat': hasattr(request.env['res.partner'], 'check_vat'),
            'partner_can_edit_vat': partner.can_edit_vat(),
            'redirect': redirect,
            'page_name': 'my_details',
        })

        response = request.render("portal.portal_my_details", values)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response
