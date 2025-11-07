from openai import OpenAI
import json
import re
import os
from typing import Optional, Dict, Any

from kousuan.skills import SmartCalculatorEngine

default_system_prompt = """
你是一名小学数学老师，请为小学生提供的口算题目生成详细的分步解题过程.

## 要求
1. 选择最合适的速算方法进行解题。并且提供循序渐进的完整解题步骤说明。
2. 输出解题过程时，必须包含每一步的解说词，且解说词必须为中文。
3. 输出的JSON中，尽量包含每一步的公式（如有）。

## 输出格式要求
- 并输出结构化JSON，请严格输出JSON格式，不要输出多余内容。
- 方法名称name，保持简洁明了不添加修饰词，如果提供了参考计算技巧，请保持与参考计算技巧名称保持一致。
- 字段包括：question, name, description, result, steps, error。每个step包含description, operation, result, narration, formula（如有）。
- `formula`字段可选,公式是可以简洁表达计算技巧的形式化的表达方式，比如 (M-x)(M+x) = M² - x²`，如果该步骤有对应的数学公式，请填写公式，否则可不填。
- description字段是对该步骤的简要描述, 描述不超过30个字。
- narration字段是对该步骤的详细解说词。

=== 参考输出格式
{
  "question": "47x53",
  "name": "中间数乘法",
  "description": "对称分布数相乘，中数平方减差平方",
  "result": 2491,
  "steps": [
    {
      "description": "使用中间数乘法：47 × 53",
      "operation": "识别模式",
      "result": "寻找中间数进行对称分解,确定中间数为50，差值为3",
       "narration": "我们可以发现47和53是对称分布的数，它们的中间数是50",
    },
    {
      "description": "计算：50² - 3² = 2500 - 9 = 2491",
      "operation": "计算结果",
      "result": 2491,
      "narration": "我们可以通过计算中间数的平方减去差的平方来得到结果。",
      "formula": "(M-x)(M+x) = M² - x²"
    }
  ],
  "error": null
}
"""

class AICalculator:
    """AI计算器类，用于生成口算题目的解题建议"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, 
                 model: str = "gpt-5-mini", temperature: float = 0.8, max_tokens: int = 2048):
        """
        初始化AI计算器
        
        Args:
            api_key: OpenAI API密钥，默认从环境变量获取
            base_url: API基础URL，默认从环境变量获取
            model: 使用的模型名称
            temperature: 生成温度
            max_tokens: 最大生成token数
        """
        env = os.environ
        self.api_key = api_key or env.get("OPENAI_API_KEY", "")
        self.base_url = base_url or env.get("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # 初始化客户端
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        
        # 系统提示词
        self.system_prompt = default_system_prompt
    
    def generate(self, prompt: str, user_input: str = '', format: str = "json") -> Any:
        """
        生成AI响应
        
        Args:
            prompt: 系统提示词
            user_input: 用户输入
            format: 返回格式，支持 "json" 或 "text"
            
        Returns:
            生成的响应内容
        """
        try:
            messages = [
                {"role": "system", "content": prompt}
            ]
            if user_input:
                messages.append({"role": "user", "content": user_input})
                
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            content = response.choices[0].message.content
            if not content:
                return {"success": False, "error": "LLM未返回内容"}
                
            print("LLM原始输出:", content)
            
            if format == "json":
                content = content.replace('```json', '').replace('```', '')
                return json.loads(content.strip())
            return content.strip()
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_suggestion(self, question: str, calc_skills: Optional[str] = None) -> Dict[str, Any]:
        """
        生成计算建议
        
        Args:
            question: 口算题目
            calc_skills: 参考计算技巧（可选）
            
        Returns:
            包含解题建议的字典
        """
        user_input = f"""题目：{question}"""
        if calc_skills:
            user_input += f"\n## 参考计算技巧：\n\n{calc_skills}"
            
        result = self.generate(self.system_prompt, user_input=user_input, format="json")
        
        if isinstance(result, dict) and result.get("steps"):
            result['question'] = question
            result['success'] = True
            
        return result
    
    def generate_skills(self, question: str) -> Dict[str, Any]:
        """
        基于智能计算引擎生成计算技巧建议
        
        Args:
            question: 口算题目
            
        Returns:
            包含计算技巧和解题建议的字典
        """
        engine = SmartCalculatorEngine()
        result_data = engine.calculate_with_cross_validation(question) or {}
        # 提取所有匹配的计算方法
        cross_validation = result_data.get("cross_validation", {})
        methods = []
        if result_data.get('success') and cross_validation:
            calculators = cross_validation.get('calculators', [])
            methods = [
                calc.get('name', '') + '\n> ' + calc.get('description', '') 
                for calc in calculators if calc.get('success', False)
            ]
            calc_skills = '- ' + '\n- '.join(methods)
        else:
            calc_skills = None
        # 生成AI建议
        result = self.generate_suggestion(question, calc_skills=calc_skills)
        
        # 添加引擎计算结果
        if isinstance(result, dict):
            result['engine_methods'] = methods
            
        return result
    
    def update_config(self, **kwargs):
        """
        更新配置参数
        
        Args:
            **kwargs: 配置参数
        """
        if 'api_key' in kwargs:
            self.api_key = kwargs['api_key']
        if 'base_url' in kwargs:
            self.base_url = kwargs['base_url']
        if 'model' in kwargs:
            self.model = kwargs['model']
        if 'temperature' in kwargs:
            self.temperature = kwargs['temperature']
        if 'max_tokens' in kwargs:
            self.max_tokens = kwargs['max_tokens']
        
        # 重新初始化客户端
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)


# 保持向后兼容的函数接口
def generate_calculator_suggestion(question, calc_skills=None) -> dict:
    """
    生成计算建议（向后兼容函数）
    """
    calculator = AICalculator()
    return calculator.generate_suggestion(question, calc_skills)


def generate_calculator_skills(question):
    """
    生成计算技巧（向后兼容函数）
    """
    calculator = AICalculator()
    return calculator.generate_skills(question)