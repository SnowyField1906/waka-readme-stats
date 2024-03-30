"""
Readme Development Metrics With waka time progress
"""
from asyncio import run
from datetime import datetime
from typing import Dict
from urllib.parse import quote

from humanize import intword, naturalsize, intcomma

from manager_download import init_download_manager, DownloadManager as DM
from manager_environment import EnvironmentManager as EM
from manager_github import init_github_manager, GitHubManager as GHM
from manager_debug import init_debug_manager, DebugManager as DBM
from graphics_chart_drawer import create_loc_graph, GRAPH_PATH
from yearly_commit_calculator import calculate_commit_data
from graphics_list_formatter import make_list, make_commit_day_time_list, make_language_per_repo_list


async def get_waka_time_stats(repositories: Dict, commit_dates: Dict) -> str:
    stats = "📊 **Since my first \"Hello World!\", I have spent time on** \n\n```text\n"
    data = await DM.get_remote_json("waka_stats")

    if EM.SHOW_COMMIT or EM.SHOW_DAYS_OF_WEEK:
        stats += f"{await make_commit_day_time_list(data['data']['timezone'], repositories, commit_dates)}\n\n"

    if EM.SHOW_LANGUAGE:
        lang_list = make_list(data["data"]["languages"])
        stats += f"💬 Languages: \n{lang_list}\n\n"

    if EM.SHOW_EDITORS:
        edit_list = make_list(data["data"]["editors"])
        stats += f"🔥 Editors: \n{edit_list}\n\n"

    if EM.SHOW_OS:
        os_list = make_list(data["data"]["operating_systems"])
        stats += f"💻 Operating Systems: \n{os_list}\n\n"

    return f"{stats[:-1]}```\n\n"


async def get_short_github_info() -> str:
    stats = "**🐱 My GitHub Data** \n\n"
    data = await DM.get_remote_json("github_stats")

    disk_usage = "Used in GitHub's Storage" % naturalsize(GHM.USER.disk_usage)
    stats += f"> 📦 {disk_usage} \n > \n"

    contributions = "Contributions in the year" % intcomma(data["years"][0]["total"]), data["years"][0]["year"]
    stats += f"> 🏆 {contributions}\n > \n"

    opted_to_hire = GHM.USER.hireable
    if opted_to_hire:
        stats += "> 💼 Opted to Hire\n > \n"
    else:
        stats += "> 🚫 Not Opted to Hire\n > \n"

    public_repo = GHM.USER.public_repos
    if public_repo != 1:
        stats += f"> 📜 {'public repositories' % public_repo} \n > \n"
    else:
        stats += f"> 📜 {'public repository' % public_repo} \n > \n"

    private_repo = GHM.USER.owned_private_repos if GHM.USER.owned_private_repos is not None else 0
    if public_repo != 1:
        stats += f"> 🔑 {'private repositories' % private_repo} \n > \n"
    else:
        stats += f"> 🔑 {'private repository' % private_repo} \n > \n"

    return stats


async def collect_user_repositories() -> Dict:
    repositories = await DM.get_remote_graphql("user_repository_list", username=GHM.USER.login, id=GHM.USER.node_id)
    repo_names = [repo["name"] for repo in repositories]
    DBM.g("\tUser repository list collected!")

    contributed = await DM.get_remote_graphql("repos_contributed_to", username=GHM.USER.login)

    contributed_nodes = [repo for repo in contributed if repo is not None and repo["name"] not in repo_names and not repo["isFork"]]
    DBM.g("\tUser contributed to repository list collected!")

    return repositories + contributed_nodes


async def get_stats() -> str:
    repositories = await collect_user_repositories()
    yearly_data, commit_data = await calculate_commit_data(repositories)
    stats = await get_waka_time_stats(repositories, commit_data)

    if EM.SHOW_SHORT_INFO:
        stats += await get_short_github_info()

    if EM.SHOW_LANGUAGE_PER_REPO:
        stats += f"{make_language_per_repo_list(repositories)}\n\n"

    if EM.SHOW_LOC_CHART:
        await create_loc_graph(yearly_data, GRAPH_PATH)
        stats += f"**Timeline'**\n\n{GHM.update_chart('Lines of Code', GRAPH_PATH)}"

    if EM.SHOW_TOTAL_CODE_TIME:
        data = await DM.get_remote_json("waka_all")
        data = str(data['data']['text'])
        stats += f"![I have been coding for](http://img.shields.io/badge/{quote('I have been coding for')}-{quote(data)}-blue) "

    if EM.SHOW_LINES_OF_CODE:
        total_loc = sum([yearly_data[y][q][d]["add"] for y in yearly_data.keys() for q in yearly_data[y].keys() for d in yearly_data[y][q].keys()])
        data = f"{intword(total_loc)} lines of code"
        stats += f"![Lines of code](https://img.shields.io/badge/'I have been writing-{quote(data)}-blue)\n\n"

    if EM.SHOW_PROFILE_VIEWS:
        data = GHM.REMOTE.get_views_traffic()
        stats += f"![Profile views](http://img.shields.io/badge/'Profile views-{data['count']}-blue) "

    return stats


async def main():
    init_github_manager()
    await init_download_manager(GHM.USER.login)

    stats = await get_stats()

    if not EM.DEBUG_RUN:
        GHM.update_readme(stats)
        GHM.commit_update()
    else:
        GHM.set_github_output(stats)
    await DM.close_remote_resources()


if __name__ == "__main__":
    init_debug_manager()
    start_time = datetime.now()
    DBM.g("Program execution started at $date.", date=start_time)
    run(main())
    end_time = datetime.now()
    DBM.g("Program execution finished at $date.", date=end_time)
    DBM.p("Program finished in $time.", time=end_time - start_time)
