from typing import List, Dict, Tuple,Optional, Tuple, Union, Any

from flotorch.sdk.utils.llm_utils import invoke, async_invoke, parse_llm_response, LLMResponse
from flotorch.sdk.utils.logging_utils import log_object_creation, log_error, log_llm_request, log_llm_response

class FlotorchLLM:
    def __init__(self, model_id: str, api_key: str, base_url: str):
        self.model_id = model_id
        self.api_key = api_key
        self.base_url = base_url
        
        # Log object creation
        log_object_creation("FlotorchLLM", model_id=model_id, base_url=base_url)
    
    def invoke(
        self,
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict]] = None, 
        response_format=None, 
        extra_body: Optional[Dict] = None, 
        **kwargs
    ) -> Union[LLMResponse, Tuple[LLMResponse, Any]]:
        try:
            # Log request details
            log_llm_request(self.model_id, messages, tools, **kwargs)
            
            # Extract return_headers before passing to invoke
            return_headers = kwargs.pop('return_headers', False)
            response = invoke(messages, self.model_id, self.api_key, self.base_url, tools=tools, response_format=response_format, extra_body=extra_body, return_headers=return_headers, **kwargs)
            if return_headers:
                response_body, response_headers = response
            else:
                response_body = response

            parsed_response = parse_llm_response(response_body)
            # Log response details
            tool_calls = response_body.get('choices', [{}])[0].get('message', {}).get('tool_calls', [])
            usage = response_body.get('usage', {})
            
            # Determine if this is likely a final response (no tool calls and has content)
            is_final_response = not tool_calls and parsed_response.content.strip()
            
            log_llm_response(self.model_id, parsed_response.content, tool_calls, usage, is_final_response)
            
            if return_headers:
                return parsed_response, response_headers
            else:
                return parsed_response
        except Exception as e:
            log_error("FlotorchLLM.invoke", e)
            raise

    async def ainvoke(
        self, 
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        response_format=None, 
        extra_body: Optional[Dict] = None,
        **kwargs
    ) -> Union[LLMResponse, Tuple[LLMResponse, Any]]:
        """
        Invoke LLM with individual parameters instead of a complete payload.
        Creates the payload internally from the provided parameters.
        """
        
        try:
            # Log request details
            log_llm_request(self.model_id, messages, tools, **kwargs)
            
            # Extract return_headers before passing to async_invoke
            return_headers = kwargs.pop('return_headers', False)
            
            # Use the utility function that handles payload creation
            response = await async_invoke(messages, self.model_id, self.api_key, self.base_url, tools=tools, response_format=response_format, extra_body=extra_body, return_headers=return_headers, **kwargs)
            if return_headers:
                response_body, response_headers = response
            else:
                response_body = response
            
            parsed_response = parse_llm_response(response_body)
            # Log response details
            tool_calls = response_body.get('choices', [{}])[0].get('message', {}).get('tool_calls', [])
            usage = response_body.get('usage', {})
            
            # Determine if this is likely a final response (no tool calls and has content)
            is_final_response = not tool_calls and parsed_response.content.strip()
            
            log_llm_response(self.model_id, parsed_response.content, tool_calls, usage, is_final_response)
            
            if return_headers:
                return parsed_response, response_headers
            else:
                return parsed_response
        except Exception as e:
            log_error("FlotorchLLM.ainvoke", e)
            raise