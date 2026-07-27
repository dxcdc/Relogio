from django.contrib import admin
from .models import (
    JobTitle, JobCategory, EmploymentStatus, Subunit, LegalEntity, Location,
    WorkShift, PayGrade, CurrencyType, Nationality, Education, Skill, Language,
    License, Membership, City, Province, Country
)

@admin.register(JobTitle, JobCategory, EmploymentStatus, Subunit, LegalEntity, Location,
                WorkShift, PayGrade, CurrencyType, Nationality, Education, Skill, Language,
                License, Membership, City, Province, Country)
class GenericAdmin(admin.ModelAdmin):
    pass
