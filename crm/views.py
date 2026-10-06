import json
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from user_management.decorators import module_required, role_required, is_htmx
from .models import Lead
from .forms import LeadForm


@module_required('crm')
@role_required(['admin', 'manager', 'staff'])
def lead_list(request):
    """List all leads scoped to the active tenant schema with search & status filtering."""
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()

    leads = Lead.objects.all().order_by('-created_at')

    if status_filter:
        leads = leads.filter(status=status_filter)
    if query:
        leads = leads.filter(
            name__icontains=query
        ) | leads.filter(
            company_name__icontains=query
        ) | leads.filter(
            email__icontains=query
        )

    context = {
        'leads': leads,
        'query': query,
        'status_filter': status_filter,
        'total_count': leads.count(),
        'status_choices': Lead.STATUS_CHOICES,
    }

    if is_htmx(request) and not request.GET.get('full_page'):
        return render(request, 'crm/partials/lead_table.html', context)
    return render(request, 'crm/lead_list.html', context)


@module_required('crm')
@role_required(['admin', 'manager'])
@require_http_methods(["GET", "POST"])
def lead_create(request):
    """HTMX-powered lead creation dialog and submission handler."""
    if request.method == "POST":
        form = LeadForm(request.POST)
        if form.is_valid():
            lead = form.save()
            response = HttpResponse("", status=200)
            response["HX-Trigger"] = json.dumps({
                "closeModal": True,
                "refreshLeads": True,
                "showToast": f"Lead '{lead.name}' created successfully!"
            })
            return response
        # Validation error: return modal partial with error states
        return render(request, 'crm/partials/lead_modal.html', {
            'form': form,
            'modal_title': 'Add New Lead',
            'action_url': request.path,
        }, status=422)

    form = LeadForm()
    return render(request, 'crm/partials/lead_modal.html', {
        'form': form,
        'modal_title': 'Add New Lead',
        'action_url': request.path,
    })


@module_required('crm')
@role_required(['admin', 'manager'])
@require_http_methods(["GET", "POST"])
def lead_update(request, pk):
    """HTMX-powered lead edit dialog and update handler."""
    lead = get_object_or_404(Lead, pk=pk)

    if request.method == "POST":
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            response = HttpResponse("", status=200)
            response["HX-Trigger"] = json.dumps({
                "closeModal": True,
                "refreshLeads": True,
                "showToast": f"Lead '{lead.name}' updated successfully!"
            })
            return response
        return render(request, 'crm/partials/lead_modal.html', {
            'form': form,
            'lead': lead,
            'modal_title': f"Edit Lead: {lead.name}",
            'action_url': request.path,
        }, status=422)

    form = LeadForm(instance=lead)
    return render(request, 'crm/partials/lead_modal.html', {
        'form': form,
        'lead': lead,
        'modal_title': f"Edit Lead: {lead.name}",
        'action_url': request.path,
    })


@module_required('crm')
@role_required(['admin'])
@require_http_methods(["DELETE", "POST"])
def lead_delete(request, pk):
    """HTMX inline delete endpoint (Admin only)."""
    lead = get_object_or_404(Lead, pk=pk)
    lead_name = lead.name
    lead.delete()

    response = HttpResponse("", status=200)
    response["HX-Trigger"] = json.dumps({
        "showToast": f"Lead '{lead_name}' deleted."
    })
    return response
