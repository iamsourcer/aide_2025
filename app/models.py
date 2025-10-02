from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.humanize.templatetags.humanize import naturaltime




# Create your models here.


class Company(models.Model):
    name = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="companies")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Companies"


class CompanyContact(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(max_length=254, null=True, blank=True)
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="company_contacts"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="company_contacts")


    def clean(self):
        if self.phone is None and self.email is None:
            raise ValidationError(("Please provide phone or email"))

    def __str__(self):
        return self.first_name + " " + self.last_name + " | " + self.company.name

    # ambos pueden unicos pero no a la vez
    class Meta:
        unique_together = ["phone", "email"]
        verbose_name_plural = "Company Contacts"


class Location(models.Model):
    name = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="locations")

    # def __str__(self):
    #    if self.user_id:
    #        return self.name

    def __str__(self):
        try:
            return f"{self.name}"
        except Exception:
            return self.name


class Project(models.Model):
    class StatusChoices(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    name = models.CharField(max_length=50, unique=True)
    position = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20, choices=StatusChoices.choices, default=StatusChoices.OPEN
    )
    location = models.ForeignKey(
        Location,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="projects",
    )
    remote = models.BooleanField(default=False)
    salary = models.PositiveIntegerField(null=True, blank=True)
    fee = models.PositiveIntegerField(null=True, blank=True)
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="projects"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')


    def __str__(self):
        return self.name + ' - ' + self.company.name

    def is_open(self):
        return self.candidates


class Tag(models.Model):
    name = models.CharField(max_length=30, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tags")

    def __str__(self):
        return self.name


class Candidate(models.Model):

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    email = models.EmailField(max_length=254)
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="candidates",
    )

    current_title = models.CharField(max_length=50, null=True, blank=True)
    current_company = models.CharField(max_length=50, null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="candidates")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="candidates")

    resume = models.FileField("resume", null=True, blank=True, default=None)
    parsed_resume = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.first_name + " " + self.last_name

    # Pueden ser opcionales tanto email como phone pero no los dos a la vez

    def clean(self):
        if self.phone is None and self.email is None:
            raise ValidationError(("Please provide phone or email"))

    # ambos pueden unicos pero no a la vez
    class Meta:
        unique_together = ["phone", "email"]
        ordering = ["-updated_at"]
    
    # hacemos el override del save - si hay resume parseamos y metemos todo en parsed_resume 
    # def save(self, *args, **kwargs):
    #     if not self.resume:  

    #     super().save(*args, **kwargs)

class Link(models.Model):
    class StatusChoices(models.TextChoices):
        SOURCED = "sourced", "Sourced"
        LEAD_APPLIED = "lead-applied", "Lead/Applied"
        OUTREACH_LINKEDIN_EMAIL = "outreach", "Outreach - Linkedin/Email"
        PHONE_SCREEN = "phone screen", "Phone Screen"
        SUBMITTED = "submitted", "Submitted"
        REJECTED = "rejected", "Rejected"
        INTERVIEW = "interview", "Interview"
        ONSITE = "onsite", "Onsite"
        HIRED = "hired", "Hired"

    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name="links")

    candidate = models.ForeignKey(Candidate,
                                  on_delete=models.CASCADE,
                                  related_name="links")

    project = models.ForeignKey(Project,
                                on_delete=models.CASCADE,
                                related_name="links",
                                limit_choices_to={'status': 'open'})

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    status = models.CharField(
        max_length=30, choices=StatusChoices.choices, default=StatusChoices.SOURCED
    )

    
    def __str__(self):
        return (
            self.project.name
            + " | "
            + "Candidate: "
            + self.candidate.first_name
            + " "
            + self.candidate.last_name
        )

    class Meta:
        unique_together = ['candidate', 'project']
        verbose_name_plural = "Links"
    
    

class Note(models.Model):

    text = models.TextField()
    link = models.ForeignKey(Link, on_delete=models.CASCADE, related_name='notes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name} - {naturaltime(self.updated_at)}'



