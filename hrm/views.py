import json
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from user_management.decorators import module_required, role_required, is_htmx
from .models import Employee, Department
from .forms import EmployeeForm, DepartmentForm


@module_required('hrm')
@role_required(['admin', 'manager', 'staff'])
def employee_list(request):
    """List employees scoped to the active tenant schema with department & active status filters."""
    query = request.GET.get('q', '').strip()
    dept_id = request.GET.get('department', '').strip()
    status_filter = request.GET.get('status', '').strip()

    employees = Employee.objects.select_related('department').all().order_by('-joining_date')

    if dept_id:
        employees = employees.filter(department_id=dept_id)
    if status_filter == 'active':
        employees = employees.filter(is_active=True)
    elif status_filter == 'inactive':
        employees = employees.filter(is_active=False)

    if query:
        employees = employees.filter(
            first_name__icontains=query
        ) | employees.filter(
            last_name__icontains=query
        ) | employees.filter(
            email__icontains=query
        ) | employees.filter(
            designation__icontains=query
        )

    departments = Department.objects.all().order_by('name')

    context = {
        'employees': employees,
        'departments': departments,
        'query': query,
        'selected_dept': dept_id,
        'status_filter': status_filter,
        'total_count': employees.count(),
    }

    if is_htmx(request) and not request.GET.get('full_page'):
        return render(request, 'hrm/partials/employee_table.html', context)
    return render(request, 'hrm/employee_list.html', context)


@module_required('hrm')
@role_required(['admin', 'manager'])
@require_http_methods(["GET", "POST"])
def employee_create(request):
    """HTMX modal for creating an employee."""
    if request.method == "POST":
        form = EmployeeForm(request.POST)
        if form.is_valid():
            emp = form.save()
            response = HttpResponse("", status=200)
            response["HX-Trigger"] = json.dumps({
                "closeModal": True,
                "refreshEmployees": True,
                "showToast": f"Employee '{emp.first_name} {emp.last_name}' added successfully!"
            })
            return response
        return render(request, 'hrm/partials/employee_modal.html', {
            'form': form,
            'modal_title': 'Add New Employee',
            'action_url': request.path,
        }, status=422)

    form = EmployeeForm()
    return render(request, 'hrm/partials/employee_modal.html', {
        'form': form,
        'modal_title': 'Add New Employee',
        'action_url': request.path,
    })


@module_required('hrm')
@role_required(['admin', 'manager'])
@require_http_methods(["GET", "POST"])
def employee_update(request, pk):
    """HTMX modal for updating an employee record."""
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == "POST":
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            emp = form.save()
            response = HttpResponse("", status=200)
            response["HX-Trigger"] = json.dumps({
                "closeModal": True,
                "refreshEmployees": True,
                "showToast": f"Employee '{emp.first_name} {emp.last_name}' updated successfully!"
            })
            return response
        return render(request, 'hrm/partials/employee_modal.html', {
            'form': form,
            'employee': employee,
            'modal_title': f"Edit Employee: {employee.first_name} {employee.last_name}",
            'action_url': request.path,
        }, status=422)

    form = EmployeeForm(instance=employee)
    return render(request, 'hrm/partials/employee_modal.html', {
        'form': form,
        'employee': employee,
        'modal_title': f"Edit Employee: {employee.first_name} {employee.last_name}",
        'action_url': request.path,
    })


@module_required('hrm')
@role_required(['admin'])
@require_http_methods(["DELETE", "POST"])
def employee_delete(request, pk):
    """HTMX inline delete endpoint for employees (Admin only)."""
    employee = get_object_or_404(Employee, pk=pk)
    full_name = f"{employee.first_name} {employee.last_name}"
    employee.delete()

    response = HttpResponse("", status=200)
    response["HX-Trigger"] = json.dumps({
        "showToast": f"Employee '{full_name}' deleted."
    })
    return response


@module_required('hrm')
@role_required(['admin', 'manager'])
@require_http_methods(["GET", "POST"])
def department_manage(request):
    """HTMX dialog to add and list departments."""
    if request.method == "POST":
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dept = form.save()
            response = HttpResponse("", status=200)
            response["HX-Trigger"] = json.dumps({
                "closeModal": True,
                "refreshEmployees": True,
                "showToast": f"Department '{dept.name}' created!"
            })
            return response
        departments = Department.objects.all().order_by('name')
        return render(request, 'hrm/partials/department_modal.html', {
            'form': form,
            'departments': departments,
            'modal_title': 'Manage Departments',
            'action_url': request.path,
        }, status=422)

    form = DepartmentForm()
    departments = Department.objects.all().order_by('name')
    return render(request, 'hrm/partials/department_modal.html', {
        'form': form,
        'departments': departments,
        'modal_title': 'Manage Departments',
        'action_url': request.path,
    })
