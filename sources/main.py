"""
Readme Development Metrics With waka time progress
"""
from asyncio import run
from datetime import datetime
from typing import Dict
from urllib.parse import quote

from humanize import intword
from manager_download import init_download_manager, DownloadManager as DM
from manager_environment import EnvironmentManager as EM
from manager_github import init_github_manager, GitHubManager as GHM
from manager_debug import init_debug_manager, DebugManager as DBM
from yearly_commit_calculator import calculate_commit_data
from graphics_list_formatter import make_list, make_commit_day_time_list


async def get_waka_time_stats(repositories: Dict, commit_dates: Dict) -> str:
    stats = str()
    data = await DM.get_remote_json("waka_stats")

    commit_list = await make_commit_day_time_list(data['data']['timezone'], repositories, commit_dates)
    stats += f"{commit_list}\n\n"

    stats += "📊 **I have spent time on** \n\n```text\n"

    lang_list = make_list(data["data"]["languages"])
    stats += f"📚 Languages: \n{lang_list}\n\n"

    edit_list = make_list(data["data"]["editors"])
    stats += f"📑 Editors: \n{edit_list}\n\n"

    os_list = make_list(data["data"]["operating_systems"])
    stats += f"💻 Operating Systems: \n{os_list}\n\n"

    return f"{stats[:-1]}```\n\n"


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

    # stats += f"{make_language_per_repo_list(repositories)}\n\n"

    stats += "<div align='center'><samp></br>~~~</br></br></samp>"

    total_time = await DM.get_remote_json("waka_all")
    hours = int(total_time['data']['text'].split(" ")[0])
    minutes = int(total_time['data']['text'].split(" ")[2])
    data = f"{hours + 1 if minutes > 30 else hours} coding hours"

    stats += f"<img src='http://img.shields.io/badge/{quote(data)}-black?style=for-the-badge' /> "

    total_loc = sum([yearly_data[y][q][d]["add"] for y in yearly_data.keys() for q in yearly_data[y].keys() for d in yearly_data[y][q].keys()])
    data = f"{intword(total_loc)} lines of code"
    stats += f"<img src='https://img.shields.io/badge/{quote(data)}-black?style=for-the-badge' />"

    stats += "</div>\n\n"

    # data = GHM.REMOTE.get_views_traffic()
    # stats += f"![Profile views](http://img.shields.io/badge/'Profile views-{data['count']}-blue)\n\n"

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
