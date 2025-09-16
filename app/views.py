from app.models import Candidate, Project, Link, Company
import json


def dashboard_callback(request, context):
    if not request.user.is_superuser:

        user = request.user
        # cantidad de candidatos
        candidates = user.candidates.count()
        # cantidad de companies
        companies = user.companies.count()

        # cantidad de projectos totales
        projects = sum(c.projects.count() for c in user.companies.all())

        # for company in user.companies.all():
        #     for project in company.projects.all():

        # numero de Links AKA "Submissions" en los ultimos 7 days
        links = sum(c.links.count() for c in user.candidates.all())
    else:
        candidates = Candidate.objects.all().count()
        companies = Company.objects.all().count()
        projects = Project.objects.all().count()
        links = Link.objects.all().count()

    my = "My " if not request.user.is_superuser else ""

    context.update({
        "counters": [
            {"label": my + "Candidates", "value": candidates or '-'},
            {"label": my + "Links", "value": links or '-'},
            {"label": my + "Projects", "value": projects or '-'},
            {"label": my + "Companies", "value": companies or '-'},
            ],
        "chart_links_per_status": json.dumps(
                         {
                             "labels": [value for label, value in Link.StatusChoices.choices],
                             "datasets": [
                                 {
                                     "label": "Links per Status ",
                                     "data": [Link.objects.filter(status=status).count() for status in Link.StatusChoices.values],
                                     # "data": [s.links.count() for s in Status.objects.all()],
                                     "backgroundColor": "#9333ea",
                                 },
                             ],
                         }
                     ),
        })

    return context
