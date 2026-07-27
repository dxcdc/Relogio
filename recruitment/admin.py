from django.contrib import admin
from .models import Skill, JobOpening, Candidate, PublicApplication, Interview, InterviewFeedback


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display  = ['name', 'category', 'icon']
    list_filter   = ['category']
    search_fields = ['name']
    ordering      = ['category', 'name']


@admin.register(JobOpening)
class JobOpeningAdmin(admin.ModelAdmin):
    list_display  = ['title', 'department', 'status', 'created_at']
    list_filter   = ['status', 'department']
    search_fields = ['title']
    filter_horizontal = ['required_skills', 'desired_skills']


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display  = ['name', 'email', 'job_opening', 'current_stage', 'status', 'match_score']
    list_filter   = ['status', 'current_stage']
    search_fields = ['name', 'email']
    filter_horizontal = ['skills']


@admin.register(PublicApplication)
class PublicApplicationAdmin(admin.ModelAdmin):
    list_display  = ['name', 'email', 'job_opening', 'match_score', 'status', 'created_at']
    list_filter   = ['status', 'job_opening']
    search_fields = ['name', 'email']
    filter_horizontal = ['skills']


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display  = ['candidate', 'stage', 'date', 'status']
    list_filter   = ['stage', 'status']


@admin.register(InterviewFeedback)
class InterviewFeedbackAdmin(admin.ModelAdmin):
    list_display  = ['interview', 'interviewer', 'score', 'created_at']
