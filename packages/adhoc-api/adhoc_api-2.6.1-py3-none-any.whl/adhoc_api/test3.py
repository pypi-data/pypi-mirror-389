# put this file in adhoc-api/adhoc_api/

from adhoc_api.loader import load_yaml_api
from adhoc_api.uaii import gemini_15_flash, gemini_25_pro
from adhoc_api.tool import AdhocApi
from pathlib import Path

here = Path(__file__).parent

def test():
    drafter_configs = [gemini_25_pro]

    gdc_api = load_yaml_api(here / '../examples/gdc/api.yaml')
    adhoc = AdhocApi(apis=[gdc_api], drafter_config=drafter_configs, curator_config=None)
    res = adhoc.use_api('Genomics Data Commons', 'how do I list all the cases in GDC filtering for individuals over 50')
    print(res)


if __name__ == "__main__":
    test()