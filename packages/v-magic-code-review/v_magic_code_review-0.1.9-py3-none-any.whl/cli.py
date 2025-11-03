import argparse
import logging
import os
import textwrap
from typing import Optional
from urllib.parse import urlparse, parse_qs

import bs4
import gitlab
import pyperclip
from atlassian import Confluence, Jira
from gemini_webapi import GeminiClient
from gemini_webapi.constants import Model
from markdownify import MarkdownConverter
from rich.console import Console
from rich.markdown import Markdown
from termcolor import colored
from yaspin import yaspin
from yaspin.spinners import Spinners

from config import GitlabConfig, JiraConfig, JiraField, ConfluenceConfig, GeminiConfig
from prompt import Prompts
from util import call_async_func, remove_blank_lines, first_element

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class GitlabService:
    def __init__(self):
        gl = gitlab.Gitlab(GitlabConfig.HOST, private_token=GitlabConfig.TOKEN)
        gl_project = gl.projects.get(GitlabConfig.PROJECT_ID)

        self.gl = gl
        self.gl_project = gl_project

    def get_mr(self, mr_id):
        return self.gl_project.mergerequests.get(mr_id)

    def find_mr_by_jira_key(self, jira_key):
        merge_requests = self.gl_project.mergerequests.list(state='opened', iterator=True)
        for mr in merge_requests:
            if jira_key in mr.title:
                return mr
        return None

    def get_plain_diff_from_mr(self, mr):
        latest_diff_version = max([it.id for it in mr.diffs.list(all=True)])
        latest_diff = mr.diffs.get(latest_diff_version)

        full_plain_diff = []

        for change in latest_diff.diffs:
            old_path = change.get('old_path')
            new_path = change.get('new_path')
            diff_content = change.get('diff')
            new_file = change.get('new_file')
            renamed_file = change.get('renamed_file')
            deleted_file = change.get('deleted_file')

            # Skip files based on an extension or path
            if (
                any(old_path.endswith(ext) for ext in GitlabConfig.DIFF_EXCLUDE_EXT)
                or any(old_path.startswith(path) for path in GitlabConfig.DIFF_EXCLUDE_PATH)
            ):
                continue
            # Skip files based on an extension or path
            if (
                any(new_path.endswith(ext) for ext in GitlabConfig.DIFF_EXCLUDE_EXT)
                or any(new_path.startswith(path) for path in GitlabConfig.DIFF_EXCLUDE_PATH)
            ):
                continue
            # Skip empty diffs
            if not diff_content:
                continue

            diff_git_line = f"diff --git a/{old_path} b/{new_path}"
            full_plain_diff.append(diff_git_line)

            # Handle file mode changes, new files, deleted files, and renamed files
            if new_file:
                full_plain_diff.append("new file mode 100644")  # Assuming typical file mode
                full_plain_diff.append("--- /dev/null")
                full_plain_diff.append(f"+++ b/{new_path}")
            elif deleted_file:
                full_plain_diff.append(f"--- a/{old_path}")
                full_plain_diff.append("+++ /dev/null")
            elif renamed_file:
                full_plain_diff.append(f"rename from {old_path}")
                full_plain_diff.append(f"rename to {new_path}")
                full_plain_diff.append(f"--- a/{old_path}")
                full_plain_diff.append(f"+++ b/{new_path}")
            else:
                full_plain_diff.append(f"--- a/{old_path}")
                full_plain_diff.append(f"+++ b/{new_path}")
            full_plain_diff.append(diff_content)
        return "\n".join(full_plain_diff)

    def add_comments(self, mr, body):
        mr.notes.create({'body': body})


class JiraService:
    def __init__(self):
        self.jira = Jira(
            url=JiraConfig.HOST,
            token=JiraConfig.TOKEN,
        )

    def get_client(self) -> Jira:
        return self.jira

    def get_issue(self, issue_key: str) -> dict:
        return self.jira.issue(issue_key)

    def get_issue_comments(self, issue: dict) -> str:
        original_comments = issue['fields'][JiraField.COMMENT]['comments']
        text_comments = []
        for comment in original_comments:
            author_section = '{} {}：\n'.format(comment['created'], comment['author']['displayName'])
            body_section = remove_blank_lines(comment['body'])
            text_comments.append(author_section + body_section)
            logging.info('get issue comment, author: %s, body: %s', author_section, body_section.splitlines()[-1])
        return '\n'.join(text_comments)

    def get_issue_requirements(self, issue: dict, confluence_service: 'ConfluenceService') -> str:
        description = issue['fields'][JiraField.DESCRIPTION]
        if not description:
            return ''

        if description.startswith('https://'):
            logging.info("get requirements from confluence: %s", description)

            wiki_url = description
            page = confluence_service.get_page_by_url(wiki_url)
            requirements = confluence_service.get_requirements(page, issue['key'])
        else:
            logging.info('get requirements from description: %s', description)
            requirements = description
        return requirements

    def get_issue_design(self, issue: dict, confluence_service: 'ConfluenceService') -> str:
        remote_links = self.jira.get_issue_remote_links(issue['key'])
        issue_designs = []
        for remote_link in remote_links:
            application = remote_link['application']
            if not application or application['type'] != 'com.atlassian.confluence':
                continue
            url = remote_link['object']['url']
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)
            page_id = first_element(params.get('pageId') or [])
            page = confluence_service.get_page_by_id(page_id)
            space = page['_expandable']['space']
            if space != '/rest/api/space/ORI':
                continue
            logging.info('get design from confluence, title: %s, url: %s', page['title'], url)
            issue_designs.append(confluence_service.get_page_markdown(page))
        return '\n\n'.join(issue_designs)


class ConfluenceService:
    def __init__(self):
        self.confluence = Confluence(
            url=ConfluenceConfig.HOST,
            token=ConfluenceConfig.TOKEN,
            cloud=False
        )

    def get_page_by_url(self, url):
        return self.get_page_by_id(url.split('/pages/')[1].split('/')[0])

    def get_page_by_id(self, page_id):
        return self.confluence.get_page_by_id(page_id=page_id, expand='body.storage')

    def get_page_markdown(self, page):
        soup = bs4.BeautifulSoup(page['body']['storage']['value'], "lxml")
        return MarkdownConverter().convert_soup(soup)

    def get_requirements(self, page, jira_key):
        bs_content = bs4.BeautifulSoup(page['body']['storage']['value'], "lxml")

        reference_row = self.get_reference_row(bs_content, jira_key)
        if reference_row is None:
            logging.warning('jira key not found in confluence page: %s', jira_key)
            return ''
        requirements = reference_row.get_text(separator='\n', strip=True)
        return requirements

    def get_reference_row(self, bs_content, jira_key):
        for table in bs_content.find_all('table'):
            for row in table.find_all('tr'):
                for cell in row.find_all(['td', 'th']):
                    if jira_key in cell.get_text(strip=True):
                        return row
        return None


class GeminiService:
    def __init__(self):
        self.gemini_client = GeminiClient(
            secure_1psid=GeminiConfig.cookie_secure_1psid,
            secure_1psidts=GeminiConfig.cookie_secure_1psidts,
        )
        call_async_func(self.gemini_client.init, timeout=600, auto_refresh=False)

    def do_code_quality_analysis(self, prompt: str) -> str:
        resp = call_async_func(
            self.gemini_client.generate_content,
            prompt=prompt,
            model=Model.G_2_5_PRO,
        )
        return resp.text


def code_review(
    jira_key: str,
    mr_id: Optional[int],
    only_code: Optional[bool],
    copy_prompt: Optional[bool],
    prompt_template_name: Optional[str],
) -> None:
    gitlab_service = GitlabService()
    if mr_id is not None:
        mr = gitlab_service.get_mr(mr_id)
    else:
        mr = gitlab_service.find_mr_by_jira_key(jira_key)
    assert mr is not None, f"merge request not found with jira key: {jira_key}"

    logging.info('merge request link: %s', mr.web_url)
    logging.info('merge request title: %s', mr.title)

    if only_code:
        issue_summary = '无'
        issue_requirements = '无'
        issue_design = '无'
        issue_comments = '无'
    else:
        logging.info('get jira ...')
        jira_service = JiraService()
        jira_issue = jira_service.get_issue(jira_key)
        assert jira_issue is not None, f"jira issue not found: {jira_key}"

        logging.info('jira issue link: %s', jira_issue['self'])
        logging.info('jira issue summary: %s', jira_issue['fields'][JiraField.SUMMARY])

        issue_summary = jira_issue['fields'][JiraField.SUMMARY]

        logging.info('get wikis ...')
        confluence_service = ConfluenceService()
        issue_requirements = jira_service.get_issue_requirements(jira_issue, confluence_service)
        logging.info('✨ issue requirements length: %s', len(issue_requirements))

        issue_design = jira_service.get_issue_design(jira_issue, confluence_service)
        logging.info('✨ issue design length: %s', len(issue_design))

        issue_comments = jira_service.get_issue_comments(jira_issue)
        logging.info('✨ issue comments length: %s', len(issue_comments))

    mr_diff = gitlab_service.get_plain_diff_from_mr(mr)
    logging.info('✨ code  diff length: %s', len(mr_diff))

    prompt = Prompts.create(
        template_name=prompt_template_name,
        issue_summary=issue_summary,
        issue_requirements=issue_requirements,
        issue_design=issue_design,
        issue_comments=issue_comments,
        mr_description=mr.description,
        mr_diff=mr_diff
    )
    # logging.info('✨ prompt length: %s, tokens num: %s', len(prompt), num_tokens_from_text(prompt))

    if copy_prompt:
        pyperclip.copy(prompt)
        print("✅ {}".format(colored('Prompt 已复制到剪贴板', 'green', attrs=['bold'])))
        return

    gemini_service = GeminiService()
    with yaspin(Spinners.clock, text="Waiting for Gemini's response, usually takes about 2 minutes", timer=True) as sp:
        analysis_result = gemini_service.do_code_quality_analysis(prompt)
        analysis_result = analysis_result.lstrip("```markdown")
        analysis_result = analysis_result.rstrip("```")
        analysis_result_with_section = f"""
<details>

<summary>AI Code Review 结果，请 Owner 对结果中的问题一一回复</summary>

{analysis_result}

</details>
        """
        analysis_result_with_section = textwrap.dedent(analysis_result_with_section).strip()

    Console().print(Markdown(analysis_result, code_theme='rrt'))

    print()

    selected = input(
        "✨ {}{}/{}， 或者{}/{}\n👉 ".format(
            colored('是否添加到 MR Comments？', 'yellow', attrs=['bold']),
            colored('添加(Y)', 'green', attrs=['bold']),
            colored('放弃(Q)', 'red', attrs=['bold']),
            colored('复制(C)', 'magenta', attrs=['bold']),
            colored('保存(S)', 'blue', attrs=['bold'])
        )
    )
    if selected.lower() == 'y':
        gitlab_service.add_comments(mr, analysis_result_with_section)
        print("✅ {}".format(colored('已添加到 MR', 'green', attrs=['bold'])))
    elif selected.lower() == 'c':
        pyperclip.copy(analysis_result_with_section)
        print("✅ 已复制到剪贴板")
    elif selected.lower() == 's':
        file_path = os.path.expanduser('~/Downloads/magic_code_review_{}.md'.format(jira_key))
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(analysis_result)
        print("✅ 已保存到 {}".format(file_path))
    else:
        print("👋 Bye!")


def print_version_text() -> None:
    print("{} {}".format(
        colored('v-cr', color='green', attrs=['bold']),
        colored('v0.1.9', color='red', attrs=['bold'])
    ))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Magic Code Review')
    parser.add_argument(
        'jira_key_or_mr_id',
        type=str,
        nargs='?',
        metavar="JIRA_KEY OR MR_ID",
        help='jira issue key or merge request id'
    )
    parser.add_argument('-m', '--mr-id', type=int, help='merge request id')
    parser.add_argument('-o', '--only-code', action='store_true', help='only review code diff')
    parser.add_argument('-c', '--copy-prompt', action='store_true', help='copy prompt to clipboard')
    parser.add_argument('--prompt-template', type=str, default='default', help='specific prompt template')
    parser.add_argument('--list-prompt-template', action='store_true', help='list all prompt templates')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--version', action='store_true')
    return parser.parse_args()


def main():
    args = parse_args()

    if args.version:
        print_version_text()
        return

    if args.list_prompt_template:
        names = ['* ' + it + '\n' for it in Prompts.list_template_names()]
        output = textwrap.dedent('''
            Avalible Prompt Templates:
                
            {}
        ''').strip().format(''.join(names))
        Console().print(Markdown(output))
        return

    logging.info('args: %s', args)

    assert args.prompt_template in Prompts.list_template_names(), f"prompt template not found: {args.prompt_template}"

    if args.jira_key_or_mr_id:
        jira_key_or_mr_id = args.jira_key_or_mr_id
        only_code = args.only_code
        mr_id = args.mr_id

        if mr_id is None and jira_key_or_mr_id.isnumeric():
            mr_id = jira_key_or_mr_id
            only_code = True

        code_review(jira_key_or_mr_id, mr_id, only_code, args.copy_prompt, args.prompt_template)


if __name__ == "__main__":
    main()
