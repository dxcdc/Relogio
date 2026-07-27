from django.urls import path
from . import views

urlpatterns = [
    # ── Job Openings (internal) ────────────────────────────────────────────
    path('jobs/',                             views.job_list,                  name='job_list'),
    path('jobs/create/',                      views.job_create,                name='job_create'),
    path('jobs/<int:pk>/edit/',               views.job_edit,                  name='job_edit'),
    path('jobs/<int:pk>/delete/',             views.job_delete,                name='job_delete'),

    # ── Metrics ────────────────────────────────────────────────────────────
    path('metrics/',                          views.recruitment_metrics,       name='recruitment_metrics'),

    # ── Pipeline ───────────────────────────────────────────────────────────
    path('pipeline/',                         views.candidate_pipeline,        name='candidate_pipeline'),
    path('pipeline/update/',                  views.update_candidate_stage_ajax, name='update_candidate_stage_ajax'),
    path('pipeline/onboard/<int:candidate_id>/', views.onboard_as_employee,    name='onboard_as_employee'),
    path('pipeline/onboard/<int:candidate_id>/email/', views.send_onboard_email, name='send_onboard_email'),

    # ── Candidates (internal CRUD) ─────────────────────────────────────────
    path('candidates/',                       views.candidate_list,            name='candidate_list'),
    path('candidates/create/',                views.candidate_create,          name='candidate_create'),
    path('candidates/<int:pk>/edit/',         views.candidate_edit,            name='candidate_edit'),
    path('candidates/<int:pk>/delete/',       views.candidate_delete,          name='candidate_delete'),
    path('candidates/<int:pk>/profile/',      views.candidate_profile,         name='candidate_profile'),

    # ── Interviews & Feedback ──────────────────────────────────────────────
    path('candidates/<int:candidate_pk>/schedule/', views.interview_schedule,  name='interview_schedule'),
    path('interviews/<int:interview_pk>/feedback/', views.interview_feedback_create, name='interview_feedback_create'),

    # ── Applications Review (internal RH) ─────────────────────────────────
    path('jobs/<int:job_pk>/applications/',    views.applications_review,      name='applications_review'),
    path('applications/<int:app_pk>/accept/',  views.application_accept,       name='application_accept'),
    path('applications/<int:app_pk>/reject/',  views.application_reject,       name='application_reject'),
    path('applications/<int:app_pk>/',         views.application_detail,       name='application_detail'),

    # ── PUBLIC PORTAL (no login) ───────────────────────────────────────────
    path('vagas/',                            views.public_job_list,           name='public_job_list'),
    path('vagas/<int:pk>/candidatar/',        views.public_apply,              name='public_apply'),
    path('vagas/obrigado/',                   views.apply_thanks,              name='apply_thanks'),

    # ── Skills Management ──────────────────────────────────────────────────
    path('skills/',                           views.skill_list,                name='skill_list'),
    path('skills/<int:pk>/delete/',           views.skill_delete,              name='skill_delete'),
]
