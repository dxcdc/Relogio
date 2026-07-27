from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from django.db.models import Q
from .models import Survey, SurveyQuestion, SurveyResponse, SurveyAnswer

class PendingSurveyListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        emp = getattr(request.user, 'employee', None)
        if not emp:
            return Response([])

        qs = Survey.objects.filter(status='PUBLISHED')
        filtered_qs = []
        for s in qs:
            if s.target_type == 'ALL':
                filtered_qs.append(s.id)
            elif s.target_type == 'LEGAL_ENTITY' and getattr(emp, 'legal_entity_id', None) == s.target_legal_entity_id:
                filtered_qs.append(s.id)
            elif s.target_type == 'SUBUNIT' and getattr(emp, 'sub_division_id', None) == s.target_subunit_id:
                filtered_qs.append(s.id)
            elif s.target_type == 'CITY' and getattr(emp, 'city_id', None) == s.target_city_id:
                filtered_qs.append(s.id)
                
        answered_ids = SurveyResponse.objects.filter(employee=emp).values_list('survey_id', flat=True)
        now = timezone.now()
        
        pending_surveys = Survey.objects.filter(id__in=filtered_qs).exclude(id__in=answered_ids).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=now)
        ).order_by('-created_at')

        data = []
        for s in pending_surveys:
            data.append({
                'id': s.id,
                'title': s.title,
                'description': s.description,
                'is_anonymous': s.is_anonymous,
            })
            
        return Response(data)

class SurveyDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            survey = Survey.objects.get(pk=pk, status='PUBLISHED')
        except Survey.DoesNotExist:
            return Response({"error": "Pesquisa não encontrada"}, status=status.HTTP_404_NOT_FOUND)

        questions = survey.questions.all().order_by('order')
        questions_data = []
        for q in questions:
            questions_data.append({
                'id': q.id,
                'text': q.question_text,
                'question_type': q.question_type, 
                'options': [opt.strip() for opt in q.choices.split(';')] if q.choices else [],
                'is_required': q.is_required,
            })

        return Response({
            'id': survey.id,
            'title': survey.title,
            'description': survey.description,
            'is_anonymous': survey.is_anonymous,
            'questions': questions_data
        })

    def post(self, request, pk):
        emp = getattr(request.user, 'employee', None)
        if not emp:
            return Response({"error": "Usuário não vinculado a um funcionário."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            survey = Survey.objects.get(pk=pk, status='PUBLISHED')
        except Survey.DoesNotExist:
            return Response({"error": "Pesquisa não encontrada"}, status=status.HTTP_404_NOT_FOUND)

        if SurveyResponse.objects.filter(survey=survey, employee=emp).exists():
            return Response({"error": "Você já respondeu a esta pesquisa."}, status=status.HTTP_400_BAD_REQUEST)

        answers_data = request.data.get('answers', [])
        
        response_obj = SurveyResponse.objects.create(
            survey=survey,
            employee=emp
        )

        for ans in answers_data:
            question_id = ans.get('question_id')
            answer_text = ans.get('answer_text', '')
            try:
                question = SurveyQuestion.objects.get(id=question_id, survey=survey)
                ans_obj = SurveyAnswer(response=response_obj, question=question)
                
                if question.question_type == 'RATING_10' or question.question_type == 'RATING':
                    try:
                        ans_obj.rating_answer = int(float(str(answer_text)))
                    except ValueError:
                        pass
                elif question.question_type == 'MULTIPLE_CHOICE' or question.question_type == 'GOOD_BAD':
                    ans_obj.choice_answer = str(answer_text)[:255]
                else:
                    ans_obj.text_answer = str(answer_text)
                    
                ans_obj.save()
            except SurveyQuestion.DoesNotExist:
                continue

        return Response({"message": "Pesquisa enviada com sucesso!"})
