"""AgentBill SDK Client"""
import time
import httpx
from typing import Any, Optional, Dict
from .tracer import AgentBillTracer
from .types import AgentBillConfig


class AgentBill:
    """
    AgentBill SDK for Python
    
    Example:
        >>> from agentbill import AgentBill
        >>> import openai
        >>> 
        >>> # Initialize AgentBill
        >>> agentbill = AgentBill.init({
        ...     "api_key": "your-api-key",
        ...     "customer_id": "customer-123",
        ...     "debug": True
        ... })
        >>> 
        >>> # Wrap your OpenAI client
        >>> client = agentbill.wrap_openai(openai.OpenAI(api_key="sk-..."))
        >>> 
        >>> # Use normally - all calls are tracked!
        >>> response = client.chat.completions.create(
        ...     model="gpt-4",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
    """
    
    def __init__(self, config: AgentBillConfig):
        self.config = config
        self.tracer = AgentBillTracer(config)
    
    @classmethod
    def init(cls, config: AgentBillConfig) -> "AgentBill":
        """Initialize AgentBill SDK"""
        return cls(config)
    
    def _estimate_tokens(self, text: str) -> int:
        """Simple token estimation: ~4 chars per token"""
        return max(1, len(str(text)) // 4)
    
    def _estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on model pricing (simplified)"""
        pricing = {
            # OpenAI
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            # Anthropic
            "claude-sonnet-4-5": {"input": 0.003, "output": 0.015},
            "claude-opus-4-1-20250805": {"input": 0.015, "output": 0.075},
            "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
            # Mistral
            "mistral-large-latest": {"input": 0.004, "output": 0.012},
            # Gemini
            "gemini-pro": {"input": 0.00025, "output": 0.0005},
        }
        
        model_price = pricing.get(model, {"input": 0.001, "output": 0.002})
        return (input_tokens / 1000 * model_price["input"]) + (output_tokens / 1000 * model_price["output"])
    
    def _validate_request(self, model: str, messages: Any, estimated_output_tokens: int = 1000) -> Dict:
        """Call ai-cost-guard-router edge function (tier-based routing)"""
        if not self.config.get("daily_budget") and not self.config.get("monthly_budget"):
            return {"allowed": True}  # Skip validation if no budgets set
        
        url = f"{self.config.get('base_url', 'https://bgwyprqxtdreuutzpbgw.supabase.co')}/functions/v1/ai-cost-guard-router"
        
        payload = {
            "api_key": self.config["api_key"],
            "customer_id": self.config.get("customer_id"),
            "model": model,
            "messages": messages,
        }
        
        try:
            with httpx.Client(timeout=10) as client:
                response = client.post(url, json=payload)
                result = response.json()
                
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] Router response: {result}")
                    if result.get("tier"):
                        print(f"[AgentBill] Tier: {result['tier']}, Mode: {result.get('mode', 'unknown')}")
                
                return result
        except Exception as e:
            if self.config.get("debug"):
                print(f"[AgentBill Cost Guard] Router failed: {e}")
            return {"allowed": True}  # Fail open to avoid blocking on network errors
    
    def _track_usage(self, model: str, provider: str, input_tokens: int, output_tokens: int, latency_ms: float, cost: float, event_name: str = "ai_request"):
        """Call track-ai-usage edge function"""
        url = f"{self.config.get('base_url', 'https://bgwyprqxtdreuutzpbgw.supabase.co')}/functions/v1/track-ai-usage"
        
        payload = {
            "api_key": self.config["api_key"],
            "customer_id": self.config.get("customer_id"),
            "agent_id": self.config.get("agent_id"),
            "event_name": event_name,
            "model": model,
            "provider": provider,
            "prompt_tokens": input_tokens,
            "completion_tokens": output_tokens,
            "latency_ms": latency_ms,
            "cost": cost,
        }
        
        try:
            with httpx.Client(timeout=10) as client:
                client.post(url, json=payload)
                
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] Usage tracked: ${cost:.4f}")
        except Exception as e:
            if self.config.get("debug"):
                print(f"[AgentBill Cost Guard] Tracking failed: {e}")
    
    def wrap_openai(self, client: Any) -> Any:
        """Wrap OpenAI client with Cost Guard protection"""
        
        # Track chat completions
        original_chat_create = client.chat.completions.create
        def tracked_chat_create(*args, **kwargs):
            model = kwargs.get("model", "unknown")
            messages = kwargs.get("messages", [])
            max_tokens = kwargs.get("max_tokens", kwargs.get("max_completion_tokens", 1000))
            
            # Extract event_name from agentbill_options if provided (don't pass to OpenAI)
            agentbill_options = kwargs.pop("agentbill_options", {})
            event_name = agentbill_options.get("event_name", "ai_request")
            
            # Phase 1: Validate budget BEFORE API call
            validation = self._validate_request(model, messages, max_tokens)
            if not validation.get("allowed"):
                error_msg = validation.get("reason", "Budget limit reached")
                error = Exception(error_msg)
                error.code = "BUDGET_EXCEEDED"
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ❌ Request blocked: {error_msg}")
                raise error
            
            # Phase 2: Execute AI call
            if self.config.get("debug"):
                print(f"[AgentBill] Intercepting OpenAI chat.completions.create with model: {model}")
            
            start_time = time.time()
            span = self.tracer.start_span("openai.chat.completions.create", {
                "model": model,
                "provider": "openai"
            })
            
            try:
                response = original_chat_create(*args, **kwargs)
                latency = (time.time() - start_time) * 1000
                
                # Phase 3: Track actual usage
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                cost = self._estimate_cost(model, input_tokens, output_tokens)
                
                self._track_usage(model, "openai", input_tokens, output_tokens, latency, cost, event_name)
                
                span.set_attributes({
                    "response.prompt_tokens": input_tokens,
                    "response.completion_tokens": output_tokens,
                    "response.total_tokens": response.usage.total_tokens,
                    "latency_ms": latency
                })
                span.set_status(0)
                
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ✓ Protected call completed: ${cost:.4f}")
                
                return response
            except Exception as e:
                span.set_status(1, str(e))
                raise
            finally:
                span.end()
        
        client.chat.completions.create = tracked_chat_create
        
        # Track embeddings
        original_embeddings_create = client.embeddings.create
        def tracked_embeddings_create(*args, **kwargs):
            if self.config.get("debug"):
                print(f"[AgentBill] Intercepting OpenAI embeddings.create with model: {kwargs.get('model', 'unknown')}")
            
            start_time = time.time()
            span = self.tracer.start_span("openai.embeddings.create", {
                "model": kwargs.get("model", "unknown"),
                "provider": "openai"
            })
            
            try:
                response = original_embeddings_create(*args, **kwargs)
                latency = (time.time() - start_time) * 1000
                span.set_attributes({
                    "response.prompt_tokens": response.usage.prompt_tokens,
                    "response.total_tokens": response.usage.total_tokens,
                    "latency_ms": latency
                })
                span.set_status(0)
                return response
            except Exception as e:
                span.set_status(1, str(e))
                raise
            finally:
                span.end()
        
        client.embeddings.create = tracked_embeddings_create
        
        # Track image generation
        original_images_generate = client.images.generate
        def tracked_images_generate(*args, **kwargs):
            if self.config.get("debug"):
                print(f"[AgentBill] Intercepting OpenAI images.generate")
            
            start_time = time.time()
            span = self.tracer.start_span("openai.images.generate", {
                "model": kwargs.get("model", "dall-e-3"),
                "provider": "openai",
                "size": kwargs.get("size", "1024x1024"),
                "quality": kwargs.get("quality", "standard")
            })
            
            try:
                response = original_images_generate(*args, **kwargs)
                latency = (time.time() - start_time) * 1000
                span.set_attributes({"latency_ms": latency})
                span.set_status(0)
                return response
            except Exception as e:
                span.set_status(1, str(e))
                raise
            finally:
                span.end()
        
        client.images.generate = tracked_images_generate
        
        # Track audio transcription (Whisper)
        original_audio_transcriptions_create = client.audio.transcriptions.create
        def tracked_audio_transcriptions_create(*args, **kwargs):
            if self.config.get("debug"):
                print(f"[AgentBill] Intercepting OpenAI audio.transcriptions.create")
            
            start_time = time.time()
            span = self.tracer.start_span("openai.audio.transcriptions.create", {
                "model": kwargs.get("model", "whisper-1"),
                "provider": "openai"
            })
            
            try:
                response = original_audio_transcriptions_create(*args, **kwargs)
                latency = (time.time() - start_time) * 1000
                span.set_attributes({"latency_ms": latency})
                span.set_status(0)
                return response
            except Exception as e:
                span.set_status(1, str(e))
                raise
            finally:
                span.end()
        
        client.audio.transcriptions.create = tracked_audio_transcriptions_create
        
        # Track text-to-speech
        original_audio_speech_create = client.audio.speech.create
        def tracked_audio_speech_create(*args, **kwargs):
            if self.config.get("debug"):
                print(f"[AgentBill] Intercepting OpenAI audio.speech.create")
            
            start_time = time.time()
            span = self.tracer.start_span("openai.audio.speech.create", {
                "model": kwargs.get("model", "tts-1"),
                "provider": "openai",
                "voice": kwargs.get("voice", "alloy")
            })
            
            try:
                response = original_audio_speech_create(*args, **kwargs)
                latency = (time.time() - start_time) * 1000
                span.set_attributes({"latency_ms": latency})
                span.set_status(0)
                return response
            except Exception as e:
                span.set_status(1, str(e))
                raise
            finally:
                span.end()
        
        client.audio.speech.create = tracked_audio_speech_create
        
        # Track moderations
        original_moderations_create = client.moderations.create
        def tracked_moderations_create(*args, **kwargs):
            if self.config.get("debug"):
                print(f"[AgentBill] Intercepting OpenAI moderations.create")
            
            start_time = time.time()
            span = self.tracer.start_span("openai.moderations.create", {
                "model": kwargs.get("model", "text-moderation-latest"),
                "provider": "openai"
            })
            
            try:
                response = original_moderations_create(*args, **kwargs)
                latency = (time.time() - start_time) * 1000
                span.set_attributes({"latency_ms": latency})
                span.set_status(0)
                return response
            except Exception as e:
                span.set_status(1, str(e))
                raise
            finally:
                span.end()
        
        client.moderations.create = tracked_moderations_create
        
        return client
    
    def wrap_anthropic(self, client: Any) -> Any:
        """Wrap Anthropic client with Cost Guard protection"""
        original_create = client.messages.create
        
        def tracked_create(*args, **kwargs):
            model = kwargs.get("model", "unknown")
            messages = kwargs.get("messages", [])
            max_tokens = kwargs.get("max_tokens", 1000)
            
            # Extract event_name from agentbill_options if provided (don't pass to Anthropic)
            agentbill_options = kwargs.pop("agentbill_options", {})
            event_name = agentbill_options.get("event_name", "ai_request")
            
            # Phase 1: Validate budget BEFORE API call
            validation = self._validate_request(model, messages, max_tokens)
            if not validation.get("allowed"):
                error_msg = validation.get("reason", "Budget limit reached")
                error = Exception(error_msg)
                error.code = "BUDGET_EXCEEDED"
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ❌ Request blocked: {error_msg}")
                raise error
            
            # Phase 2: Execute AI call
            start_time = time.time()
            span = self.tracer.start_span("anthropic.message", {
                "model": model,
                "provider": "anthropic"
            })
            
            try:
                response = original_create(*args, **kwargs)
                latency = (time.time() - start_time) * 1000
                
                # Phase 3: Track actual usage
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                cost = self._estimate_cost(model, input_tokens, output_tokens)
                
                self._track_usage(model, "anthropic", input_tokens, output_tokens, latency, cost, event_name)
                
                span.set_attributes({
                    "response.input_tokens": input_tokens,
                    "response.output_tokens": output_tokens,
                    "latency_ms": latency
                })
                span.set_status(0)
                
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ✓ Protected call completed: ${cost:.4f}")
                
                return response
            except Exception as e:
                span.set_status(1, str(e))
                raise
            finally:
                span.end()
        
        client.messages.create = tracked_create
        return client
    
    def wrap_bedrock(self, client: Any) -> Any:
        """Wrap AWS Bedrock client with Cost Guard protection"""
        original_invoke_model = client.invoke_model
        
        def tracked_invoke_model(*args, **kwargs):
            model = kwargs.get("modelId", "unknown")
            body_str = kwargs.get("body", "{}")
            
            # Parse body for messages
            import json
            try:
                body = json.loads(body_str)
                messages = body.get("messages", body.get("prompt", ""))
                max_tokens = body.get("max_tokens", body.get("max_tokens_to_sample", 1000))
            except:
                messages = ""
                max_tokens = 1000
            
            # Phase 1: Validate budget BEFORE API call
            validation = self._validate_request(model, messages, max_tokens)
            if not validation.get("allowed"):
                error_msg = validation.get("reason", "Budget limit reached")
                error = Exception(error_msg)
                error.code = "BUDGET_EXCEEDED"
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ❌ Request blocked: {error_msg}")
                raise error
            
            # Phase 2: Execute AI call
            if self.config.get("debug"):
                print(f"[AgentBill] Intercepting Bedrock invoke_model with model: {model}")
            
            start_time = time.time()
            span = self.tracer.start_span("bedrock.invoke_model", {
                "model": model,
                "provider": "bedrock"
            })
            
            try:
                response = original_invoke_model(*args, **kwargs)
                latency = (time.time() - start_time) * 1000
                
                # Parse response body for token usage
                body = json.loads(response['body'].read())
                
                # Handle different Bedrock model response formats
                input_tokens = 0
                output_tokens = 0
                if 'usage' in body:  # Claude models
                    input_tokens = body['usage'].get('input_tokens', 0)
                    output_tokens = body['usage'].get('output_tokens', 0)
                elif 'inputTextTokenCount' in body:  # Titan models
                    input_tokens = body.get('inputTextTokenCount', 0)
                    output_tokens = body['results'][0].get('tokenCount', 0) if 'results' in body else 0
                
                # Phase 3: Track actual usage
                cost = self._estimate_cost(model, input_tokens, output_tokens)
                self._track_usage(model, "bedrock", input_tokens, output_tokens, latency, cost)
                
                span.set_attributes({
                    "response.input_tokens": input_tokens,
                    "response.output_tokens": output_tokens,
                    "latency_ms": latency
                })
                span.set_status(0)
                
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ✓ Protected call completed: ${cost:.4f}")
                
                return response
            except Exception as e:
                span.set_status(1, str(e))
                raise
            finally:
                span.end()
        
        client.invoke_model = tracked_invoke_model
        return client
    
    def wrap_azure_openai(self, client: Any) -> Any:
        """Wrap Azure OpenAI client with Cost Guard protection"""
        original_create = client.chat.completions.create
        
        def tracked_create(*args, **kwargs):
            model = kwargs.get("model", "unknown")
            messages = kwargs.get("messages", [])
            max_tokens = kwargs.get("max_tokens", 1000)
            
            # Phase 1: Validate budget BEFORE API call
            validation = self._validate_request(model, messages, max_tokens)
            if not validation.get("allowed"):
                error_msg = validation.get("reason", "Budget limit reached")
                error = Exception(error_msg)
                error.code = "BUDGET_EXCEEDED"
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ❌ Request blocked: {error_msg}")
                raise error
            
            # Phase 2: Execute AI call
            if self.config.get("debug"):
                print(f"[AgentBill] Intercepting Azure OpenAI chat.completions.create")
            
            start_time = time.time()
            span = self.tracer.start_span("azure_openai.chat.completions", {
                "model": model,
                "provider": "azure_openai"
            })
            
            try:
                response = original_create(*args, **kwargs)
                latency = (time.time() - start_time) * 1000
                
                # Phase 3: Track actual usage
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                cost = self._estimate_cost(model, input_tokens, output_tokens)
                
                self._track_usage(model, "azure_openai", input_tokens, output_tokens, latency, cost)
                
                span.set_attributes({
                    "response.prompt_tokens": input_tokens,
                    "response.completion_tokens": output_tokens,
                    "response.total_tokens": response.usage.total_tokens,
                    "latency_ms": latency
                })
                span.set_status(0)
                
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ✓ Protected call completed: ${cost:.4f}")
                
                return response
            except Exception as e:
                span.set_status(1, str(e))
                raise
            finally:
                span.end()
        
        client.chat.completions.create = tracked_create
        return client
    
    def wrap_mistral(self, client: Any) -> Any:
        """Wrap Mistral AI client with Cost Guard protection"""
        original_create = client.chat.complete
        
        def tracked_create(*args, **kwargs):
            model = kwargs.get("model", "unknown")
            messages = kwargs.get("messages", [])
            max_tokens = kwargs.get("max_tokens", 1000)
            
            # Phase 1: Validate budget BEFORE API call
            validation = self._validate_request(model, messages, max_tokens)
            if not validation.get("allowed"):
                error_msg = validation.get("reason", "Budget limit reached")
                error = Exception(error_msg)
                error.code = "BUDGET_EXCEEDED"
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ❌ Request blocked: {error_msg}")
                raise error
            
            # Phase 2: Execute AI call
            if self.config.get("debug"):
                print(f"[AgentBill] Intercepting Mistral chat.complete with model: {model}")
            
            start_time = time.time()
            span = self.tracer.start_span("mistral.chat.complete", {
                "model": model,
                "provider": "mistral"
            })
            
            try:
                response = original_create(*args, **kwargs)
                latency = (time.time() - start_time) * 1000
                
                # Phase 3: Track actual usage
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                cost = self._estimate_cost(model, input_tokens, output_tokens)
                
                self._track_usage(model, "mistral", input_tokens, output_tokens, latency, cost)
                
                span.set_attributes({
                    "response.prompt_tokens": input_tokens,
                    "response.completion_tokens": output_tokens,
                    "response.total_tokens": response.usage.total_tokens,
                    "latency_ms": latency
                })
                span.set_status(0)
                
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ✓ Protected call completed: ${cost:.4f}")
                
                return response
            except Exception as e:
                span.set_status(1, str(e))
                raise
            finally:
                span.end()
        
        client.chat.complete = tracked_create
        return client
    
    def wrap_google_ai(self, client: Any) -> Any:
        """Wrap Google AI (Gemini) client with Cost Guard protection"""
        original_generate_content = client.generate_content
        
        def tracked_generate_content(*args, **kwargs):
            model = getattr(client, '_model_name', 'gemini-pro')
            content = args[0] if args else kwargs.get("contents", "")
            
            # Phase 1: Validate budget BEFORE API call
            validation = self._validate_request(model, content, 1000)
            if not validation.get("allowed"):
                error_msg = validation.get("reason", "Budget limit reached")
                error = Exception(error_msg)
                error.code = "BUDGET_EXCEEDED"
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ❌ Request blocked: {error_msg}")
                raise error
            
            # Phase 2: Execute AI call
            if self.config.get("debug"):
                print(f"[AgentBill] Intercepting Google AI generate_content")
            
            start_time = time.time()
            span = self.tracer.start_span("google_ai.generate_content", {
                "model": model,
                "provider": "google_ai"
            })
            
            try:
                response = original_generate_content(*args, **kwargs)
                latency = (time.time() - start_time) * 1000
                
                # Phase 3: Track actual usage
                input_tokens = 0
                output_tokens = 0
                if hasattr(response, 'usage_metadata'):
                    input_tokens = response.usage_metadata.prompt_token_count
                    output_tokens = response.usage_metadata.candidates_token_count
                
                cost = self._estimate_cost(model, input_tokens, output_tokens)
                self._track_usage(model, "google_ai", input_tokens, output_tokens, latency, cost)
                
                if hasattr(response, 'usage_metadata'):
                    span.set_attributes({
                        "response.prompt_tokens": input_tokens,
                        "response.completion_tokens": output_tokens,
                        "response.total_tokens": response.usage_metadata.total_token_count,
                        "latency_ms": latency
                    })
                
                span.set_status(0)
                
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ✓ Protected call completed: ${cost:.4f}")
                
                return response
            except Exception as e:
                span.set_status(1, str(e))
                raise
            finally:
                span.end()
        
        client.generate_content = tracked_generate_content
        return client
    
    def track_signal(self, **kwargs):
        """
        Track a custom signal/event with comprehensive parameters
        
        Supports all 68 parameters including optional trace_id and span_id for OTEL correlation:
        - event_name (required)
        - trace_id (optional) - For correlating with OTEL spans for cost reconciliation
        - span_id (optional) - For correlating with OTEL spans for cost reconciliation
        - agent_external_id (auto-filled from config if not provided)
        - data_source, timestamp
        - customer_external_id, account_external_id, user_external_id, 
          order_external_id, session_id, conversation_id, thread_id
        - model, provider, prompt_hash, prompt_sample, response_sample, function_name, tool_name
        - prompt_tokens, completion_tokens, total_tokens, streaming_tokens, cached_tokens, reasoning_tokens
        - latency_ms, time_to_first_token, time_to_action_ms, queue_time_ms, processing_time_ms
        - revenue, cost, conversion_value, revenue_source
        - experiment_id, experiment_group, variant_id, ab_test_name
        - conversion_type, conversion_step, funnel_stage, goal_achieved
        - feedback_score, user_satisfaction, error_type, error_message, retry_count, success_rate
        - tags, category, priority, severity, compliance_flag, data_classification
        - product_id, feature_flag, environment, deployment_version, region, tenant_id
        - parent_span_id
        - custom_dimensions, metadata, data
        
        Example:
            # Basic tracking
            agentbill.track_signal(
                event_name="user_conversion",
                revenue=99.99,
                customer_external_id="cust_123"
            )
            
            # With OTEL correlation for cost reconciliation
            trace_context = agentbill.tracer.start_span("ai_completion")
            # ... make AI call ...
            agentbill.track_signal(
                event_name="ai_request",
                revenue=5.00,
                trace_id=trace_context.trace_id,  # Optional
                span_id=trace_context.span_id     # Optional
            )
        """
        import httpx
        import time
        
        if "event_name" not in kwargs:
            raise ValueError("event_name is required")
        
        url = f"{self.config.get('base_url', 'https://bgwyprqxtdreuutzpbgw.supabase.co')}/functions/v1/record-signals"
        
        # Build payload with all provided parameters
        payload = {k: v for k, v in kwargs.items() if v is not None}
        
        # Auto-fill agent_id or agent_external_id from config if not provided (REQUIRED by API)
        if "agent_external_id" not in payload and "agent_id" not in payload:
            if "agent_external_id" in self.config:
                payload["agent_external_id"] = self.config["agent_external_id"]
            elif "agent_id" in self.config:
                payload["agent_id"] = self.config["agent_id"]
            else:
                raise ValueError(
                    "agent_id or agent_external_id is required. Either pass it in track_signal() or set it in AgentBill.init() config. "
                    "Example: AgentBill.init({'api_key': '...', 'agent_id': 'uuid-here'}) or agent_external_id: 'my-agent-1'"
                )
        
        # Auto-fill customer_id or customer_external_id from config if not provided
        if "customer_id" not in payload and "customer_external_id" not in payload:
            if "customer_id" in self.config:
                # Check if it's a UUID format - send as customer_id, else customer_external_id
                import re
                customer_val = self.config["customer_id"]
                is_uuid = bool(re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', customer_val, re.I))
                if is_uuid:
                    payload["customer_id"] = customer_val
                else:
                    payload["customer_external_id"] = customer_val
            elif "customer_external_id" in self.config:
                payload["customer_external_id"] = self.config["customer_external_id"]
        
        # Add timestamp if not provided
        if "timestamp" not in payload:
            payload["timestamp"] = time.time()
        
        try:
            with httpx.Client() as client:
                response = client.post(
                    url,
                    json=payload,
                    headers={
                        "X-API-Key": self.config['api_key'],
                        "Content-Type": "application/json"
                    },
                    timeout=10
                )
                if self.config.get("debug"):
                    trace_info = f" (trace: {kwargs.get('trace_id')})" if kwargs.get('trace_id') else ""
                    print(f"[AgentBill] Signal tracked: {kwargs.get('event_name')}{trace_info}")
                return response.status_code == 200
        except Exception as e:
            if self.config.get("debug"):
                print(f"[AgentBill] Failed to track signal: {e}")
            return False
    
    async def flush(self):
        """Flush pending telemetry data"""
        await self.tracer.flush()
