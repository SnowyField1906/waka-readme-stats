from enum import Enum
from typing import Dict, Tuple, List
from datetime import datetime

from pytz import timezone, utc

from manager_environment import EnvironmentManager as EM


DAY_TIME_EMOJI = ["🌞", "🌆", "🌃", "🌙"]  # Emojis, representing different times of day.
DAY_TIME_NAMES = ["Morning", "Daytime", "Evening", "Night"]  # Localization identifiers for different times of day.
WEEK_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]  # Localization identifiers for different days of week.


class Symbol(Enum):
    VERSION_1 = "█", "░"
    VERSION_2 = "⣿", "⣀"
    VERSION_3 = "⬛", "⬜"

    @staticmethod
    def get_symbols(version: int) -> Tuple[str, str]:
        return Symbol[f"VERSION_{version}"].value


def make_graph(percent: float):
    done_block, empty_block = Symbol.get_symbols(EM.SYMBOL_VERSION)
    percent_quart = round(percent / 4)
    return f"{done_block * percent_quart}{empty_block * (25 - percent_quart)}"


def make_list(data: List = None, names: List[str] = None, texts: List[str] = None, percents: List[float] = None, top_num: int = 7, sort: bool = True) -> str:
    if data is not None:
        names = [value for item in data for key, value in item.items() if key == "name"] if names is None else names
        texts = [value for item in data for key, value in item.items() if key == "text"] if texts is None else texts
        percents = [value for item in data for key, value in item.items() if key == "percent"] if percents is None else percents

    banned_names = ["Other", "Unknown", "Unknown OS", "Unknown Language"]

    for banned_name in banned_names:
        if banned_name in names:
            index = names.index(banned_name)
            names.pop(index)
            texts.pop(index)
            percents.pop(index)

    data = list(zip(names, texts, percents))
    top_data = sorted(data[:top_num], key=lambda record: record[2], reverse=True) if sort else data[:top_num]
    data_list = [f"{n[:25]}{' ' * (25 - len(n))}{t}{' ' * (20 - len(t))}{make_graph(p)}   {p:05.2f} % " for n, t, p in top_data]
    data_list = [row for row in data_list if float(row.split()[-2]) >= 0.7]

    return "\n".join(data_list)


async def make_commit_day_time_list(time_zone: str, repositories: Dict, commit_dates: Dict) -> str:
    stats = str()
    day_times = [0] * 4  # 0 - 6, 6 - 12, 12 - 18, 18 - 24
    week_days = [0] * 7  # Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday

    for repository in repositories:
        if repository["name"] not in commit_dates.keys():
            continue

        for committed_date in [commit_date for branch in commit_dates[repository["name"]].values() for commit_date in branch.values()]:
            local_date = datetime.strptime(committed_date, "%Y-%m-%dT%H:%M:%SZ")
            date = local_date.replace(tzinfo=utc).astimezone(timezone(time_zone))

            day_times[date.hour // 6] += 1
            week_days[date.isoweekday() - 1] += 1

    sum_day = sum(day_times)
    sum_week = sum(week_days)
    day_times = day_times[1:] + day_times[:1]

    if EM.SHOW_COMMIT:
        dt_names = [f"{DAY_TIME_EMOJI[i]} {DAY_TIME_NAMES[i]}" for i in range(len(day_times))]
        dt_texts = [f"{day_time} commits" for day_time in day_times]
        dt_percents = [0 if sum_day == 0 else round((day_time / sum_day) * 100, 2) for day_time in day_times]
        title = "I'm an Early" if sum(day_times[0:2]) >= sum(day_times[2:4]) else "I'm a Night"
        stats += f"**{title}** \n\n```text\n{make_list(names=dt_names, texts=dt_texts, percents=dt_percents, top_num=7, sort=False)}\n```\n"

    if EM.SHOW_DAYS_OF_WEEK:
        wd_names = [week_day for week_day in WEEK_DAY_NAMES]
        wd_texts = [f"{week_day} commits" for week_day in week_days]
        wd_percents = [0 if sum_week == 0 else round((week_day / sum_week) * 100, 2) for week_day in week_days]
        title = f"I'm most productive on {wd_names[wd_percents.index(max(wd_percents))]}"
        stats += f"📅 **{title}** \n\n```text\n{make_list(names=wd_names, texts=wd_texts, percents=wd_percents, top_num=7, sort=False)}\n```\n"

    return stats


def make_language_per_repo_list(repositories: Dict) -> str:
    language_count = dict()
    repos_with_language = [repo for repo in repositories if repo["primaryLanguage"] is not None]
    for repo in repos_with_language:
        language = repo["primaryLanguage"]["name"]
        language_count[language] = language_count.get(language, {"count": 0})
        language_count[language]["count"] += 1

    names = list(language_count.keys())
    texts = [f"{language_count[lang]['count']} {'repo' if language_count[lang]['count'] == 1 else 'repos'}" for lang in names]
    percents = [round(language_count[lang]["count"] / len(repos_with_language) * 100, 2) for lang in names]

    top_language = max(list(language_count.keys()), key=lambda x: language_count[x]["count"])
    title = f"**I mostly code in {top_language}** \n\n"
    
    return f"{title}```text\n{make_list(names=names, texts=texts, percents=percents)}\n```\n\n"
