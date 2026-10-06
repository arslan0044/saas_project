from django import template

register = template.Library()


@register.filter(name="user_role")
def user_role(user):
    """Return the tenant role string for a given user, defaulting to 'staff'."""
    if not user or not user.is_authenticated:
        return "anonymous"
    if user.is_superuser:
        return "admin"
    profile = getattr(user, "tenant_profile", None)
    return getattr(profile, "role", "staff") if profile else "staff"


@register.filter(name="has_role")
def has_role(user, allowed_roles_csv):
    """
    Template filter to verify if user has one of the comma-separated roles.
    Usage: {% if request.user|has_role:"admin,manager" %}
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    
    current_role = user_role(user)
    allowed_roles = [r.strip().lower() for r in allowed_roles_csv.split(",")]
    return current_role in allowed_roles


@register.filter(name="can_edit")
def can_edit(user):
    """Admins and Managers can create and edit records."""
    return has_role(user, "admin,manager")


@register.filter(name="can_delete")
def can_delete(user):
    """Only Admins can delete records."""
    return has_role(user, "admin")


@register.filter(name="is_module_active")
def is_module_active(tenant, module_name):
    """
    Verifies if module is in tenant.active_modules.
    Usage: {% if request.tenant|is_module_active:"crm" %}
    """
    if not tenant:
        return False
    active_modules = getattr(tenant, "active_modules", [])
    return module_name in active_modules
