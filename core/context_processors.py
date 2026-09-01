from .models import Company


def selected_company(request):
    """Expose the currently selected company (including its logo) on every page."""
    company_id = request.session.get("selected_company_id")
    if not company_id:
        return {"selected_company_global": None}

    company = Company.objects.filter(id=company_id, is_active=True).only(
        "id", "name", "logo"
    ).first()

    # Keep the session name synced if the company name changes.
    if company and request.session.get("selected_company_name") != company.name:
        request.session["selected_company_name"] = company.name

    return {"selected_company_global": company}
