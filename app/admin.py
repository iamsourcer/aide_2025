from django import forms
from django.contrib import admin, messages
from django.utils import timezone
from django.utils.html import format_html_join, format_html
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from django.core.exceptions import ValidationError 
from django.urls import reverse
from .models import Company, CompanyContact, Location, Project, Candidate, Tag, Note

# from .models import Status, Link
from .models import Link
from datetime import datetime, timedelta, date

#############

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group
from django.contrib.humanize.templatetags.humanize import naturaltime

from unfold.admin import ModelAdmin, StackedInline, TabularInline
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.contrib.inlines.admin import NonrelatedTabularInline, NonrelatedStackedInline
from unfold.decorators import action, display
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import (
    ExportForm,
    ImportForm,
    SelectableFieldsExportForm,
)


admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    pass

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass

@admin.register(Location)
class LocationAdmin(ModelAdmin):

    exclude = ["user"]
    search_fields = ["name"]

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user
        obj.save()
        # super().save_model(request, obj, form, change)

@admin.register(CompanyContact)
class CompanyContactAdmin(ModelAdmin):
    list_display = ["first_name", "last_name", "company__name"]

    # def get_queryset(self, request):
    #     qs = super().get_queryset(request)
    #     if request.user.is_superuser:
    #         return qs
    #     return qs.filter(company__user=request.user)

@admin.register(Tag)
class TagAdmin(ModelAdmin):
    search_fields = ["name"]

    # readonly_fields = ["user"]
    exclude = ["user"] 

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        super().save_model(request, obj, form, change)

class ProjectCandidateFilter(admin.SimpleListFilter):
    title = "Project"
    parameter_name = "project"

    def lookups(self, request, model_admin):
        open_projects = Project.objects.filter(status=Project.StatusChoices.OPEN)
        return [(p.id, p.name) for p in open_projects]

    def queryset(self, request, queryset):
        if self.value():
          return queryset.filter(
                links__project__id=self.value(),
                links__project__status=Project.StatusChoices.OPEN,
            ).distinct()
        return queryset

class OwnerCandidateFilter(admin.SimpleListFilter):
    title = "Owner"
    parameter_name = 'owner'

    def lookups(self, request, model_admin):

        return [
            ("mine", "Mine"),
        ]
    
    def queryset(self, request, queryset):
        
        if self.value() == 'mine':
            print('[LOG] - OwnerCandidateFilter - user_logged >', request.user)
            print(queryset.filter(user=request.user))
            return queryset.filter(user=request.user)
        return queryset

class HasLinkFilter(admin.SimpleListFilter):

    title = "Links"
    parameter_name = "link"

    def lookups(self, request, model_admin):
        return [
            ("has_link", "Linked"),
            ("no_link", "Not linked"),
        ]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset

        # elif self.value() == "recent_link":
        #     last_week_date = datetime.now() - timedelta(days=7)
        #     return queryset.filter(links__created_date__gte=last_week_date)

        elif self.value() == "has_link":
            return queryset.filter(links__isnull=False).distinct()

        elif self.value() == "no_link":
            return queryset.filter(links__isnull=True)

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

        print("[LOG] - TagListFilter.queryset - filtrando por >> ", self.value())
        return queryset.filter(tags__name=self.value())

class CandidateLinkInline(TabularInline):
    model = Link
    extra = 0
    fields = ['project', 'status']
    tab = True

    # show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('project',)
        return self.readonly_fields

class CandidateNoteInline(NonrelatedStackedInline):
    model = Note
    fields = ["link", "text"]  # Ignore property to display all fields
    readonly_fields = ['link']
    extra = 0
    tab = True
    


    def get_form_queryset(self, obj):
        """
        Gets all nonrelated objects needed for inlines. Method must be implemented.
        """
        # print('[LOG] - Esto es un log de CandidateNoteInLine', obj)
        candidato = obj
        links = candidato.links.all()

        # creamos un queryset vacio
        notes = Note.objects.none()

        for l in links:
            notes = notes.union(l.notes.all())
        return notes 
        # return self.model.objects.all()

    def save_new_instance(self, parent, instance):
        """
        Extra save method which can for example update inline instances based on current
        main model object. Method must be implemented.
        """
        pass 
    
    
    class Media:
        css = {    # ↓ ↓ ↓ ↓ ↓ ↓ Here ↓ ↓ ↓ ↓ ↓ ↓
            "all": ("app/css/link_note_admin.css",)
        }   

@admin.register(Candidate)
class CandidateAdmin(ModelAdmin, ImportExportModelAdmin):

    import_form_class = ImportForm
    export_form_class = ExportForm
    export_form_class = SelectableFieldsExportForm

    # List

    date_hierarchy = "updated_at"
    list_display = [
        "get_full_name",
        "location",
        "get_tags",
        "get_last_updated_date",
        "get_owner",
    ]

    list_filter = [
        OwnerCandidateFilter,
        ProjectCandidateFilter,
        HasLinkFilter,
    ]

    search_fields = ["first_name", "last_name", "location__name", "tags__name"]

    # Change

    # filter_horizontal = ['tags']
    autocomplete_fields = ["tags", "location"]
    readonly_fields = ["user", "created_at", "updated_at"]

    fieldsets = [
        (
            "Personal Info",
            {
                "fields": [
                    ("first_name", "last_name"),
                    ("current_title", "current_company"),
                ]
            },
        ),
        (
            "Contact details",
            {
                "classes": ["collapse", "tab"],
                "fields": [("phone", "email"), "location"],
            },
        ),
                (
            "Tags",
            {
                "classes": ["tab"],
                "fields": ["tags"],
            },
        ),
        (
            "Files",
            {
                "classes": ["tab"],
                "fields": ["resume"],
            },
        ),

    ]

    inlines = [CandidateLinkInline, CandidateNoteInline]

    @admin.display(description="Last Updated")
    def get_last_updated_date(self, obj):
        return obj.updated_at.strftime("%d/%m/%Y")

    @admin.display(description="Owner")
    def get_owner(self, obj):
        return obj.user.first_name

    @admin.display(description="Full Name")
    def get_full_name(self, obj):
        return obj.first_name + " " + obj.last_name

    @admin.display(description="Tags")
    def get_tags(self, obj):
        tags = [(tag.name,) for tag in obj.tags.all()]
        span = '<span class="bg-primary-500 text-white text-xs font-medium me-2 px-2.5 py-0.5 rounded">{}</span>'
        return format_html_join(" ", span, tags)

    def get_list_display(self, request):
        user_filtered = request.GET.get("owner", None)
        is_user_filtered = user_filtered is not None

        list_display = super().get_list_display(request)
        if is_user_filtered and "get_owner" in list_display:
            list_display.remove("get_owner")

        elif not is_user_filtered and "get_owner" not in list_display:
            list_display.append("get_owner")
        return list_display

    def get_search_results(self, request, queryset, search_term):
        print('[LOG] - search terms:', search_term)
        SEARCH_OPERATOR = '|'
        if SEARCH_OPERATOR not in search_term:
            return super().get_search_results(
                request,
                queryset,
                search_term,
            )

        print('[LOG] - Procesando busquedando con operador +')
        search_terms = search_term.split(SEARCH_OPERATOR)

        for term in search_terms:
            term = term.strip()
            queryset = queryset.filter(tags__name__icontains=term).distinct()
            print('[LOG] - term:', term, 'Largo Queryset:', len(queryset))
        # el segundo parametro le avisa si hay repetidos o son resultados limpios
        # si fuera False saldrian los repetidos
        return queryset, False

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        super().save_model(request, obj, form, change)
    

class CompanyProjectInline(TabularInline):
    # class ProjectInline(StackedInline):

    model = Project
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Company)
class CompanyAdmin(ModelAdmin):
    list_display = ["name", "get_number_of_projects"]
    search_fields = ["name"]

    @admin.display(description="Number of projects")
    def get_number_of_projects(self, obj):
        return obj.projects.count()

    # Change
    exclude = ["user"]
    inlines = [CompanyProjectInline]

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        super().save_model(request, obj, form, change)


class ProjectLinkInline(TabularInline):
    
    model = Link
    extra = 0
    fields = ['candidate', 'status']

    # show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('candidate',)
        return self.readonly_fields


@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    search_fields = ["position", "company__name"]
    list_display = [
        "position",
        "company",
        "get_creation_date",
        "count_candidates",
        "get_owner",
    ]

    exclude = ['user']
    # Change
    inlines = [ProjectLinkInline]
    

    @admin.display(description="Last Updated")
    def get_last_updated_date(self, obj):
        return obj.updated_at.strftime("%d/%m/%Y")

    @admin.display(description="Salary")
    def get_formatted_salary(self, obj):
        if obj.salary:
            return "$ {}".format(obj.salary)
        return "-"

    @admin.display(description="Created")
    def get_creation_date(self, obj):
        return naturaltime(obj.created_at)

    @admin.display(description="Candidates")
    def count_candidates(self, obj):
        # numero de candidatos LINKEADOS al project
        return obj.links.count()

    @admin.display(description="Owner")
    def get_owner(self, obj):
        return obj.user.first_name
    
    def save_model(self, request, obj, form, change):
        obj.user = request.user
        super().save_model(request, obj, form, change)


@admin.register(Note)
class NotesAdmin(ModelAdmin):
    list_display = ["link__project", "link__candidate", "updated_at", "get_owner"]
    exclude = ["user"]
    readonly_fields = []

    # Corregimos la version readonly del QuillField (por default muestra JSON)    
    @admin.display(description="Text")
    def quillField_readonly_text(self, obj):
        return format_html(obj.text.html)

    @admin.display(description="Owner")
    def get_owner(self, obj):
        return obj.user.first_name
    
    # sobreescrituras 

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        super().save_model(request, obj, form, change)
    
    # Puedo EDITAR solo si es Owner
    def has_change_permission(self, request, obj=None):

        if not obj:
            return False
        if request.user.is_superuser:
            return True
        if obj.user == request.user:
            return True
        return False
    
    # puedo BORRAR solo si es owner del link
    def has_delete_permission(self, request, obj=None):

        if not obj:
            return False
        if request.user.is_superuser:
            return True
        if obj.link.user == request.user:
            return True
        return False

    # Corregimos la version readonly del QuillField (por default muestra JSON)
    def get_readonly_fields(self, request, obj=None):
        readonly = super().get_readonly_fields(request, obj)
        
        if not obj:
            return [] # por default no hay campos readonly
        if obj.user != request.user:
            if "quillField_readonly_text" not in readonly: 
                readonly.append("quillField_readonly_text")
        else:
            if "quillField_readonly_text" in readonly: 
                readonly.remove("quillField_readonly_text")
        return readonly

    # Excluimos "text" original porque ya estamos mostrando el QuillField en version readonly
    def get_exclude(self, request, obj=None):
        exclude = super().get_exclude(request, obj)
        
        if not obj:
            return ["user"]
        if obj.user != request.user:
            if "text" not in exclude:
                exclude.append('text')
        else:
            if "text" in exclude:
                exclude.remove('text')
        return exclude



class LinkNotesInline(TabularInline):
    model = Note
    extra = 0
    
    #fields = ['text']
    exclude = ['user', 'text']
    readonly_fields = ['quillField_readonly_text', 'edit_button']

    # Corregimos la version readonly del QuillField (por default muestra JSON)    
    @admin.display(description="Text")
    def quillField_readonly_text(self, obj):
        return format_html(obj.text.html)
    
    @admin.display(description="Edit")
    def edit_button(self, obj):
        url = reverse('admin:app_note_change', args=[obj.id])
        
        return format_html(f'<a class="related-widget-wrapper-link view-related bg-white border cursor-pointer flex items-center h-9.5 justify-center ml-2 rounded shadow-sm shrink-0 text-gray-400 text-sm w-9.5 hover:text-gray-700 dark:bg-gray-900 dark:border-gray-700 dark:text-gray-500 dark:hover:text-gray-200" href="{url}"><span class="material-symbols-outlined text-sm">visibility</span></a>')


    def has_add_permission(self, request, obj=None):
        return False

    # Puedo EDITAR solo si es Owner
    def has_change_permission(self, request, obj=None):

        if request.user.is_superuser:
            return True

        return False
    
    def has_delete_permission(self, request, obj=None):
        if not obj:
            return True
        if request.user.is_superuser:
            return True   
        return False

    # Corregimos la version readonly del QuillField (por default muestra JSON)
    # def get_readonly_fields(self, request, obj=None):
    #     readonly = super().get_readonly_fields(request, obj)

    #     if obj and "quillField_readonly_text" not in readonly: 
    #         print('[LOG] - LinkNotesInline.get_readonly_fields: quillField Readonly Mejorado')
    #         # este append no hace nada, Investigar!
    #         readonly.append("quillField_readonly_text")
    #     return readonly

    # Excluimos "text" original porque ya estamos mostrando el QuillField en version readonly
    # def get_exclude(self, request, obj=None):
    #     exclude = super().get_exclude(request, obj)
        
    #     if obj and "text" not in exclude:
    #             exclude.append('text')
    #     return exclude

    class Media:
        css = {    # ↓ ↓ ↓ ↓ ↓ ↓ Here ↓ ↓ ↓ ↓ ↓ ↓
            "all": ("app/css/link_note_admin.css",)
        }      

    
@admin.register(Link)
class LinkAdmin(ModelAdmin):
    fieldsets = [
        (None, {'fields': [('candidate', 'project', 'user')],}),
        (None, {'fields': ['status'],}),
    ] 
    
    list_display = ["candidate",
                    "project",
                    "status",
                    "get_notes_counter",
                    "get_last_updated_date",
                    "get_owner",
    ]
    
    search_fields = ['candidate__first_name', 'candidate__last_name', 'project__name', 'project__company__name']
    ordering = ['-updated_at']
    readonly_fields = ["user"]
    autocomplete_fields = ["candidate", "project"]
    list_filter = [OwnerCandidateFilter, 'status']
    inlines = [LinkNotesInline]

    @admin.display(description="Notes")
    def get_notes_counter(self, obj):
        return obj.notes.count()

    @admin.display(description="Last Updated")
    def get_last_updated_date(self, obj):
        #time_difference = date.today() - obj.updated_date
        # return f'{time_difference.days} days ago'
        return naturaltime(obj.updated_at)

    @admin.display(description="Owner")
    def get_owner(self, obj):
        return obj.user.first_name

    # Esto probablemente tenga que ver con los NoteinLine
    # def save_formset(self, request, form, formset, change):
    #     instances = formset.save(commit=False)

    #     for instance in instances:
    #         instance.user = request.user
    #         instance.save()
    #     formset.save_m2m()

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        super().save_model(request, obj, form, change)
    
    # Esta es la manera horrible que tiene Django
    def get_list_display(self, request):
        user_filtered = request.GET.get("owner", None)
        is_user_filtered = user_filtered is not None

        list_display = super().get_list_display(request)
        if is_user_filtered and "get_owner" in list_display:
            list_display.remove("get_owner")

        elif not is_user_filtered and "get_owner" not in list_display:
            list_display.append("get_owner")
        return list_display

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ['candidate', 'project']
        return self.readonly_fields
    
    def has_delete_permission(self, request, obj=None):
        if not obj:
            return False
        if request.user.is_superuser:
            return True
        if obj.user == request.user:
            return obj.notes.count() == 0  # borramos link si no tiene notas
        return False
