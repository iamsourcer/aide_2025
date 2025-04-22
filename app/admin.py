from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe

from .models import Company, CompanyContact, Location, Project, Candidate, Tag
#from .models import Status, Link
from .models import Link
from datetime import datetime, timedelta

#############

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group

from unfold.admin import ModelAdmin, StackedInline, TabularInline
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.decorators import action, display
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm, SelectableFieldsExportForm


admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    pass


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


admin.site.register(Location, ModelAdmin)
# admin.site.register(Status, ModelAdmin)


@admin.register(CompanyContact)
class CompanyContactAdmin(ModelAdmin):
    list_display = ['first_name',
                    'last_name',
                    'company__name']

    def get_queryset(self, request):

        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(company__user=request.user)


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    search_fields = ['name']


class HasLinkFilter(admin.SimpleListFilter):

    title = "Links"
    parameter_name = "link"

    def lookups(self, request, model_admin):
        return [
            ('recent_link', 'recently linked '),
            ('has_link', 'linked'),
            ('no_link', 'not linked')
            ]

    def queryset(self, request, queryset):

        if self.value() is None:
            return queryset

        elif self.value() == 'recent_link':
            last_week_date = datetime.now() - timedelta(days=7)
            return queryset.filter(links__created_date__gte=last_week_date)

        elif self.value() == 'no_link':
            return queryset.filter(links__isnull=True)
        # ya estoy filtrando los candidatos
        # tengo que resolver por que los voy a filtrar
        return queryset.filter(links__isnull=False)


class TagsListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = "tags"

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "tags"

    def lookups(self, request, model_admin):

        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """

        return [(tag.name, tag.name) for tag in Tag.objects.all()]

    def queryset(self, request, queryset):

        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """

        # si no hay valor te retorno todo el queryset sin filtrar
        if self.value() is None:
            return queryset

        print('[LOG] - TagListFilter.queryset - filtrando por >> ',
              self.value())
        return queryset.filter(tags__name=self.value())


# class LinkInline(TabularInline):
class LinkInline(StackedInline):

    model = Link
    extra = 0
    # readonly_fields = ['project', 'status', 'note']
    show_change_link = True

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Candidate)
class CandidateAdmin(ModelAdmin, ImportExportModelAdmin):

    import_form_class = ImportForm
    export_form_class = ExportForm
    export_form_class = SelectableFieldsExportForm

    # List

    date_hierarchy = 'updated_at'
    list_display = ['get_full_name',
                    'location',
                    'get_tags',
                    'get_last_updated_date',
                    ]

    list_filter = ['location',
                   HasLinkFilter,
                   TagsListFilter]

    search_fields = ['first_name', 'last_name', 'tags__name']

    # Change

    # filter_horizontal = ['tags']
    autocomplete_fields = ['tags']
    readonly_fields = ['user', 'created_at', 'updated_at']

    fieldsets = [
        (
            None,

            {'fields': [('first_name', 'last_name'),
                        ('current_title', 'current_company')]
             },
        ),
        (
            'Contact details',

            {
                "fields": [
                           ('phone', 'email'),
                           'location'],
            },
        ),
        (
            None,
            {
                'classes': ['collapse'],
                'fields': ['resume'],
            },
        ),
        (
            None,
            {
                'classes': ['collapse'],
                'fields': ['tags'],
            },
        ),
    ]

    inlines = [LinkInline]

    @admin.display(description='Last Updated')
    def get_last_updated_date(self, obj):
        return obj.updated_at.strftime('%d/%m/%Y')

    @admin.display(description='Full Name')
    def get_full_name(self, obj):
        return obj.first_name + ' ' + obj.last_name

    @admin.display(description='Tags')
    def get_tags(self, obj):

        tags = [(tag.name,) for tag in obj.tags.all()]
        span = '<span class="bg-primary-500 text-white text-xs font-medium me-2 px-2.5 py-0.5 rounded">{}</span>'
        return format_html_join(' ', span, tags)

    def get_search_results(self, request, queryset, search_term):

        if '+' not in search_term:
            return super().get_search_results(
                request,
                queryset,
                search_term,
            )

        search_terms = search_term.split('+')

        for term in search_terms:
            queryset = queryset.filter(
                    tags__name__icontains=term.strip()).distinct()

        # el segundo parametro le avisa si hay repetidos o son resultados limpios
        # si fuera False saldrian los repetidos
        return queryset, False

    def save_model(self, request, obj, form, change):

        obj.user = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):

        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        # Check if the user is a superuser
        if request.user.is_superuser:
            return super().formfield_for_foreignkey(db_field, request, **kwargs)

        # If the user is not a superuser

        if db_field.name == "location":
            # Las locations para ese usuario
            queryset = Location.objects.filter(user=request.user)
            kwargs["queryset"] = queryset 
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ProjectInline(TabularInline):

    # class ProjectInline(StackedInline):

    model = Project
    extra = 0
    show_change_link = True

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Company)
class CompanyAdmin(ModelAdmin):

    list_display = ['name', 'get_number_of_projects']
    search_fields = ['name']

    @admin.display(description='Number of projects')
    def get_number_of_projects(self, obj):
        return obj.projects.count()

    # Change
    exclude = ['user']
    inlines = [ProjectInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # if request.user.is_superuser:
        #    return qs
        return qs.filter(user=request.user)

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        super().save_model(request, obj, form, change)


class CandidateInline(StackedInline):

    model = Link
    extra = 0
    # readonly_fields = ['project', 'status', 'note']
    show_change_link = True

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Project)
class ProjectAdmin(ModelAdmin):

    list_display = ['position', 'company', 'location',
                    'get_creation_date', 'count_candidates',
                    'count_links'
                    ]

    # Change

    inlines = [CandidateInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # if request.user.is_superuser:
        #    return qs
        return qs.filter(company__user=request.user)

    @admin.display(description='Last Updated')
    def get_last_updated_date(self, obj):
        return obj.updated_at.strftime('%d/%m/%Y')

    @admin.display(description='Salary')
    def get_formatted_salary(self, obj):
        if obj.salary:
            return '$ {}'.format(obj.salary)
        return '-'

    @admin.display(description='Created (in days)')
    def get_creation_date(self, obj):
        if obj.created_at:
            delta = timezone.now() - obj.created_at
            print(delta)
            days = delta.days
            return days
        return '-'

    @admin.display(description='Candidates')
    def count_candidates(self, obj):
        # numero de candidatos LINKEADOS al project
        return obj.links.count()

    @admin.display(description='Interviews')
    def count_links(self, obj):
        # numero de candidatos linkeados al project con estado "Interviewing"
        return obj.links.filter(status=Link.StatusChoices.INTERVIEW).count()
        # return obj.links.filter(status__name="Interviewing").count()


@admin.register(Link)
class LinkAdmin(ModelAdmin):

    list_display = ['candidate', 'project', 'status', 'created_date']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # if request.user.is_superuser:
        #    return qs
        return qs.filter(project__company__user=request.user)


# TODO

# convertir a multi-user
