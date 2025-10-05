# LLM Chat Templates Library

A comprehensive collection of chat templates for Large Language Models (LLMs) across various model families and frameworks. This library provides practical examples, explanations, and implementation guidance for each template format.

## Table of Contents

1. [Understanding Chat Templates](#understanding-chat-templates)
2. [Meta LLaMA Series](#meta-llama-series)
3. [Mistral Series](#mistral-series)
4. [Microsoft Phi Series](#microsoft-phi-series)
5. [Google Gemma Series](#google-gemma-series)
6. [Alibaba Qwen Series](#alibaba-qwen-series)
7. [01-AI Yi Series](#01-ai-yi-series)
8. [TII Falcon Series](#tii-falcon-series)
9. [MosaicML MPT Series](#mosaicml-mpt-series)
10. [Stability AI StableLM](#stability-ai-stablelm)
11. [Universal Formats](#universal-formats)
12. [Specialised Templates](#specialised-templates)
13. [Implementation Best Practices](#implementation-best-practices)
14. [Quick Reference](#quick-reference)

---

## Understanding Chat Templates

### What are Chat Templates?

Chat templates are structured formats that define how conversations between users and AI assistants should be formatted for training and inference. They ensure consistent communication patterns and help models understand conversation structure.

### Key Components

- **System Messages**: Instructions that define the AI's behaviour and role
- **User Messages**: Input from the human user
- **Assistant Messages**: Responses from the AI model
- **Special Tokens**: Markers that indicate conversation boundaries and roles
- **Turn Management**: How multi-turn conversations are structured

### Template Categories

1. **Instruction-based**: Focus on task completion with clear instructions
2. **Conversational**: Natural dialogue format for chat applications
3. **Role-based**: Explicit role definitions for different participants
4. **Universal**: Compatible across multiple model families

---

## Meta LLaMA Series

### LLaMA 2 Chat

**Description**: The original LLaMA 2 chat format with system prompts and instruction tags.

**When to Use**:
- LLaMA 2-based models (7B, 13B, 70B)
- When you need system prompt support
- Instruction-following applications

**Template Structure**:
```
<s>[INST] <<SYS>>
{system_prompt}
<</SYS>>

{user_message} [/INST] {assistant_message} </s><s>[INST] {user_message_2} [/INST]
```

**Examples**:

**First Turn**:
```
<s>[INST] <<SYS>>
You are a helpful assistant.
<</SYS>>

What is AI? [/INST]
```

**Multi-turn**:
```
<s>[INST] <<SYS>>
You are a helpful assistant.
<</SYS>>

What is AI? [/INST] AI is artificial intelligence... </s><s>[INST] Tell me more [/INST]
```

**Jinja2 Template**:
```jinja2
{% if messages[0]['role'] == 'system' %}
    {% set system_message = messages[0]['content'] %}
    {% set messages = messages[1:] %}
{% else %}
    {% set system_message = "" %}
{% endif %}

{% for message in messages %}
    {% if loop.first and system_message != "" %}
        {{ '<s>[INST] <<SYS>>\n' + system_message + '\n<</SYS>>\n\n' + message['content'] + ' [/INST]' }}
    {% elif message['role'] == 'user' %}
        {{ '<s>[INST] ' + message['content'] + ' [/INST]' }}
    {% elif message['role'] == 'assistant' %}
        {{ ' ' + message['content'] + ' </s>' }}
    {% endif %}
{% endfor %}
```

**Special Tokens**:
- BOS: `<s>`
- EOS: `</s>`
- User start: `[INST]`
- User end: `[/INST]`

**Implementation Notes**:
- System prompts are optional but recommended
- Ensure proper tokenisation of special tokens
- Use consistent formatting across conversations

### LLaMA 3 / 3.1 / 3.2

**Description**: Updated format with header-based structure and improved tokenisation.

**When to Use**:
- LLaMA 3, 3.1, and 3.2 models
- When you need improved conversation handling
- Modern chat applications

**Template Structure**:
```
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>

{user_message}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

{assistant_message}<|eot_id|>
```

**Example**:
```
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful assistant<|eot_id|><|start_header_id|>user<|end_header_id|>

What is AI?<|eot_id|><|start_header_id|>assistant<|end_header_id|>

AI is artificial intelligence<|eot_id|><|start_header_id|>user<|end_header_id|>

Tell me more<|eot_id|><|start_header_id|>assistant<|end_header_id|>
```

**Jinja2 Template**:
```jinja2
{{ '<|begin_of_text|>' }}
{% for message in messages %}
    {{ '<|start_header_id|>' + message['role'] + '<|end_header_id|>\n\n' + message['content'] | trim + '<|eot_id|>' }}
{% endfor %}
{% if add_generation_prompt %}
    {{ '<|start_header_id|>assistant<|end_header_id|>\n\n' }}
{% endif %}
```

**Special Tokens**:
- BOS: `<|begin_of_text|>`
- EOS: `<|end_of_text|>`
- EOT: `<|eot_id|>` (end of turn)
- Header start: `<|start_header_id|>`
- Header end: `<|end_header_id|>`

**Implementation Notes**:
- More robust than LLaMA 2 format
- Better handling of multi-turn conversations
- Improved tokenisation efficiency

### LLaMA 3.3

**Description**: Same as LLaMA 3.1 format.

**When to Use**:
- LLaMA 3.3 models
- When you need the latest LLaMA format

**Implementation Notes**:
- Identical to LLaMA 3.1
- No changes required from 3.1 to 3.3

---

## Mistral Series

### Mistral v1/v2 (7B)

**Description**: Simple instruction format without system prompts.

**When to Use**:
- Mistral 7B models
- When you don't need system prompts
- Simple instruction-following tasks

**Template Structure**:
```
<s>[INST] {user_message} [/INST] {assistant_message}</s>[INST] {user_message_2} [/INST]
```

**With System (v2)**:
```
<s>[INST] {system_prompt}

{user_message} [/INST] {assistant_message}</s>
```

**Example**:
```
<s>[INST] What is AI? [/INST] AI is artificial intelligence</s>[INST] Tell me more [/INST]
```

**Jinja2 Template**:
```jinja2
{{ bos_token }}
{% for message in messages %}
    {% if (message['role'] == 'user') != (loop.index0 % 2 == 0) %}
        {{ raise_exception('Conversation roles must alternate user/assistant/user/assistant/...') }}
    {% endif %}
    {% if message['role'] == 'user' %}
        {{ '[INST] ' + message['content'] + ' [/INST]' }}
    {% elif message['role'] == 'assistant' %}
        {{ message['content'] + eos_token }}
    {% endif %}
{% endfor %}
```

**Special Tokens**:
- BOS: `<s>`
- EOS: `</s>`

**Implementation Notes**:
- Simpler than LLaMA format
- No system prompt support in v1
- Requires strict role alternation

### Mistral v3 (Mistral-Nemo, etc.)

**Description**: Updated format with tighter spacing.

**When to Use**:
- Mistral v3 models
- When you need the latest Mistral format

**Template Structure**:
```
<s>[INST] {user_message}[/INST]{assistant_message}</s>[INST] {user_message_2}[/INST]
```

**Implementation Notes**:
- No space before `[/INST]` and no space after
- More compact than previous versions

### Mistral Large / Medium

**Description**: Format for larger Mistral models.

**When to Use**:
- Mistral Large and Medium models
- When you need Mistral's most capable models

**Template Structure**:
```
<s>[INST] {user_message} [/INST] {assistant_message}</s> [INST] {user_message_2} [/INST]
```

**Implementation Notes**:
- Similar to v1/v2 but with updated spacing
- Compatible with larger model architectures

---

## Microsoft Phi Series

### Phi-1 / Phi-1.5

**Description**: Plain text format without special structure.

**When to Use**:
- Phi-1 and Phi-1.5 models
- When you need simple text completion
- Code generation tasks

**Template Structure**:
```
{text}
```

**Implementation Notes**:
- No special formatting required
- Best for completion tasks
- Not suitable for chat applications

### Phi-2

**Description**: Instruction-based format for Phi-2 models.

**When to Use**:
- Phi-2 models
- Instruction-following tasks
- When you need structured responses

**Template Structure**:
```
Instruct: {instruction}
Output: {output}
```

**Implementation Notes**:
- Clear instruction-output structure
- Good for task-oriented applications

### Phi-3 / 3.5 Mini/Medium

**Description**: Modern chat format with role-based structure.

**When to Use**:
- Phi-3 and Phi-3.5 models
- Chat applications
- When you need system prompt support

**Template Structure**:
```
<|system|>
{system_prompt}<|end|>
<|user|>
{user_message}<|end|>
<|assistant|>
{assistant_message}<|end|>
```

**Example**:
```
<|system|>
You are a helpful AI assistant.<|end|>
<|user|>
What is AI?<|end|>
<|assistant|>
AI is artificial intelligence<|end|>
<|user|>
Tell me more<|end|>
<|assistant|>
```

**Jinja2 Template**:
```jinja2
{% for message in messages %}
    {{ '<|' + message['role'] + '|>\n' + message['content'] + '<|end|>\n' }}
{% endfor %}
{% if add_generation_prompt %}
    {{ '<|assistant|>\n' }}
{% endif %}
```

**Special Tokens**:
- System: `<|system|>`
- User: `<|user|>`
- Assistant: `<|assistant|>`
- End: `<|end|>`

**Implementation Notes**:
- Clean, readable format
- Good for chat applications
- Supports system prompts

### Phi-4

**Description**: Similar to Phi-3 with potential updates.

**When to Use**:
- Phi-4 models
- When you need the latest Phi format

**Implementation Notes**:
- Similar to Phi-3
- May have minor updates or improvements

---

## Google Gemma Series

### Gemma 1 / 1.1

**Description**: Turn-based format with explicit role markers.

**When to Use**:
- Gemma 1 and 1.1 models
- Chat applications
- When you need clear role separation

**Template Structure**:
```
<start_of_turn>user
{user_message}<end_of_turn>
<start_of_turn>model
{assistant_message}<end_of_turn>
```

**Example**:
```
<start_of_turn>user
What is AI?<end_of_turn>
<start_of_turn>model
AI is artificial intelligence<end_of_turn>
<start_of_turn>user
Tell me more<end_of_turn>
<start_of_turn>model
```

**Jinja2 Template**:
```jinja2
{{ bos_token }}
{% for message in messages %}
    {{ '<start_of_turn>' + message['role'] + '\n' + message['content'] | trim + '<end_of_turn>\n' }}
{% endfor %}
{% if add_generation_prompt %}
    {{ '<start_of_turn>model\n' }}
{% endif %}
```

**Special Tokens**:
- BOS: `<bos>`
- EOS: `<eos>`
- Start turn: `<start_of_turn>`
- End turn: `<end_of_turn>`
- Role (user): `user`
- Role (model): `model`

**Implementation Notes**:
- Clear turn-based structure
- Good for chat applications
- Supports multi-turn conversations

### Gemma 2

**Description**: Same as Gemma 1 format.

**When to Use**:
- Gemma 2 models
- When you need the latest Gemma format

**Implementation Notes**:
- Identical to Gemma 1
- No changes required

---

## Alibaba Qwen Series

### Qwen 1 / 1.5

**Description**: ChatML-based format with role markers.

**When to Use**:
- Qwen 1 and 1.5 models
- Chat applications
- When you need ChatML compatibility

**Template Structure**:
```
<|im_start|>system
{system_prompt}<|im_end|>
<|im_start|>user
{user_message}<|im_end|>
<|im_start|>assistant
{assistant_message}<|im_end|>
```

**Example**:
```
<|im_start|>system
You are a helpful assistant.<|im_end|>
<|im_start|>user
What is AI?<|im_end|>
<|im_start|>assistant
AI is artificial intelligence<|im_end|>
```

**Jinja2 Template**:
```jinja2
{% for message in messages %}
    {{ '<|im_start|>' + message['role'] + '\n' + message['content'] + '<|im_end|>\n' }}
{% endfor %}
{% if add_generation_prompt %}
    {{ '<|im_start|>assistant\n' }}
{% endif %}
```

**Special Tokens**:
- Start: `<|im_start|>`
- End: `<|im_end|>`
- System/user/assistant roles

**Implementation Notes**:
- ChatML-compatible format
- Widely supported
- Good for chat applications

### Qwen 2 / 2.5

**Description**: Same as Qwen 1.5 format.

**When to Use**:
- Qwen 2 and 2.5 models
- When you need the latest Qwen format

**Implementation Notes**:
- Identical to Qwen 1.5
- No changes required

### Qwen 2.5-Coder

**Description**: Same as Qwen 2 format.

**When to Use**:
- Qwen 2.5-Coder models
- Code generation tasks
- When you need coding-specific models

**Implementation Notes**:
- Identical to Qwen 2
- Optimised for code generation

---

## 01-AI Yi Series

### Yi-1 / Yi-1.5

**Description**: ChatML-based format similar to Qwen.

**When to Use**:
- Yi-1 and Yi-1.5 models
- Chat applications
- When you need ChatML compatibility

**Template Structure**:
```
<|im_start|>user
{user_message}<|im_end|>
<|im_start|>assistant
{assistant_message}<|im_end|>
```

**With System**:
```
<|im_start|>system
{system_prompt}<|im_end|>
<|im_start|>user
{user_message}<|im_end|>
<|im_start|>assistant
{assistant_message}<|im_end|>
```

**Special Tokens**: Same as Qwen (ChatML-based)

**Implementation Notes**:
- ChatML-compatible format
- Similar to Qwen format
- Good for chat applications

---

## TII Falcon Series

### Falcon 7B/40B/180B Base

**Description**: No specific chat template (completion model).

**When to Use**:
- Falcon base models
- Text completion tasks
- When you need base model capabilities

**Template Structure**:
```
{text}
```

**Implementation Notes**:
- No special formatting required
- Best for completion tasks
- Not suitable for chat applications

### Falcon Instruct

**Description**: Simple instruction format for Falcon instruct models.

**When to Use**:
- Falcon instruct models
- Instruction-following tasks
- When you need simple instruction format

**Template Structure**:
```
User: {user_message}
Assistant: {assistant_message}
User: {user_message_2}
Assistant:
```

**Alternative**:
```
>>QUESTION<< {question}
>>ANSWER<< {answer}
```

**Implementation Notes**:
- Simple format
- Good for instruction-following
- Supports multi-turn conversations

---

## MosaicML MPT Series

### MPT-7B/30B Base

**Description**: No specific template.

**When to Use**:
- MPT base models
- Text completion tasks
- When you need base model capabilities

**Template Structure**:
```
{text}
```

**Implementation Notes**:
- No special formatting required
- Best for completion tasks

### MPT-Chat

**Description**: ChatML format for MPT chat models.

**When to Use**:
- MPT-Chat models
- Chat applications
- When you need ChatML compatibility

**Template Structure**:
```
<|im_start|>system
{system_prompt}<|im_end|>
<|im_start|>user
{user_message}<|im_end|>
<|im_start|>assistant
{assistant_message}<|im_end|>
```

**Special Tokens**: ChatML format

**Implementation Notes**:
- ChatML-compatible format
- Good for chat applications
- Supports system prompts

---

## Stability AI StableLM

### StableLM Base

**Description**: No specific template.

**When to Use**:
- StableLM base models
- Text completion tasks
- When you need base model capabilities

**Template Structure**:
```
{text}
```

**Implementation Notes**:
- No special formatting required
- Best for completion tasks

### StableLM-Zephyr

**Description**: Uses Zephyr format.

**When to Use**:
- StableLM-Zephyr models
- Chat applications
- When you need Zephyr format

**Implementation Notes**:
- Uses Zephyr format (see below)
- Good for chat applications

---

## Universal Formats

### ChatML (OpenAI-style)

**Description**: Universal format used by many models.

**When to Use**:
- Multiple model families
- When you need universal compatibility
- Chat applications

**Template Structure**:
```
<|im_start|>system
{system_prompt}<|im_end|>
<|im_start|>user
{user_message}<|im_end|>
<|im_start|>assistant
{assistant_message}<|im_end|>
```

**Example**:
```
<|im_start|>system
You are a helpful assistant<|im_end|>
<|im_start|>user
Hello<|im_end|>
<|im_start|>assistant
Hi there!<|im_end|>
<|im_start|>user
How are you?<|im_end|>
<|im_start|>assistant
```

**Used by**:
- Qwen series
- Yi series
- MPT-Chat
- Many other models

**Jinja2 Template**:
```jinja2
{% for message in messages %}
    {{ '<|im_start|>' + message['role'] + '\n' + message['content'] + '<|im_end|>\n' }}
{% endfor %}
{% if add_generation_prompt %}
    {{ '<|im_start|>assistant\n' }}
{% endif %}
```

**Implementation Notes**:
- Widely supported format
- Good for chat applications
- Supports system prompts

---

## Specialised Templates

### Vicuna

**Description**: Simple format for Vicuna models.

**When to Use**:
- Vicuna models
- Chat applications
- When you need simple format

**Vicuna v0**:
```
{system_prompt}

USER: {user_message}
ASSISTANT: {assistant_message}
USER: {user_message_2}
ASSISTANT:
```

**Vicuna v1 / v1.1**:
```
{system_prompt}

USER: {user_message}
ASSISTANT: {assistant_message}</s>USER: {user_message_2}
ASSISTANT:
```

**Example**:
```
A chat between a curious user and an artificial intelligence assistant.

USER: What is AI?
ASSISTANT: AI is artificial intelligence</s>USER: Tell me more
ASSISTANT:
```

**Implementation Notes**:
- Simple format
- Good for chat applications
- Supports multi-turn conversations

### Alpaca

**Description**: Instruction-based format for Alpaca models.

**When to Use**:
- Alpaca models
- Instruction-following tasks
- When you need structured responses

**Template Structure**:
```
Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Response:
{response}
```

**With Input**:
```
Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Input:
{input}

### Response:
{response}
```

**Implementation Notes**:
- Clear instruction structure
- Good for task-oriented applications
- Supports input context

### Zephyr (HuggingFace)

**Description**: Clean format for Zephyr models.

**When to Use**:
- Zephyr-7B models
- Chat applications
- When you need clean format

**Template Structure**:
```
<|system|>
{system_prompt}</s>
<|user|>
{user_message}</s>
<|assistant|>
{assistant_message}</s>
```

**Example**:
```
<|system|>
You are a helpful assistant</s>
<|user|>
What is AI?</s>
<|assistant|>
AI is artificial intelligence</s>
<|user|>
Tell me more</s>
<|assistant|>
```

**Jinja2 Template**:
```jinja2
{% for message in messages %}
    {{ '<|' + message['role'] + '|>\n' + message['content'] + eos_token + '\n' }}
{% endfor %}
{% if add_generation_prompt %}
    {{ '<|assistant|>\n' }}
{% endif %}
```

**Implementation Notes**:
- Clean, readable format
- Good for chat applications
- Supports system prompts

### OpenHermes

**Description**: ChatML format for OpenHermes models.

**When to Use**:
- OpenHermes 2.5 models
- Chat applications
- When you need ChatML compatibility

**Template Structure**:
```
<|im_start|>system
{system_prompt}<|im_end|>
<|im_start|>user
{user_message}<|im_end|>
<|im_start|>assistant
{assistant_message}<|im_end|>
```

**Implementation Notes**:
- Uses ChatML format
- Good for chat applications
- Supports system prompts

### Nous-Hermes

**Description**: Simple format for Nous-Hermes models.

**When to Use**:
- Nous-Hermes models
- Chat applications
- When you need simple format

**Template Structure**:
```
### System:
{system_prompt}

### User:
{user_message}

### Assistant:
{assistant_message}
```

**Nous-Hermes 2**: Uses ChatML

**Implementation Notes**:
- Simple format
- Good for chat applications
- Supports system prompts

### OpenChat

**Description**: GPT4-corrected format for OpenChat models.

**When to Use**:
- OpenChat 3.5 models
- Chat applications
- When you need GPT4-corrected format

**Template Structure**:
```
GPT4 Correct User: {user_message}<|end_of_turn|>GPT4 Correct Assistant: {assistant_message}<|end_of_turn|>
```

**Example**:
```
GPT4 Correct User: What is AI?<|end_of_turn|>GPT4 Correct Assistant: AI is artificial intelligence<|end_of_turn|>GPT4 Correct User: Tell me more<|end_of_turn|>GPT4 Correct Assistant:
```

**Implementation Notes**:
- GPT4-corrected format
- Good for chat applications
- Supports multi-turn conversations

### Solar

**Description**: Simple format for Solar models.

**When to Use**:
- Solar 10.7B Instruct models
- Chat applications
- When you need simple format

**Template Structure**:
```
### User:
{user_message}

### Assistant:
{assistant_message}
```

**Implementation Notes**:
- Simple format
- Good for chat applications
- Supports multi-turn conversations

### Deepseek

**Description**: Instruction-based format for Deepseek models.

**When to Use**:
- Deepseek-Coder and Deepseek-Chat models
- Code generation and chat applications
- When you need instruction format

**Deepseek-Coder**:
```
### Instruction:
{instruction}

### Response:
{response}
```

**Deepseek-Chat**:
```
User: {user_message}RetryDIs that everything?EditThinking about context of vague confirmation queryThe user is asking me to provide chat templates for open source models. Let me continue with more models.{assistant_message}
User: {user_message_2}RetryDplease continueEditThinking about continuing an unspecified previous interactionThe user is asking for chat templates for open source models. Let me continue with more models.
```

**Alternative (newer)**:
```
<|begin▁of▁sentence|>User: {user_message}RetryClaude can make mistakes. Please double-check responses.
```

**Implementation Notes**:
- Instruction-based format
- Good for code generation
- Supports chat applications

---

## Implementation Best Practices

### Template Selection

1. **Model Compatibility**: Choose templates that match your target model
2. **Use Case**: Select formats appropriate for your application
3. **System Prompts**: Use formats that support system prompts when needed
4. **Multi-turn Support**: Ensure templates handle conversation history

### Tokenisation Considerations

1. **Special Tokens**: Ensure proper tokenisation of special tokens
2. **Token Limits**: Consider context length limitations
3. **Efficiency**: Choose formats that minimise token usage
4. **Consistency**: Use consistent formatting across conversations

### Error Handling

1. **Role Validation**: Ensure proper role alternation
2. **Format Validation**: Validate template structure before use
3. **Fallback Formats**: Have fallback options for unsupported models
4. **Testing**: Test templates with various conversation patterns

### Performance Optimisation

1. **Caching**: Cache formatted conversations when possible
2. **Batch Processing**: Use efficient batch processing for multiple conversations
3. **Memory Management**: Consider memory usage for large conversations
4. **Streaming**: Support streaming for real-time applications

---

## Quick Reference

### Template Comparison

| Model Family | Format Type | System Support | Multi-turn | Special Tokens |
|--------------|-------------|----------------|------------|----------------|
| LLaMA 2 | Instruction | Yes | Yes | `<s>`, `[INST]`, `[/INST]` |
| LLaMA 3 | Header-based | Yes | Yes | `<|begin_of_text|>`, `<|eot_id|>` |
| Mistral | Simple | No (v1) | Yes | `<s>`, `[INST]`, `[/INST]` |
| Phi-3 | Role-based | Yes | Yes | `<|system|>`, `<|end|>` |
| Gemma | Turn-based | Yes | Yes | `<start_of_turn>`, `<end_of_turn>` |
| Qwen | ChatML | Yes | Yes | `<|im_start|>`, `<|im_end|>` |
| Yi | ChatML | Yes | Yes | `<|im_start|>`, `<|im_end|>` |
| Falcon | Simple | No | Yes | `User:`, `Assistant:` |
| MPT | ChatML | Yes | Yes | `<|im_start|>`, `<|im_end|>` |
| ChatML | Universal | Yes | Yes | `<|im_start|>`, `<|im_end|>` |

### Format Categories

| Category | Description | Best For | Examples |
|----------|-------------|----------|----------|
| Instruction | Task-oriented with clear instructions | Task completion | Alpaca, Deepseek |
| Conversational | Natural dialogue format | Chat applications | LLaMA, Mistral |
| Role-based | Explicit role definitions | Structured conversations | Phi-3, Gemma |
| Universal | Compatible across models | Multi-model support | ChatML |

### Implementation Checklist

- [ ] Choose appropriate template for your model
- [ ] Validate template structure and special tokens
- [ ] Test with various conversation patterns
- [ ] Implement proper error handling
- [ ] Consider performance implications
- [ ] Document template usage and limitations
- [ ] Test with different model sizes and configurations
- [ ] Validate multi-turn conversation handling

### Common Pitfalls to Avoid

1. **Token Mismatches**: Ensure special tokens match model expectations
2. **Role Confusion**: Maintain consistent role alternation
3. **System Prompt Issues**: Handle system prompts correctly
4. **Context Length**: Monitor conversation length and token limits
5. **Format Inconsistency**: Use consistent formatting across conversations
6. **Error Handling**: Implement proper validation and error handling
7. **Performance**: Consider performance implications of template choice
8. **Compatibility**: Ensure template compatibility with target models

---

*This library is continuously updated with new model formats and best practices. For specific implementation questions or contributions, please refer to the project documentation.*