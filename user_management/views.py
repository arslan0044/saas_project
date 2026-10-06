import json
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from .decorators import module_required, role_required, is_htmx
from .models import TenantUserProfile
from .forms import TenantUserProfileForm


@module_required('user_management')
@role_required(['admin', 'manager', 'staff'])
def team_list(request):
    """List team members and roles scoped to the active tenant schema."""
    query = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '').strip()

    members = TenantUserProfile.objects.select_related('user').all().order_by('user__username')

    if role_filter:
        members = members.filter(role=role_filter)
    if query:
        members = members.filter(
            user__username__icontains=query
        ) | members.filter(
            user__email__icontains=query
        ) | members.filter(
            user__first_name__icontains=query
        ) | members.filter(
            user__last_name__icontains=query
        )

    context = {
        'members': members,
        'query': query,
        'role_filter': role_filter,
        'role_choices': TenantUserProfile.ROLE_CHOICES,
        'total_count': members.count(),
    }

    if is_htmx(request) and not request.GET.get('full_page'):
        return render(request, 'user_management/partials/team_table.html', context)
    return render(request, 'user_management/team_list.html', context)


@module_required('user_management')
@role_required(['admin'])
@require_http_methods(["GET", "POST"])
def team_member_edit(request, pk):
    """HTMX modal for editing a member's role and phone (Admin only)."""
    profile = get_object_or_404(TenantUserProfile, pk=pk)

    if request.method == "POST":
        form = TenantUserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            response = HttpResponse("", status=200)
            response["HX-Trigger"] = json.dumps({
                "closeModal": True,
                "refreshTeam": True,
                "showToast": f"Updated role for '{profile.user.username}'."
            })
            return response
        return render(request, 'user_management/partials/team_modal.html', {
            'form': form,
            'profile': profile,
            'modal_title': f"Edit Role: {profile.user.username}",
            'action_url': request.path,
        }, status=422)

    form = TenantUserProfileForm(instance=profile)
    return render(request, 'user_management/partials/team_modal.html', {
        'form': form,
        'profile': profile,
        'modal_title': f"Edit Role: {profile.user.username}",
        'action_url': request.path,
    })
