from .uaii import (
    ClaudeAgent,
    ClaudeModel,
    OpenAIAgent,
    OpenAIModel,
    GeminiAgent,
    GeminiModel,
    UAII,
    LLMConfig,
    claude_37_sonnet,
    gpt_4o,
    gpt_41,
    gpt_5,
    gpt_5_mini,
    gpt_5_nano,
    gemini_15_pro,
    gemini_15_flash,
    gemini_25_pro,
    gemini_25_flash,
    gemini_25_flash_lite,
    OpenRouterAgent,
    TokiModelName as OpenRouterModel,
)
from .tool import AdhocApi, APISpec
from .loader import load_yaml_api, load_yaml_examples
from pathlib import Path
from easyrepl import REPL

import pdb

here = Path(__file__).parent

test_api: APISpec = {
    'name': 'test',
    'description': 'test',
    'documentation': '',
}

def instantiate_apis():
    drafter_config: LLMConfig = {'provider': 'anthropic', 'model': 'claude-3-7-sonnet-latest'}
    drafter_config: LLMConfig = {'provider': 'openai', 'model': 'o3-mini'}
    drafter_config: LLMConfig = {'provider': 'openai', 'model': 'o1-mini'}
    drafter_config: LLMConfig = {'provider': 'openai', 'model': 'o1'}

    api = AdhocApi(apis=[test_api], drafter_config=drafter_config)


def test_claude(model:ClaudeModel='clause-3-7-sonnet-latest'):
    agent = ClaudeAgent(model=model, system_prompt='You are a helpful assistant.')
    repl_loop(agent)


def test_openai(model:OpenAIModel='gpt-4o'):
    agent = OpenAIAgent(model=model, system_prompt=None)
    repl_loop(agent)

def test_gemini(model:GeminiModel='gemini-2.5-pro'):
    agent = GeminiAgent(model=model, system_prompt='you are a helpful assistant', cache_key=None, cache_content='', ttl_seconds=0)
    repl_loop(agent)


def test_openrouter(model:OpenRouterModel='openai/gpt-4o'):
    agent = OpenRouterAgent(model=model, system_prompt='you are a helpful assistant')
    repl_loop(agent)


def repl_loop(agent:UAII):
    for query in REPL(history_file='.chat'):
        res = agent.message(query, stream=True)
        for i in res:
            print(i, end='', flush=True)
        print()

        # res = agent.message(query, stream=False)
        # print(res)



def test_api_with_examples():
    examples = load_yaml_examples(here / '../examples/gdc/examples.yaml')
    gdc_api = load_yaml_api(here / '../examples/gdc/api.yaml')
    # pdb.set_trace()
# 
    drafter_config: LLMConfig = {'provider': 'google', 'model': 'gemini-1.5-flash-001'}
    api = AdhocApi(apis=[gdc_api], drafter_config=drafter_config)
    ...

def test_yaml_loading():
    from .loader import load_interpolated_yaml
    # examples_path = here / '../examples/gdc/examples.yaml'
    # gdc_api = here / '../examples/gdc/api.yaml'
    test_path = here / '../examples/gdc/test.yaml'
    # test_path = here / '../examples/gdc/infinite.yaml'
    apple = load_interpolated_yaml(test_path)
    # print(y)
    pdb.set_trace()
    ...


def test_example_curation():
    drafter_config: LLMConfig = {'provider': 'google', 'model': 'gemini-1.5-flash-001'}
    api = load_yaml_api(here / '../examples/gdc/api.yaml')
    adhoc = AdhocApi(apis=[api], drafter_config=drafter_config)
    for query in REPL(history_file='.chat'):
        res = adhoc.use_api('Genomics Data Commons', query)
        print(res)
        print()
    

def test_example_curation_2():
    api = load_yaml_api(here / '../examples/cbioportal/api.yaml')
    adhoc = AdhocApi(apis=[api], drafter_config=claude_37_sonnet)
    for query in REPL(history_file='.chat'):
        res = adhoc.use_api('cbioportal', query)
        print(res)
        print()
    

def test_biome_apis():
    drafter_configs = [{'provider': 'openrouter', 'model': 'google/gemini-2.5-flash'}] #[gemini_25_flash]# [claude_37_sonnet, gemini_15_flash]
    api_root = here / '../../biome/src/biome/api_definitions'
    api_names = ['cbioportal', 'cda', 'gdc', 'hpa', 'idc', 'indra', 'pdc']
    apis = [load_yaml_api(api_root / name / 'api.yaml') for name in api_names]
    adhoc = AdhocApi(apis=apis, drafter_config=drafter_configs)


    # res = adhoc.use_api('genomics_data_commons', 'how do I list all the cases in GDC filtering for individuals over 50')
    res = adhoc.use_api('cbioportal', 'fetch RNA-seq z-scores for STAT5A and STAT5B across the aml target gdc and aml ohsu 2022 studies')

    print(res)

    pdb.set_trace()
    # for query in REPL(history_file='.chat'):
        # res = adhoc.use_api('Biome', query)
        # print(res)
        # print()

    """
    Some Test Cases:
        adhoc.use_api('cbioportal', 'fetch RNA-seq z-scores for STAT5A and STAT5B across the aml target gdc and aml ohsu 2022 studies')
        adhoc.use_api('cbioportal', 'now do 2020')
        adhoc.use_api('Cancer Data Aggregator', 'give me an example of fetching data from CDA')
        adhoc.use_api('Human Protein Atlas', 'search for for RNA and protein expression summary of a gene (JAK2) using its Ensembl ID')
        adhoc.use_api('Human Protein Atlas', 'search for for RNA and protein expression summary of the gene JAK1')
        adhoc.use_api('Human Protein Atlas', 'give me a general example of using the API')
        adhoc.use_api('Genomics Data Commons', 'give me a general example of using the GDC API')
        adhoc.use_api('Genomics Data Commons', 'how do I list all the cases in GDC')
        adhoc.use_api('Genomics Data Commons', 'how do I list all the cases in GDC filtering for individuals over 50')
        adhoc.use_api('Imaging Data Commons', 'what columns are available in the IDC index')
        adhoc.use_api('Imaging Data Commons', 'find slide data for myeloid leukemia specimins')
        adhoc.use_api('Imaging Data Commons', 'find slide data for myeloid leukemia specimins with the jak2 mutation')
        adhoc.use_api('INDRA Context Graph Extension (CoGEx)', 'find and summarize evidence for AML using MeSH term (and child term) queries')
        adhoc.use_api('INDRA Context Graph Extension (CoGEx)', 'do exactly this: find and summarize evidence for AML using MeSH term (and child term) queries')
        adhoc.use_api('INDRA Context Graph Extension (CoGEx)', 'give me an example of making a query in INDRA about the jak1 mutation')
        adhoc.use_api('proteomics_data_commons', 'Fetch raw mass spec data for a specific study using study name, data category, and file type in the Proteomics Data Commons (PDC)')
        adhoc.use_api('proteomics_data_commons', 'Fetch raw mass spec data relating to bone marrow with leukemia')
    """

def test_errors():
    from .loader import load_interpolated_yaml
    api = load_interpolated_yaml(here / '../examples/errors/test.yaml')
    api2 = load_interpolated_yaml(here / '../examples/errors/test.yaml')
    # drafter_config: LLMConfig = {'provider': 'google', 'model': 'gemini-1.5-flash-001'}
    print(api, api2)



if __name__ == '__main__':
    # test_claude('claude-opus-4-0')
    # test_openai('gpt-5')
    # test_gemini('gemini-2.5-flash-lite')
    # test_openrouter('google/gemini-2.5-flash-lite')
    # instantiate_apis()
    # test_api_with_examples()
    # test_yaml_loading()
    # test_example_curation()
    test_biome_apis()
    # test_errors()