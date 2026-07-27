"""
Match engine: compara as skills de um candidato/solicitação com os requisitos da vaga.
Score: 0–100%
  - Skills obrigatórias correspondem a 70% do score
  - Skills desejáveis correspondem a 30% do score
"""


def calculate_match(skills_ids, job_opening):
    """
    :param skills_ids: conjunto (set ou queryset) de IDs de skills do candidato
    :param job_opening: instância de JobOpening
    :return: float de 0.0 a 100.0
    """
    candidate_set = set(skills_ids)

    required = set(job_opening.required_skills.values_list('id', flat=True))
    desired  = set(job_opening.desired_skills.values_list('id', flat=True))

    if not required and not desired:
        return 0.0

    if required:
        req_score = len(required & candidate_set) / len(required)
    else:
        req_score = 1.0  # Sem obrigatórias → pontuação máxima nesse critério

    if desired:
        des_score = len(desired & candidate_set) / len(desired)
    else:
        des_score = 0.0

    weight_req = 0.70 if required else 0.0
    weight_des = 0.30 if desired  else 0.0

    # Normalizar pesos para somarem 1
    total_weight = weight_req + weight_des
    if total_weight == 0:
        return 0.0

    score = (req_score * weight_req + des_score * weight_des) / total_weight
    return round(score * 100, 1)


def skill_breakdown(skills_ids, job_opening):
    """
    Retorna dicionário com listas de skills em comum e skills faltantes.
    Útil para o painel de match do RH.
    """
    candidate_set = set(skills_ids)

    from .models import Skill

    required = job_opening.required_skills.all()
    desired  = job_opening.desired_skills.all()

    matched_required  = [s for s in required if s.id in candidate_set]
    missing_required  = [s for s in required if s.id not in candidate_set]
    matched_desired   = [s for s in desired  if s.id in candidate_set]
    missing_desired   = [s for s in desired  if s.id not in candidate_set]

    return {
        'matched_required': matched_required,
        'missing_required': missing_required,
        'matched_desired':  matched_desired,
        'missing_desired':  missing_desired,
    }
