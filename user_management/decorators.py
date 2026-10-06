from functools import wraps
import json
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect


def is_htmx(request):
    """Detect whether incoming request originated from an HTMX client."""
    return request.headers.get("HX-Request") == "true"


def module_required(module_name):
    """
    Feature-Gating Security Decorator.
    
    Verifies that the requested module is active for the current tenant 
    (inspected via request.tenant.active_modules).
    
    - For direct browser requests: Raises PermissionDenied (HTTP 403).
    - For HTMX requests: Returns an atomic HTML warning banner (HTTP 403).
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            tenant = getattr(request, "tenant", None)
            active_modules = getattr(tenant, "active_modules", []) if tenant else []

            if module_name not in active_modules:
                if is_htmx(request):
                    return HttpResponse(
                        f"""
                        <div class="rounded-xl border border-rose-200 bg-rose-50 p-6 text-center text-rose-800 shadow-sm">
                            <h3 class="text-base font-bold">Module Subscription Inactive</h3>
                            <p class="mt-1 text-sm text-rose-600">
                                The <span class="font-mono font-semibold">{module_name}</span> module is not enabled for {tenant.name if tenant else 'this tenant'}.
                            </p>
                        </div>
                        """,
                        status=403,
                    )
                raise PermissionDenied(
                    f"The module '{module_name}' is not enabled for your organization."
                )

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def role_required(allowed_roles):
    """
    Role-Based Access Control (RBAC) Security Decorator.
    
    Enforces permission boundaries based on TenantUserProfile.role:
      - 'admin': Full CRUD access and administrative settings.
      - 'manager': Create, Read, and Update records; Deletion prohibited.
      - 'staff': Read-only access to records; mutation actions prohibited.
      
    Superusers bypass RBAC checks.
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user

            if not user.is_authenticated:
                if is_htmx(request):
                    response = HttpResponse("Authentication required", status=401)
                    response["HX-Redirect"] = "/admin/login/"
                    return response
                return redirect("/admin/login/")

            # Django Superuser bypass
            if user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Retrieve tenant-scoped profile
            profile = getattr(user, "tenant_profile", None)
            user_role = getattr(profile, "role", "staff") if profile else "staff"

            if user_role not in allowed_roles:
                if is_htmx(request):
                    return HttpResponse(
                        f"""
                        <div class="rounded-xl border border-amber-200 bg-amber-50 p-4 text-amber-800 text-sm shadow-sm flex items-center justify-between">
                            <span>Forbidden: Your current role (<strong class="capitalize">{user_role}</strong>) cannot perform this action.</span>
                            <button onclick="this.parentElement.remove()" class="text-amber-600 hover:text-amber-800 font-bold ml-4">&times;</button>
                        </div>
                        """,
                        status=403,
                    )
                raise PermissionDenied(
                    f"Insufficient permissions. Required role: {', '.join(allowed_roles)} (You are: {user_role})."
                )

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
