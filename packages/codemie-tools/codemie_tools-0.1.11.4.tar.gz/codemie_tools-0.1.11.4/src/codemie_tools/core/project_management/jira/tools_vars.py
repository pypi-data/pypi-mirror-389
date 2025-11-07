from codemie_tools.base.models import ToolMetadata
from codemie_tools.core.project_management.jira.models import JiraConfig


def get_jira_tool_description(api_version: int = 2):
    if api_version == 2:
        description = (
            "JIRA Tool for Official Atlassian JIRA REST API V2 to call, searching, creating, updating issues, etc."
            "Required args: relative_url, method, params"
            "1. 'method': HTTP method (GET, POST, PUT, DELETE, etc.)"
            "2. 'relative_url': JIRA API URI starting with '/rest/api/2/...' (no query params in URL)"
            "3. 'params': Optional request body/query params as stringified JSON"
        )
    elif api_version == 3:
        description = (
            "JIRA Tool for Official Atlassian JIRA REST API V3 to call, searching, creating, updating issues, etc."
            "Required args: relative_url, method, params"
            "1. 'method': HTTP method (GET, POST, PUT, DELETE, etc.)"
            "2. 'relative_url': JIRA API URI starting with '/rest/api/3/...' (no query params in URL)"
            "3. 'params': Optional request body/query params as stringified JSON"
            "4. IMPORTANT: For issue search you should use /rest/api/3/search/jql, because /rest/api/3/search is deprecated endpoint"
        )
    else:
        raise ValueError(f"Wrong API version, required 2 or 3, given is: {api_version}")

    description += """
    Key behaviors:
    - Get minimum required fields for search/read operations unless user requests more
    - Query API for missing required info, ask user if not found
    - For status updates: get available statuses first, compare with user input
    - File attachments: To attach files to an issue, use POST method with '/rest/api/{version}/issue/{issueIdOrKey}/attachments'
      and include the file name in params as {"file": "filename.ext"} or {"files": ["file1.ext", "file2.ext"]} for multiple files
    """
    return description


GENERIC_JIRA_TOOL = ToolMetadata(
    name="generic_jira_tool",
    description=get_jira_tool_description(),
    label="Generic Jira",
    user_description="""
    Provides access to the Jira API, enabling interaction with Jira project management and issue tracking features. This tool allows the AI assistant to perform various operations related to issues, projects, and workflows in both Jira Server and Jira Cloud environments.

    Key capabilities:
    - Create, update, search, and manage Jira issues
    - Attach files and documents to issues
    - Manage projects, sprints, and workflows
    - Query issue status, assignees, and metadata

    Before using it, it is necessary to add a new integration for the tool by providing:
    1. Alias (A friendly name for the Jira integration)
    2. Jira URL
    3. Username/email for Jira (Required for Jira Cloud)
    4. Token (API token or Personal Access Token)

    Usage Note:
    Use this tool when you need to manage Jira issues, projects, sprints, retrieve information from your Jira environment, or attach files to issues.
    """.strip(),
    settings_config=True,
    config_class=JiraConfig
)
