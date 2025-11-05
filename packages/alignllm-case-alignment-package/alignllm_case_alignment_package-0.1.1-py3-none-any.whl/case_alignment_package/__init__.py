import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def get_cosine_similarity(emb1, emb2):
    emb1 = emb1.reshape(1, -1) if emb1.ndim == 1 else emb1
    emb2 = emb2.reshape(1, -1) if emb2.ndim == 1 else emb2
    similarity = cosine_similarity(emb1, emb2)
    return similarity[0, 0]

def get_case_alignment(case_embs, case_base):
    emb1, emb2 = case_embs
    emb1 = emb1.reshape(1, -1) if emb1.ndim == 1 else emb1
    emb2 = emb2.reshape(1, -1) if emb2.ndim == 1 else emb2
    alignment_scores = []
    for past_case in case_base:
        past_prob_emb, past_solution_emb = past_case
        past_prob_emb = past_prob_emb.reshape(1, -1) if past_prob_emb.ndim == 1 else past_prob_emb
        past_solution_emb = past_solution_emb.reshape(1, -1) if past_solution_emb.ndim == 1 else past_solution_emb
        prob_similarity = cosine_similarity(emb1, past_prob_emb)
        solution_similarity = cosine_similarity(emb2, past_solution_emb)
        alignment_score = (prob_similarity + solution_similarity) / 2.0
        alignment_scores.append(alignment_score)
    return (sum(alignment_scores) / len(alignment_scores))[0][0]

def get_weighted_case_alignment(case_embs, case_base):
    emb1, emb2 = case_embs
    emb1 = emb1.reshape(1, -1) if emb1.ndim == 1 else emb1
    emb2 = emb2.reshape(1, -1) if emb2.ndim == 1 else emb2
    alignment_scores = []
    weights = []
    for past_case in case_base:
        past_prob_emb, past_solution_emb = past_case
        past_prob_emb = past_prob_emb.reshape(1, -1) if past_prob_emb.ndim == 1 else past_prob_emb
        past_solution_emb = past_solution_emb.reshape(1, -1) if past_solution_emb.ndim == 1 else past_solution_emb
        prob_similarity = cosine_similarity(emb1, past_prob_emb)[0][0]
        solution_similarity = cosine_similarity(emb2, past_solution_emb)[0][0]
        alignment_score = (prob_similarity + solution_similarity) / 2.0
        alignment_scores.append(alignment_score)
        weights.append(prob_similarity)
    total_weight = sum(weights)
    if total_weight == 0:
        return 0
    normalized_weights = [w / total_weight for w in weights]
    weighted_alignment_score = sum(a * w for a, w in zip(alignment_scores, normalized_weights))
    return weighted_alignment_score