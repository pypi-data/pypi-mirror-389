from archytas.react import ReActAgent, FailedTaskError
from archytas.tools import PythonTool
from easyrepl import REPL
from adhoc_api.tool import AdhocApi, APISpec
from adhoc_api.uaii import claude_37_sonnet

from bs4 import BeautifulSoup
import requests
from markdownify import markdownify


def main():    
    # set up the API spec for the JokeAPI
    gdc_api: APISpec = {
        'name': "JokesAPI",
        'description': 'JokeAPI is a REST API that serves uniformly and well formatted jokes.',
        'documentation': get_joke_api_documentation(),
    }

    # set up the tools and agent
    adhoc_api = AdhocApi(apis=[gdc_api], drafter_config=claude_37_sonnet)
    python = PythonTool()
    agent = ReActAgent(model='gpt-4o', tools=[adhoc_api, python], verbose=True)

    # REPL to interact with agent
    for query in REPL(history_file='.chat'):
        try:
            answer = agent.react(query)
            print(answer)
        except FailedTaskError as e:
            print(f"Error: {e}")


def get_joke_api_documentation() -> str:
    """Download the HTML of the joke API documentation page with soup and convert it to markdown."""
    url = 'https://sv443.net/jokeapi/v2/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    markdown = markdownify(str(soup))
    
    return markdown


if __name__ == "__main__":
    main()