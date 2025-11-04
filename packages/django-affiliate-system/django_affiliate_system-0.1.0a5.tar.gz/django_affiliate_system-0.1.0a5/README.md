# Django Affiliate System

[![PyPI version](https://badge.fury.io/py/django-affiliate-system.svg)](https://badge.fury.io/py/django-affiliate-system)
[![Python Versions](https://img.shields.io/pypi/pyversions/django-affiliate-system.svg)](https://pypi.org/project/django-affiliate-system/)
[![Django Versions](https://img.shields.io/pypi/djversions/django-affiliate-system.svg)](https://pypi.org/project/django-affiliate-system/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

A comprehensive, production-ready Django affiliate marketing and referral tracking system with built-in REST API support.

## Features

- 🎯 **Multi-tenant Support** - Manage multiple affiliate programs
- 🔗 **Referral Link Management** - Generate and track custom referral links
- 📊 **Advanced Analytics** - Track clicks, conversions, and commissions
- 💰 **Commission Calculation** - Flexible commission rules and payouts
- 🔐 **Hybrid Authentication** - JWT and API key authentication
- 📱 **Session Tracking** - Multi-touch attribution models
- 🎨 **RESTful API** - Complete REST API with Django REST Framework
- 🔔 **Webhook Support** - External conversion tracking
- ⚡ **Celery Task Support** (Optional)

## Requirements

- Python 3.9+
- Django 4.0+
- Django REST Framework 3.14+

## Installation

### Basic Installation

```bash
pip install django-affiliate-system
```

### With Optional Dependencies

```bash

# With Celery support
pip install django-affiliate-system[celery]

# With all optional features
pip install django-affiliate-system[all]
```

## Quick Start

### 1. Add to Installed Apps

Add `django_affiliate_system` and its dependencies to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'rest_framework_simplejwt',
    'django_affiliate_system',
]
```

### 2. Add Middleware

```python
MIDDLEWARE = [
    # ...
    'django_affiliate_system.middleware.CORSMiddleware',
    'django_affiliate_system.middleware.TenantMiddleware',
]
```

### 3. Configure Settings

```python
# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'django_affiliate_system.authentication.HybridAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Django Affiliate System
AFFILIATE_SYSTEM = {
    'DOMAIN_PROTOCOL': 'https',
    'DOMAIN': 'yourdomain.com',
    'DEFAULT_COMMISSION_RATE': 10.0,  # 10%
    'COOKIE_DURATION_DAYS': 30,
    'ALLOWED_CORS_ORIGINS': [
        'http://localhost:3000',
        'https://yourdomain.com',
    ],
}
```

### 4. Include URLs

```python
from django.urls import path, include

urlpatterns = [
    # ...
    path('affiliate/', include('django_affiliate_system.urls')),
]
```

### 5. Run Migrations

```bash
python manage.py migrate django_affiliate_system
```

### 6. Create a Tenant

```python
from django_affiliate_system.models import Tenant
from django.contrib.auth import get_user_model

User = get_user_model()
owner = User.objects.create_user('owner@example.com', password='password')

tenant = Tenant.objects.create(
    name="My Affiliate Program",
    slug="my-program",
    destination_url="https://mysite.com",
    owner=owner,
    default_commission_rate=15.0
)

print(f"API Key: {tenant.api_key}")
```

## API Usage

### Authentication

The system supports two authentication methods:

#### 1. JWT Authentication (for user-facing APIs)

```bash
# Get token
curl -X POST http://localhost:8000/affiliate/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "password"}'

# Use token
curl http://localhost:8000/affiliate/api/affiliates/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 2. API Key Authentication (for tenant APIs)

```bash
curl http://localhost:8000/affiliate/api/tenants/ \
  -H "X-API-Key: YOUR_TENANT_API_KEY"
```

### Create an Affiliate

```bash
curl -X POST http://localhost:8000/affiliate/api/affiliates/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-API-Key: YOUR_TENANT_API_KEY" \
  -H "Content-Type: application/json"
```

### Create a Referral Link

```bash
curl -X POST http://localhost:8000/affiliate/api/referral-links/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-API-Key: YOUR_TENANT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "my-custom-link",
    "destination_url": "https://mysite.com/product"
  }'
```

### Track Events

```bash
# Track a click
curl -X POST http://localhost:8000/affiliate/api/track/ \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "click",
    "referral_code": "AFFILIATE_CODE",
    "session_id": "unique-session-id"
  }'

# Track a conversion
curl -X POST http://localhost:8000/affiliate/api/track/ \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "purchase",
    "referral_code": "AFFILIATE_CODE",
    "session_id": "unique-session-id",
    "conversion_value": 99.99,
    "is_conversion": true
  }'
```

### Get Affiliate Statistics

```bash
curl http://localhost:8000/affiliate/api/affiliates/stats/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-API-Key: YOUR_TENANT_API_KEY"
```

## Models Overview

- **Tenant** - Platforms using the affiliate system
- **Affiliate** - Users who refer others
- **ReferralLink** - Unique referral links for affiliates
- **ReferralAction** - Track all referral actions (clicks, signups, purchases)
- **Commission** - Commissions earned from referrals
- **Payout** - Payments to affiliates
- **CommissionRule** - Rules for calculating commissions
- **ReferralSession** - Track user sessions across touchpoints

## Advanced Features

### Multi-Touch Attribution

```python
from django_affiliate_system.services.tracking import process_tracking_event

action = process_tracking_event(
    data={
        'event_type': 'purchase',
        'referral_code': 'REF123',
        'session_id': 'session-uuid',
        'conversion_value': 100.00,
        'is_conversion': True
    },
    meta=request.META,
    use_sessions=True,
    attribution_model='first_click'  # or 'last_click'
)
```

### Custom Commission Rules

```python
from django_affiliate_system.models import CommissionRule

rule = CommissionRule.objects.create(
    tenant=tenant,
    name="Premium Product Commission",
    action_type="purchase",
    is_percentage=True,
    value=20.0,  # 20%
    min_value=10.00,
    max_value=100.00,
    is_active=True
)
```

### Celery Tasks (Optional)

```python
# tasks.py in your project
from django_affiliate_system.tasks import process_payout

# Trigger payout processing
process_payout.delay(payout_id=123)
```

## Testing

```bash
# Install dev dependencies
pip install django-affiliate-system[dev]

# Run tests
pytest

# With coverage
pytest --cov=django_affiliate_system
```

## Documentation

Full documentation is available at [https://django-affiliate-system.readthedocs.io/](https://django-affiliate-system.readthedocs.io/)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📧 Email: aayodeji.f@gmail.com
- 🐛 Issues: [GitHub Issues](https://github.com/aayodejii/django-affiliate-system/issues)
- 📖 Documentation: [Read the Docs](https://django-affiliate-system.readthedocs.io/)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes.

## Credits

Created and maintained by [Ayodeji Akenroye](https://github.com/aayodejii).

# django-affiliate-system
