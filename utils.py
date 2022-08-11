from datetime import datetime


def get_current_semester():
    date = datetime.now()
    if datetime.now().month < 8:
        return 'P' + str(date.year)
    else:
        return 'A' + str(date.year)


def get_last_semesters(nb_semesters: int):
    current = get_current_semester()
    res = [current]
    season, year = current[0], int(current[1:])
    for _ in range(nb_semesters):
        season = 'P' if season == 'A' else 'A'
        if season == 'P':
            year -= 1
        res.append(season + str(year))
    return res
