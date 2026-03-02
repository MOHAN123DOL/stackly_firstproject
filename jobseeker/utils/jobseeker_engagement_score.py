

def calculate_engagement_score(applied, saved, alerts):
        score = 0

        score += applied * 5
        score += saved * 2
        score += alerts * 3

        return min(score, 100)  # cap at 100