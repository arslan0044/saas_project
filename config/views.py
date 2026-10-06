from django.shortcuts import render
from django.db.models import Sum


def dashboard(request):
    """
    Central multi-tenant portal dashboard.
    Dynamically renders Control Plane metrics on the 'public' schema,
    or modular operational metrics on individual tenant schemas.
    """
    tenant = getattr(request, 'tenant', None)
    schema_name = getattr(tenant, 'schema_name', 'public') if tenant else 'public'
    active_modules = getattr(tenant, 'active_modules', []) if tenant else []

    context = {
        'is_public_schema': (schema_name == 'public'),
        'active_modules': active_modules,
    }

    # Public schema context (Control plane)
    if schema_name == 'public':
        from tenant_manament.models import Tenant, Domain
        context['tenant_count'] = Tenant.objects.exclude(schema_name='public').count()
        context['domain_count'] = Domain.objects.count()
        context['tenants'] = Tenant.objects.exclude(schema_name='public').order_by('-created_on')[:10]
        return render(request, 'dashboard.html', context)

    # Tenant schema context (Data plane)
    # 1. CRM Metrics (if gated)
    if 'crm' in active_modules:
        from crm.models import Lead
        leads = Lead.objects.all()
        context['lead_count'] = leads.count()
        context['pipeline_value'] = leads.aggregate(total=Sum('estimated_value'))['total'] or 0.00
        context['recent_leads'] = leads.order_by('-created_at')[:5]

    # 2. HRM Metrics (if gated)
    if 'hrm' in active_modules:
        from hrm.models import Employee, Department
        context['employee_count'] = Employee.objects.count()
        context['active_employees'] = Employee.objects.filter(is_active=True).count()
        context['dept_count'] = Department.objects.count()
        context['recent_employees'] = Employee.objects.select_related('department').order_by('-joining_date')[:5]

    # 3. User Management Metrics (if gated)
    if 'user_management' in active_modules:
        from user_management.models import TenantUserProfile
        context['member_count'] = TenantUserProfile.objects.count()

    return render(request, 'dashboard.html', context)
