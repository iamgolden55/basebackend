def build_user_token_data(user):
    return {
        'basic_info': {
            'full_name': f"{user.first_name} {user.last_name}".strip(),
            'email': user.email,
            'has_completed_onboarding': user.has_completed_onboarding,
            'role': 'patient',
            'hpn': user.hpn,
            'state': user.state,
            'city': user.city,
            'phone': user.phone,
            'country': user.country,
            'gender': user.gender,
            'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None
        }
    }