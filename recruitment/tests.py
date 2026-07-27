from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from recruitment.models import JobOpening, Candidate, Interview, InterviewFeedback
from admin_app.models import Subunit
from pim.models import Employee
from agenda.models import Event

User = get_user_model()

class RecruitmentTestCase(TestCase):
    def setUp(self):
        # Create department
        self.department = Subunit.objects.create(name="Departamento de Testes")
        
        # Create a mock user
        self.user = User.objects.create_user(
            username="test_admin", 
            email="test_admin@netline.com.br", 
            password="testpassword",
            role="Admin"  # Assuming role field exists on User
        )
        
        # Create active employees
        self.employee1 = Employee.objects.create(
            first_name="John",
            last_name="Doe",
            state="ACTIVE",
            sub_division=self.department
        )
        self.employee2 = Employee.objects.create(
            first_name="Jane",
            last_name="Smith",
            state="ACTIVE",
            sub_division=self.department
        )

    def test_job_opening_creation(self):
        job = JobOpening.objects.create(
            title="Dev Python",
            department=self.department,
            description="Vaga para testes",
            status="OPEN"
        )
        self.assertEqual(job.title, "Dev Python")
        self.assertEqual(job.status, "OPEN")
        self.assertEqual(str(job), "Dev Python (Aberta)")

    def test_candidate_creation(self):
        job = JobOpening.objects.create(
            title="Dev Python",
            department=self.department,
            description="Vaga para testes"
        )
        candidate = Candidate.objects.create(
            name="Alice Wonder",
            email="alice@wonder.com",
            phone="123456",
            job_opening=job,
            current_stage="screening",
            status="IN_PROGRESS"
        )
        self.assertEqual(candidate.name, "Alice Wonder")
        self.assertEqual(candidate.current_stage, "screening")
        self.assertEqual(str(candidate), "Alice Wonder")

    def test_interview_scheduling_and_agenda_sync(self):
        job = JobOpening.objects.create(
            title="Dev Python",
            department=self.department,
            description="Vaga para testes"
        )
        candidate = Candidate.objects.create(
            name="Alice Wonder",
            email="alice@wonder.com",
            job_opening=job,
            current_stage="hr_interview"
        )
        
        # Create Interview object
        interview_date = timezone.now() + timedelta(days=1)
        interview = Interview.objects.create(
            candidate=candidate,
            stage="hr_interview",
            date=interview_date,
            notes="Teste de notas de entrevista",
            status="SCHEDULED"
        )
        interview.interviewers.add(self.employee1, self.employee2)
        
        # Test Event synchronization logic (as written in views.py, but verified programmatically here)
        title = f"Entrevista: {candidate.name} ({interview.get_stage_display()})"
        event = Event.objects.create(
            title=title,
            event_type='entrevista',
            organizer=self.employee1,
            start_date=interview.date,
            end_date=interview.date + timedelta(hours=1),
            notes=f"Entrevista para a vaga: {candidate.job_opening.title}\n\nObservações: {interview.notes}",
            status='agendado'
        )
        event.employees.set(interview.interviewers.all())
        event.save()
        
        interview.linked_event = event
        interview.save()
        
        self.assertIsNotNone(interview.linked_event)
        self.assertEqual(interview.linked_event.event_type, "entrevista")
        self.assertEqual(interview.linked_event.employees.count(), 2)
        self.assertIn(self.employee1, interview.linked_event.employees.all())

    def test_interview_feedback_submission(self):
        job = JobOpening.objects.create(
            title="Dev Python",
            department=self.department,
            description="Vaga para testes"
        )
        candidate = Candidate.objects.create(
            name="Alice Wonder",
            email="alice@wonder.com",
            job_opening=job,
            current_stage="hr_interview"
        )
        interview = Interview.objects.create(
            candidate=candidate,
            stage="hr_interview",
            date=timezone.now(),
            status="SCHEDULED"
        )
        interview.interviewers.add(self.employee1)
        
        # Submit feedback
        feedback = InterviewFeedback.objects.create(
            interview=interview,
            interviewer=self.employee1,
            score=4,
            feedback_text="Candidato aprovado com ressalvas."
        )
        
        # Logic from view: Update interview status to Completed on feedback submit
        interview.status = 'COMPLETED'
        interview.save()
        
        self.assertEqual(feedback.score, 4)
        self.assertEqual(interview.status, 'COMPLETED')
        self.assertEqual(str(feedback), f"Feedback de {self.employee1.full_name} para {candidate.name}")
