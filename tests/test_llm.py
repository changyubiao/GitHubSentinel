import unittest
# from src.github_client import GitHubClient
from src.llm import LLM



class TestLLM(unittest.TestCase):
    def test_generate_daily_report(self):
        # Add test cases for LLM
        pass




if __name__ == '__main__':
    # unittest.main()
    pass


    # deepseek-v3-2-251201
    llm = LLM(factory_name='ark',model_name='deepseek-v3-2-251201')
    print(llm,id(llm.client))

    llm2 = LLM(factory_name='ark',model_name='deepseek-v3-2-251201')
    print(llm2,id(llm2.client))

    # glm-4-7-251222   https://ark.cn-beijing.volces.com/api/v3
    llm2 = LLM(factory_name='ark',model_name='glm-4-7-251222')
    print(llm2,id(llm2.client))
    # doubao-seed-2-0-pro-260215
    llm = LLM(factory_name='ark',model_name='doubao-seed-2-0-pro-260215')
    print(llm,id(llm.client))
    # qwen3-32b-20250429
    llm3 = LLM(factory_name='apiyi',model_name='gpt-3.5-turbo')
    print(llm3,id(llm3.client))

    llm4 = LLM(factory_name='apiyi',model_name='gpt-4')
    print(llm4,id(llm4.client))