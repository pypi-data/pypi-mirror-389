#
import asyncio
from pro_craft import AsyncIntel
from digital_life.models import PersonInfo, CharactersData, ContentVer, BriefResponse
from digital_life.utils import memoryCards2str, extract_article
from digital_life import inference_save_case
import pandas as pd


###

class DigitalAvatar:
    def __init__(self,inference_save_case = False,model_name = "doubao-1-5-pro-256k-250115"):
        self.inters = AsyncIntel(model_name = model_name)
        self.inference_save_case = inference_save_case


    async def desensitization(self, memory_cards: list[str]) -> list[str]:
        """
        数字分身脱敏 0100
        0100
        """
        tasks = []
        for memory_card in memory_cards:
            tasks.append(self.inters.intellect_format(
                                input_data=memory_card.get("content"),
                                prompt_id="avatar-desensitization",
                                version = None,
                                inference_save_case=self.inference_save_case,
                                OutputFormat = ContentVer,
                                 ))

        results = await asyncio.gather(*tasks, return_exceptions=False)

        for i, memory_card in enumerate(memory_cards):
            memory_card["content"] = results[i].get("content")
        return memory_cards
    
    async def personality_extraction(self, memory_cards: list[dict],action:str,old_character:str) -> str:
        """
        数字分身性格提取 0099
        """
        memoryCards_str, _ = memoryCards2str(memory_cards)

        output_format = """"""
        result = await self.inters.intellect(
                                    input_data="\n操作方案:\n" + action + "\n旧人物性格:\n" + old_character +"\n记忆卡片:\n" +  memoryCards_str,
                                    output_format=output_format,
                                    prompt_id ="avatar-personality-extraction",
                                    version = None,
                                    inference_save_case = self.inference_save_case,
                                    )
        
        
        result_content = extract_article(result)
        return result_content

    async def abrief(self, memory_cards: list[dict]) -> dict:
        """
        数字分身介绍 0098
        """
        
        memoryCards_str, _ = memoryCards2str(memory_cards)
        result = await self.inters.intellect_format(
                                input_data="聊天历史:\n" + memoryCards_str,
                                prompt_id="avatar-brief",
                                version = None,
                                inference_save_case=self.inference_save_case,
                                OutputFormat = BriefResponse,
                                 )
        return result

    async def auser_relationship_extraction(self,text: str) -> dict:
        """
        用户关系提取 0097
        # TODO
        """
        result = await self.inters.intellect_format(
                        input_data="聊天历史" + text,
                        prompt_id="user-relationship-extraction",
                        version = None,
                        inference_save_case=self.inference_save_case,
                        OutputFormat = CharactersData,
                        ExtraFormats=[PersonInfo]
                            )
        return result

    async def auser_overview(self,action: str,old_overview: str, memory_cards: list[dict],
                             version = None,
                             ) -> str:
        """
        用户概述 0096
        """
        memoryCards_str, _ = memoryCards2str(memory_cards)
        result = await self.inters.intellect_format(
                input_data="\n操作方案:\n" + action + "\n旧概述文本:\n" + old_overview +"\n记忆卡片:\n" +  memoryCards_str,
                prompt_id="user-overview",
                version = None,
                inference_save_case=self.inference_save_case,
                OutputFormat = ContentVer,
                    )
        return result.get("content")




