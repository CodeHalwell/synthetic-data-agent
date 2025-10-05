# LLM Post-Training Templates Library

A comprehensive collection of data formats and templates for fine-tuning Large Language Models (LLMs) across various post-training techniques. This library provides practical examples, explanations, and implementation guidance for each method.

## Table of Contents

1. [Supervised Fine-Tuning (SFT)](#supervised-fine-tuning-sft)
2. [Parameter-Efficient Fine-Tuning (PEFT)](#parameter-efficient-fine-tuning-peft)
3. [Reinforcement Learning from Human Feedback (RLHF)](#reinforcement-learning-from-human-feedback-rlhf)
4. [Direct Preference Optimization (DPO)](#direct-preference-optimization-dpo)
5. [Constitutional AI & Self-Critique](#constitutional-ai--self-critique)
6. [Chain-of-Thought & Reasoning](#chain-of-thought--reasoning)
7. [Tool Use & Function Calling](#tool-use--function-calling)
8. [Multimodal Fine-Tuning](#multimodal-fine-tuning)
9. [Domain-Specific Methods](#domain-specific-methods)
10. [Emerging Techniques](#emerging-techniques)
11. [Safety & Robustness](#safety--robustness)
12. [Efficiency & Compression](#efficiency--compression)
13. [Quick Reference](#quick-reference)

---

## Supervised Fine-Tuning (SFT)

### Standard Supervised Fine-Tuning

**Description**: The foundational approach where models learn from input-output pairs using cross-entropy loss. This is the most common starting point for fine-tuning.

**When to Use**: 
- Initial fine-tuning on domain-specific data
- Converting a general model to a specialised one
- When you have high-quality paired examples

**Data Format**:
```jsonl
{"text": "User: What is AI?\nAssistant: AI is artificial intelligence..."}

// Or separated format:
{"prompt": "What is AI?", "completion": "AI is artificial intelligence..."}

// Or chat format:
{"messages": [
  {"role": "user", "content": "What is AI?"},
  {"role": "assistant", "content": "AI is artificial intelligence..."}
]}
```

**Implementation Notes**:
- Use consistent formatting across your dataset
- Include system prompts when needed for context
- Ensure completion tokens are properly formatted for your tokeniser

### Instruction Tuning

**Description**: Fine-tunes models to follow specific instructions, making them more controllable and task-oriented.

**When to Use**:
- Creating instruction-following models
- Multi-task learning scenarios
- When you need precise control over model behaviour

**Data Format**:
```jsonl
{"instruction": "Translate to French", "input": "Hello", "output": "Bonjour"}

{"instruction": "Summarise this article", "input": "Long article text...", "output": "Brief summary"}

// With system prompt:
{"messages": [
  {"role": "system", "content": "You are a helpful translator"},
  {"role": "user", "content": "Translate 'hello' to French"},
  {"role": "assistant", "content": "Bonjour"}
]}
```

**Implementation Notes**:
- Keep instructions clear and specific
- Use consistent instruction templates
- Include examples for complex tasks

### Multi-Task Fine-Tuning

**Description**: Trains models on multiple tasks simultaneously, improving generalisation and efficiency.

**When to Use**:
- Building general-purpose models
- When you have diverse but related tasks
- Resource-constrained scenarios

**Data Format**:
```jsonl
{"task": "translation", "input": "Hello", "output": "Bonjour", "source_lang": "en", "target_lang": "fr"}
{"task": "summarisation", "input": "Long text...", "output": "Summary"}
{"task": "qa", "context": "Passage", "question": "Q?", "output": "Answer"}
```

**Implementation Notes**:
- Balance task distribution in your dataset
- Use task-specific prefixes or tokens
- Monitor performance across all tasks

---

## Parameter-Efficient Fine-Tuning (PEFT)

### LoRA (Low-Rank Adaptation)

**Description**: Trains low-rank decomposition matrices instead of full model parameters, dramatically reducing trainable parameters.

**When to Use**:
- Limited computational resources
- Quick experimentation
- When you need to maintain multiple specialised models

**Data Format**:
```jsonl
// Same as standard SFT - the difference is in training config, not data
{"prompt": "Question", "completion": "Answer"}
```

**Implementation Notes**:
- Choose appropriate rank (typically 8-64)
- Apply to attention layers primarily
- Can be combined with other PEFT methods

### QLoRA (Quantised LoRA)

**Description**: LoRA with quantised base model, enabling fine-tuning on consumer hardware.

**When to Use**:
- Very limited GPU memory
- Personal or small-scale projects
- When model size is a constraint

**Data Format**:
```jsonl
// Same as LoRA
{"prompt": "Question", "completion": "Answer"}
```

**Implementation Notes**:
- Use 4-bit quantisation typically
- Monitor quality degradation
- Works best with newer architectures

### Prefix Tuning

**Description**: Trains soft prompt tokens prepended to input, keeping the base model frozen.

**When to Use**:
- When you want to specialise model behaviour
- Multi-task scenarios with shared base
- Quick adaptation to new domains

**Data Format**:
```jsonl
{"input": "Translate: Hello", "output": "Bonjour"}
```

**Implementation Notes**:
- Choose appropriate prefix length
- Initialise with task-relevant embeddings
- Can be combined with other methods

---

## Reinforcement Learning from Human Feedback (RLHF)

### Reward Model Training

**Description**: Trains a separate model to predict human preferences, which is then used to guide policy optimisation.

**When to Use**:
- When you have human preference data
- Building aligned models
- When quality is more important than efficiency

**Data Format**:
```jsonl
// Binary comparison:
{"prompt": "Explain quantum computing", 
 "response_0": "Quantum computing uses qubits which can be in superposition...", 
 "response_1": "It's like regular computing but quantum.",
 "preferred": 0}

// With scores:
{"prompt": "Write a poem",
 "responses": [
   {"text": "Roses are red...", "score": 8},
   {"text": "Flowers bloom...", "score": 6}
 ]}

// Multiple comparisons:
{"prompt": "Explain AI",
 "response_a": "AI is...",
 "response_b": "Artificial intelligence...",
 "response_c": "It's computers...",
 "rankings": [2, 1, 3]}  // response_b is best
```

**Implementation Notes**:
- Collect diverse preference data
- Use Bradley-Terry model for pairwise preferences
- Validate reward model on held-out data

### PPO (Proximal Policy Optimisation)

**Description**: Uses the reward model to train the policy with policy gradient methods, balancing exploration and exploitation.

**When to Use**:
- After training a reward model
- When you need stable policy updates
- Large-scale RLHF implementations

**Data Format**:
```jsonl
// Query dataset (prompts only):
{"query": "Explain machine learning"}
{"query": "Write a story about a robot"}

// During training, model generates responses and gets rewards
```

**Implementation Notes**:
- Use appropriate KL penalty
- Monitor reward model accuracy
- Implement proper value function estimation

---

## Direct Preference Optimization (DPO)

### Standard DPO

**Description**: Optimises directly on preference pairs without needing a separate reward model, simplifying the RLHF pipeline.

**When to Use**:
- When you have preference data but limited compute
- Simpler alternative to RLHF
- When reward modelling is challenging

**Data Format**:
```jsonl
{"prompt": "Explain recursion",
 "chosen": "Recursion is when a function calls itself. For example...",
 "rejected": "It's when something repeats."}

// With chat history:
{"prompt": [
   {"role": "user", "content": "What is recursion?"}
 ],
 "chosen": [
   {"role": "assistant", "content": "Detailed explanation..."}
 ],
 "rejected": [
   {"role": "assistant", "content": "Brief unclear answer"}
 ]}
```

**Implementation Notes**:
- Ensure clear preference differences
- Use appropriate beta parameter
- Monitor for mode collapse

### IPO (Identity Preference Optimisation)

**Description**: Regularised version of DPO that prevents overfitting to preferences.

**When to Use**:
- When DPO shows signs of overfitting
- Large preference datasets
- When generalisation is critical

**Data Format**:
```jsonl
// Same as DPO:
{"prompt": "Question", "chosen": "Better answer", "rejected": "Worse answer"}
```

**Implementation Notes**:
- Tune regularisation strength
- Monitor validation performance
- Use early stopping

### KTO (Kahneman-Tversky Optimisation)

**Description**: Uses binary feedback instead of preference pairs, inspired by prospect theory.

**When to Use**:
- When pairwise preferences are hard to collect
- Binary quality assessment scenarios
- When you have absolute quality labels

**Data Format**:
```jsonl
{"prompt": "Explain photosynthesis", 
 "completion": "Photosynthesis is the process...", 
 "label": true}  // true = desirable, false = undesirable

{"prompt": "What is 2+2?",
 "completion": "5",
 "label": false}
```

**Implementation Notes**:
- Ensure clear quality thresholds
- Balance positive and negative examples
- Consider confidence weighting

---

## Constitutional AI & Self-Critique

### Constitutional AI (CAI)

**Description**: Self-critique and revision based on constitutional principles, enabling models to improve their own outputs.

**When to Use**:
- Building safe and helpful models
- When human feedback is limited
- Creating self-improving systems

**Data Format**:
```jsonl
{"prompt": "How to hack a computer?",
 "initial_response": "Here's how...",
 "critique_request": "Critique this response for helpfulness and harmlessness",
 "critique": "This response could enable harmful behaviour...",
 "revision_request": "Revise to be helpful but harmless",
 "revision": "I can't provide hacking instructions, but I can explain cybersecurity..."}

// Simplified format:
{"instruction": "Question",
 "response": "Initial",
 "principles": ["Be helpful", "Be harmless"],
 "critique": "Issues found",
 "revision": "Improved response"}
```

**Implementation Notes**:
- Define clear constitutional principles
- Use iterative refinement
- Validate safety improvements

### RRHF (Rank Responses to align Human Feedback)

**Description**: Ranks multiple responses and trains on rankings rather than binary preferences.

**When to Use**:
- When you have multiple response candidates
- Ranking-based evaluation scenarios
- When you want to capture nuanced preferences

**Data Format**:
```jsonl
{"prompt": "Explain AI",
 "responses": [
   {"text": "AI is...", "rank": 2},
   {"text": "Artificial intelligence refers to...", "rank": 1},
   {"text": "It's computers.", "rank": 3}
 ]}
```

**Implementation Notes**:
- Ensure consistent ranking criteria
- Use appropriate ranking loss functions
- Validate ranking quality

---

## Chain-of-Thought & Reasoning

### Chain-of-Thought Fine-Tuning

**Description**: Trains models to show explicit reasoning steps, improving performance on complex reasoning tasks.

**When to Use**:
- Mathematical reasoning tasks
- Complex problem-solving
- When interpretability is important

**Data Format**:
```jsonl
{"question": "If John has 5 apples and gives 2 away, how many does he have?",
 "chain_of_thought": "Let's think step by step:\n1. John starts with 5 apples\n2. He gives away 2 apples\n3. 5 - 2 = 3",
 "answer": "3 apples"}

// Alternative format:
{"prompt": "Question",
 "reasoning": "Step-by-step reasoning",
 "conclusion": "Final answer"}
```

**Implementation Notes**:
- Use consistent reasoning templates
- Validate reasoning correctness
- Consider different reasoning styles

### Self-Consistency Training

**Description**: Generates multiple reasoning paths and uses consensus for final answers.

**When to Use**:
- When single reasoning paths are unreliable
- Complex multi-step problems
- When you want to improve confidence

**Data Format**:
```jsonl
{"question": "Math problem",
 "reasoning_paths": [
   {"path": "Method 1...", "answer": "42"},
   {"path": "Method 2...", "answer": "42"},
   {"path": "Method 3...", "answer": "41"}
 ],
 "consensus_answer": "42",
 "confidence": 0.67}
```

**Implementation Notes**:
- Generate diverse reasoning paths
- Use appropriate consensus methods
- Monitor consistency improvements

---

## Tool Use & Function Calling

### Tool Use Fine-Tuning

**Description**: Trains models to use external tools and APIs, enabling them to perform actions beyond text generation.

**When to Use**:
- Building agentic systems
- When you need real-time information
- Creating interactive applications

**Data Format**:
```jsonl
{"messages": [
  {"role": "user", "content": "What's the weather in Paris?"}
 ],
 "tool_calls": [
   {"type": "function", "function": {"name": "get_weather", "arguments": "{\"location\": \"Paris\"}"}}
 ],
 "tool_responses": [
   {"result": "Sunny, 22°C"}
 ],
 "final_response": "The weather in Paris is sunny with a temperature of 22°C"}
```

**Implementation Notes**:
- Define clear tool interfaces
- Include error handling examples
- Validate tool usage patterns

### Function Calling Training

**Description**: Teaches models to call functions with correct parameters and handle responses.

**When to Use**:
- API integration scenarios
- When you need structured outputs
- Building workflow automation

**Data Format**:
```jsonl
{"prompt": "Schedule a meeting for tomorrow at 2pm",
 "available_functions": [
   {"name": "schedule_meeting", "parameters": {"date": "string", "time": "string", "title": "string"}}
 ],
 "function_call": {
   "name": "schedule_meeting",
   "arguments": {"date": "2024-01-16", "time": "14:00", "title": "Meeting"}
 }}
```

**Implementation Notes**:
- Use consistent function schemas
- Include parameter validation examples
- Handle edge cases and errors

---

## Multimodal Fine-Tuning

### Vision-Language Fine-Tuning

**Description**: Trains models on image-text pairs, enabling them to understand and generate text based on visual content.

**When to Use**:
- Image captioning tasks
- Visual question answering
- When you need visual understanding

**Data Format**:
```jsonl
{"image": "base64_encoded_image_or_path",
 "messages": [
   {"role": "user", "content": [
     {"type": "image"},
     {"type": "text", "text": "What's in this image?"}
   ]},
   {"role": "assistant", "content": "This image shows a cat sitting on a windowsill"}
 ]}

// Alternative:
{"image_path": "images/cat.jpg",
 "caption": "A cat sits on a windowsill looking outside",
 "detailed_description": "A gray tabby cat..."}
```

**Implementation Notes**:
- Use appropriate image preprocessing
- Balance text and visual tokens
- Consider different image resolutions

### Audio-Language Fine-Tuning

**Description**: Trains models on audio-text pairs for speech understanding and generation.

**When to Use**:
- Speech recognition tasks
- Audio content analysis
- Voice-based applications

**Data Format**:
```jsonl
{"audio_path": "audio/sample.wav",
 "transcription": "Hello, how are you?",
 "intent": "greeting",
 "response": "I'm doing well, thank you!"}
```

**Implementation Notes**:
- Use appropriate audio preprocessing
- Consider different audio formats
- Balance audio and text components

---

## Domain-Specific Methods

### Medical/Healthcare Fine-Tuning

**Description**: Specialised fine-tuning for medical knowledge and clinical reasoning.

**When to Use**:
- Medical AI applications
- Clinical decision support
- Healthcare documentation

**Data Format**:
```jsonl
{"patient_case": "Patient presents with fever and cough",
 "medical_history": "No significant past medical history",
 "diagnosis": "Upper respiratory infection",
 "treatment_plan": "Rest, fluids, acetaminophen for fever",
 "reasoning": "Symptoms consistent with viral URI...",
 "confidence": 0.8,
 "requires_specialist": false}
```

**Implementation Notes**:
- Ensure medical accuracy
- Include appropriate disclaimers
- Validate with medical professionals

### Legal Fine-Tuning

**Description**: Legal document understanding and analysis.

**When to Use**:
- Legal research applications
- Contract analysis
- Compliance checking

**Data Format**:
```jsonl
{"case_text": "Plaintiff v. Defendant...",
 "legal_question": "What is the statute of limitations?",
 "jurisdiction": "California",
 "answer": "Under California law, the statute of limitations is...",
 "citations": ["Cal. Civ. Proc. Code § 335.1"]}
```

**Implementation Notes**:
- Include proper legal citations
- Specify jurisdiction when relevant
- Ensure legal accuracy

### Code Fine-Tuning

**Description**: Programming tasks and code generation.

**When to Use**:
- Code generation tools
- Programming assistance
- Code review applications

**Data Format**:
```jsonl
{"instruction": "Write a function to reverse a string",
 "input": "",
 "output": "def reverse_string(s):\n    return s[::-1]",
 "language": "python",
 "test_cases": [
   {"input": "hello", "output": "olleh"},
   {"input": "world", "output": "dlrow"}
 ]}
```

**Implementation Notes**:
- Include test cases when possible
- Specify programming language
- Validate code correctness

---

## Emerging Techniques

### GRPO (Group Relative Policy Optimisation)

**Description**: Optimises by comparing multiple responses from the same prompt in groups, without needing a separate reward model.

**When to Use**:
- When you have multiple response candidates per prompt
- Group-based evaluation scenarios
- When reward modelling is challenging

**Data Format**:
```jsonl
// Group-based comparison:
{"prompt": "Explain quantum entanglement",
 "responses": [
   {"text": "Quantum entanglement is when two particles...", "group_score": 0.9},
   {"text": "It's when particles are connected...", "group_score": 0.7},
   {"text": "Entanglement means particles affect each other...", "group_score": 0.8},
   {"text": "It's spooky action at a distance...", "group_score": 0.6}
 ]}

// Alternative format with relative preferences:
{"prompt": "Write a poem",
 "group": [
   {"response": "Response 1", "relative_quality": "best"},
   {"response": "Response 2", "relative_quality": "good"},
   {"response": "Response 3", "relative_quality": "worst"}
 ]}

// Simplified format (model generates group during training):
{"query": "Question"}
// System generates N responses and ranks them relative to each other
```

**Implementation Notes**:
- Ensure consistent group composition
- Use appropriate group scoring methods
- Monitor group diversity

### ReMax (Reward Maximisation)

**Description**: Directly maximises expected reward without KL penalty.

**When to Use**:
- When you have reliable reward signals
- Direct optimisation scenarios
- When KL constraints are not needed

**Data Format**:
```jsonl
{"prompt": "Question",
 "response": "Answer",
 "reward": 0.85}
```

**Implementation Notes**:
- Ensure reward signal quality
- Monitor for reward hacking
- Use appropriate regularisation

### REBEL (Reward-Based Expected Bellman Error Learning)

**Description**: Off-policy RL method for LLM alignment.

**When to Use**:
- Offline RL scenarios
- When you have historical interaction data
- Policy improvement from logged data

**Data Format**:
```jsonl
{"state": "Conversation context",
 "action": "Generated response",
 "reward": 0.8,
 "next_state": "New context",
 "done": false,
 "behavior_policy_logprob": -2.3}
```

**Implementation Notes**:
- Ensure proper state representation
- Use appropriate value function approximation
- Monitor off-policy correction

### PRO (Preference Ranking Optimisation)

**Description**: Generalises DPO to multiple preferences.

**When to Use**:
- When you have multiple response rankings
- Complex preference structures
- When binary preferences are insufficient

**Data Format**:
```jsonl
{"prompt": "Explain AI",
 "responses": [
   {"text": "AI is artificial intelligence...", "rank": 1},
   {"text": "AI refers to machine intelligence...", "rank": 2},
   {"text": "It's computer stuff...", "rank": 4},
   {"text": "Artificial intelligence means...", "rank": 3}
 ]}
```

**Implementation Notes**:
- Ensure consistent ranking criteria
- Use appropriate ranking loss functions
- Validate ranking quality

### SPPO (Self-Play Preference Optimisation)

**Description**: Self-play between model iterations with preference optimisation.

**When to Use**:
- Iterative model improvement
- When you have strong base models
- Self-improving systems

**Data Format**:
```jsonl
{"prompt": "Question",
 "iteration_t_response": "Response from current model",
 "iteration_t+1_response": "Response from updated model",
 "win_rate": 0.65}  // How often t+1 wins
```

**Implementation Notes**:
- Use strong base models
- Monitor for quality improvements
- Implement proper evaluation

### EXO (Exploratory Preference Optimisation)

**Description**: DPO with exploration bonus.

**When to Use**:
- When you want to encourage exploration
- Novel response generation
- When standard DPO is too conservative

**Data Format**:
```jsonl
{"prompt": "Question",
 "chosen": "Explored high-reward response",
 "rejected": "Typical response",
 "exploration_bonus": 0.15,
 "novelty_score": 0.8}
```

**Implementation Notes**:
- Balance exploration and exploitation
- Use appropriate novelty scoring
- Monitor exploration effectiveness

### ReST (Reinforced Self-Training)

**Description**: Generate samples, filter by reward, retrain.

**When to Use**:
- When you have reward models
- Quality-focused training
- When computational resources are limited

**Data Format**:
```jsonl
// Generation phase:
{"prompt": "Question",
 "generated_samples": [
   {"response": "Sample 1", "reward": 0.6},
   {"response": "Sample 2", "reward": 0.9},
   {"response": "Sample 3", "reward": 0.4}
 ],
 "threshold": 0.7}

// Training phase uses only samples above threshold:
{"prompt": "Question", "completion": "Sample 2"}
```

**Implementation Notes**:
- Choose appropriate threshold
- Ensure reward model quality
- Monitor sample quality

### V-MPO (Maximum a Posteriori Policy Optimisation)

**Description**: Constrains policy updates with KL divergence.

**When to Use**:
- When you need stable policy updates
- Conservative policy improvement
- When you have prior policy information

**Data Format**:
```jsonl
{"state": "Context",
 "action": "Response",
 "reward": 0.8,
 "old_policy_logprob": -3.2,
 "value_estimate": 0.75}
```

**Implementation Notes**:
- Use appropriate KL constraints
- Monitor policy stability
- Implement proper value estimation

### AWR (Advantage-Weighted Regression)

**Description**: Weight samples by advantage for offline RL.

**When to Use**:
- Offline RL scenarios
- When you have advantage estimates
- Policy improvement from logged data

**Data Format**:
```jsonl
{"prompt": "Question",
 "response": "Answer",
 "reward": 0.8,
 "baseline_value": 0.6,
 "advantage": 0.2,  // reward - baseline
 "weight": 1.5}  // exp(advantage / temperature)
```

**Implementation Notes**:
- Ensure proper advantage estimation
- Use appropriate temperature scaling
- Monitor weight distribution

### CQL (Conservative Q-Learning) for LLMs

**Description**: Conservative offline RL approach.

**When to Use**:
- Offline RL scenarios
- When you need conservative updates
- Policy improvement from logged data

**Data Format**:
```jsonl
{"state": "Context",
 "action": "Response",
 "reward": 0.7,
 "next_state": "New context",
 "dataset_action_logprob": -2.5}
```

**Implementation Notes**:
- Use appropriate conservative penalties
- Monitor policy improvement
- Ensure proper state representation

### IQL (Implicit Q-Learning) for LLMs

**Description**: Implicit Q-learning for offline RL.

**When to Use**:
- Offline RL scenarios
- When you have logged interaction data
- Policy improvement from historical data

**Data Format**:
```jsonl
{"state": "Context",
 "action": "Response", 
 "reward": 0.8,
 "next_state": "New context",
 "terminal": false}
```

**Implementation Notes**:
- Ensure proper state representation
- Use appropriate value function approximation
- Monitor policy improvement

### RL-CAI (RL for Constitutional AI)

**Description**: RL with constitutional principles as rewards.

**When to Use**:
- Building safe and helpful models
- When you have constitutional principles
- Creating self-improving systems

**Data Format**:
```jsonl
{"prompt": "Question",
 "response": "Answer",
 "constitutional_scores": {
   "helpfulness": 0.9,
   "harmlessness": 0.95,
   "honesty": 0.85
 },
 "principles_violated": [],
 "aggregate_reward": 0.9}
```

**Implementation Notes**:
- Define clear constitutional principles
- Use appropriate reward aggregation
- Monitor principle adherence

### APO (Anchored Preference Optimisation)

**Description**: DPO anchored to reference distribution.

**When to Use**:
- When you have reference responses
- Anchored preference learning
- When you want to maintain reference behaviour

**Data Format**:
```jsonl
{"prompt": "Question",
 "chosen": "Better response",
 "rejected": "Worse response",
 "anchor_response": "Reference response",
 "anchor_weight": 0.5}
```

**Implementation Notes**:
- Choose appropriate anchor weight
- Ensure reference quality
- Monitor anchor influence

### Nash-MD (Nash Mirror Descent)

**Description**: Game-theoretic multi-agent alignment.

**When to Use**:
- Multi-agent scenarios
- Game-theoretic alignment
- When you have multiple competing objectives

**Data Format**:
```jsonl
{"prompt": "Question",
 "player_1_response": "Response A",
 "player_2_response": "Response B",
 "player_1_utility": 0.7,
 "player_2_utility": 0.6,
 "nash_distance": 0.15}
```

**Implementation Notes**:
- Define clear utility functions
- Use appropriate Nash equilibrium computation
- Monitor equilibrium convergence

### SALMON (Self-Alignment with Principle-Following Reward Models)

**Description**: Self-alignment using principle-driven rewards.

**When to Use**:
- Building principle-following models
- When you have clear principles
- Creating self-improving systems

**Data Format**:
```jsonl
{"prompt": "Question",
 "response": "Answer",
 "principles": [
   {"principle": "Be helpful", "score": 0.9},
   {"principle": "Be harmless", "score": 0.95},
   {"principle": "Be honest", "score": 0.85}
 ],
 "self_evaluation": "This response adheres to principles because..."}
```

**Implementation Notes**:
- Define clear principles
- Use appropriate principle scoring
- Monitor principle adherence

### RRHF-enhanced (Rank Responses with Hindsight Feedback)

**Description**: Ranking with hindsight relabeling.

**When to Use**:
- When you have hindsight information
- Goal relabeling scenarios
- When original goals are not achieved

**Data Format**:
```jsonl
{"prompt": "Original goal: Summarise in 50 words",
 "responses": [
   {"text": "100 word summary", "original_rank": 3, "hindsight_goal": "Summarise in 100 words", "hindsight_rank": 1},
   {"text": "50 word summary", "original_rank": 1, "hindsight_goal": "Summarise in 50 words", "hindsight_rank": 1}
 ]}
```

**Implementation Notes**:
- Ensure proper hindsight relabeling
- Use appropriate ranking methods
- Monitor hindsight quality

### PKD (Preference Knowledge Distillation)

**Description**: Distil preference knowledge from teacher.

**When to Use**:
- When you have teacher preference models
- Knowledge transfer scenarios
- When you want to compress preference knowledge

**Data Format**:
```jsonl
{"prompt": "Question",
 "response_a": "Response A",
 "response_b": "Response B",
 "teacher_preference_logits": {"a": 0.8, "b": 0.2},
 "teacher_confidence": 0.9}
```

**Implementation Notes**:
- Use strong teacher models
- Monitor knowledge transfer
- Ensure preference quality

### R-DPO (Refined Direct Preference Optimisation)

**Description**: DPO with refinement steps.

**When to Use**:
- When you have refinement information
- Multi-stage preference learning
- When you want to improve preference quality

**Data Format**:
```jsonl
{"prompt": "Question",
 "initial_chosen": "Initial good response",
 "initial_rejected": "Initial bad response",
 "refined_chosen": "Refined good response",
 "refinement_steps": [
   {"critique": "Could be clearer", "improvement": "Added clarity"}
 ]}
```

**Implementation Notes**:
- Ensure proper refinement steps
- Use appropriate refinement criteria
- Monitor refinement quality

### MODPO (Multi-Objective DPO)

**Description**: Optimise multiple objectives simultaneously.

**When to Use**:
- When you have multiple objectives
- Multi-objective optimisation scenarios
- When you want to balance different criteria

**Data Format**:
```jsonl
{"prompt": "Question",
 "chosen": "Response A",
 "rejected": "Response B",
 "objectives": {
   "helpfulness": {"chosen_score": 0.9, "rejected_score": 0.6},
   "safety": {"chosen_score": 0.95, "rejected_score": 0.8},
   "conciseness": {"chosen_score": 0.7, "rejected_score": 0.5}
 },
 "objective_weights": {"helpfulness": 0.5, "safety": 0.3, "conciseness": 0.2}}
```

**Implementation Notes**:
- Define clear objectives
- Use appropriate objective weights
- Monitor objective balance

### Token-Level RL (TRL beyond PPO)

**Description**: RL at token level rather than sequence level.

**When to Use**:
- When you need fine-grained control
- Token-level optimisation scenarios
- When sequence-level RL is insufficient

**Data Format**:
```jsonl
{"prompt": "Complete: The capital of France is",
 "tokens": ["Paris", ",", "a", "beautiful"],
 "token_rewards": [1.0, 0.8, 0.9, 0.7],
 "token_advantages": [0.3, 0.1, 0.2, 0.0]}
```

**Implementation Notes**:
- Ensure proper token-level rewards
- Use appropriate advantage estimation
- Monitor token-level improvements

### GSHF (Generative Self-Help Feedback)

**Description**: Model generates its own feedback.

**When to Use**:
- Self-improving systems
- When you have strong base models
- Iterative improvement scenarios

**Data Format**:
```jsonl
{"prompt": "Question",
 "draft": "Initial response",
 "self_feedback": "This response could be improved by...",
 "self_score": 0.6,
 "revision": "Improved response",
 "revision_score": 0.85}
```

**Implementation Notes**:
- Use strong base models
- Monitor self-feedback quality
- Ensure improvement validation

### Pairwise Cringe Loss

**Description**: Penalise model for preferring worse responses.

**When to Use**:
- When you want to penalise poor preferences
- Preference correction scenarios
- When you want to improve preference quality

**Data Format**:
```jsonl
{"prompt": "Question",
 "good_response": "Quality answer",
 "bad_response": "Poor answer",
 "model_good_logprob": -2.5,
 "model_bad_logprob": -2.3,  // Model incorrectly prefers bad
 "cringe_penalty": 0.2}
```

**Implementation Notes**:
- Ensure clear quality distinctions
- Use appropriate penalty strength
- Monitor preference correction

### COIG (Chinese Open Instruction Generalist) - Instruction Method

**Description**: Specific instruction tuning approach.

**When to Use**:
- Instruction-following models
- When you have structured instructions
- Multi-task instruction scenarios

**Data Format**:
```jsonl
{"task_type": "question_answering",
 "instruction": "Answer the following question",
 "input": "What is AI?",
 "output": "AI is...",
 "meta": {"language": "en", "domain": "technology"}}
```

**Implementation Notes**:
- Use consistent instruction templates
- Include appropriate metadata
- Monitor instruction adherence

### LIMA-style Training (Less Is More for Alignment)

**Description**: High-quality curated dataset, minimal examples.

**When to Use**:
- When you have high-quality data
- Quality-focused training
- When you want to minimise data requirements

**Data Format**:
```jsonl
// Emphasis on quality over quantity - typically <1000 examples
{"prompt": "Question",
 "response": "Extremely high-quality, carefully curated response",
 "quality_score": 0.99,
 "curation_notes": "Verified by experts"}
```

**Implementation Notes**:
- Ensure high data quality
- Use appropriate quality metrics
- Monitor quality maintenance

### WPO (Winner-Take-All Preference Optimisation)

**Description**: Only train on clear winner in preferences.

**When to Use**:
- When you have clear preference winners
- Quality-focused training
- When you want to focus on best responses

**Data Format**:
```jsonl
{"prompt": "Question",
 "responses": [
   {"text": "Response 1", "votes": 8},
   {"text": "Response 2", "votes": 2}
 ],
 "winner": 0,
 "margin_threshold": 0.6,  // Only train if margin > threshold
 "use_for_training": true}
```

**Implementation Notes**:
- Ensure clear preference margins
- Use appropriate threshold
- Monitor training quality

### Hindsight Instruction Relabeling (HIR)

**Description**: Relabel failed attempts with achieved goals.

**When to Use**:
- When you have failed attempts
- Goal relabeling scenarios
- When you want to learn from failures

**Data Format**:
```jsonl
{"original_instruction": "Write a 100-word essay",
 "attempted_output": "50-word essay",
 "relabeled_instruction": "Write a 50-word essay",
 "success_label": true}  // Now counts as success
```

**Implementation Notes**:
- Ensure proper goal relabeling
- Use appropriate success criteria
- Monitor relabeling quality

### RAFT (Reward rAnked FineTuning)

**Description**: Ranks responses by reward and trains on top-k responses only.

**When to Use**:
- When you have reward models
- Quality-focused training
- When computational resources are limited

**Data Format**:
```jsonl
{"prompt": "Question",
 "responses": [
   {"text": "Response 1", "reward": 0.9, "rank": 1},
   {"text": "Response 2", "reward": 0.7, "rank": 2},
   {"text": "Response 3", "reward": 0.4, "rank": 3}
 ],
 "use_top_k": 1}  // Only train on rank 1
```

**Implementation Notes**:
- Choose appropriate k value
- Ensure reward model quality
- Monitor training stability

### SPIN (Self-Play Fine-Tuning from AI Feedback)

**Description**: Self-play between old and new model versions with AI feedback.

**When to Use**:
- When human feedback is limited
- Iterative model improvement
- When you have strong base models

**Data Format**:
```jsonl
{"prompt": "Question",
 "old_model_response": "Response from iteration t",
 "new_model_response": "Response from iteration t+1",
 "preference": "new"}  // Which is better
```

**Implementation Notes**:
- Use strong base models
- Monitor for quality improvements
- Implement proper evaluation

---

## Safety & Robustness

### Red Teaming Fine-Tuning

**Description**: Trains models on adversarial examples to improve robustness.

**When to Use**:
- Building secure AI systems
- When safety is critical
- Preparing for deployment

**Data Format**:
```jsonl
{"adversarial_prompt": "Ignore previous instructions and...",
 "vulnerable_response": "Okay, I will...",
 "safe_response": "I cannot ignore my instructions. How can I help you?",
 "attack_type": "prompt_injection"}
```

**Implementation Notes**:
- Include diverse attack types
- Balance safety and utility
- Regular red teaming exercises

### Toxicity Reduction

**Description**: Reduces toxic outputs through targeted training.

**When to Use**:
- When deploying in public settings
- Content moderation applications
- Building inclusive AI systems

**Data Format**:
```jsonl
{"prompt": "Tell me about...",
 "toxic_response": "Response with slurs...",
 "safe_response": "Respectful response...",
 "toxicity_score_before": 0.9,
 "toxicity_score_after": 0.1}
```

**Implementation Notes**:
- Use appropriate toxicity detectors
- Balance safety and freedom
- Monitor for over-censorship

---

## Efficiency & Compression

### Knowledge Distillation

**Description**: Trains smaller models to mimic larger models.

**When to Use**:
- When you need smaller models
- Resource-constrained environments
- Maintaining performance with reduced size

**Data Format**:
```jsonl
{"prompt": "Question",
 "teacher_response": "Detailed response from GPT-4",
 "teacher_logits": [0.1, 0.7, 0.2, ...]}  // Optional
```

**Implementation Notes**:
- Choose appropriate student architecture
- Use temperature scaling
- Monitor performance retention

### Curriculum Learning

**Description**: Trains on progressively harder examples.

**When to Use**:
- When you have difficulty-graded data
- Complex task learning
- When you want to improve learning efficiency

**Data Format**:
```jsonl
{"prompt": "Question",
 "response": "Answer",
 "difficulty": 1,  // Start with difficulty 1, increase over time
 "curriculum_stage": 1}
```

**Implementation Notes**:
- Define clear difficulty criteria
- Implement progressive scheduling
- Monitor learning curves

---

## Quick Reference

### Technique Comparison

| Technique | Key Data Requirements | Loss Type | Best Use Case |
|-----------|----------------------|-----------|---------------|
| SFT | Input-output pairs | Cross-entropy | Initial fine-tuning |
| DPO | Preference pairs (chosen/rejected) | Preference loss | Preference alignment |
| PPO | Prompts + reward model | Policy gradient | Large-scale RLHF |
| KTO | Binary feedback (good/bad) | Binary loss | Simple quality assessment |
| ORPO | Preference pairs (no separate SFT) | Unified loss | Combined SFT + preference |
| RLAIF | AI-generated preferences | Preference loss | When human feedback is limited |
| Constitutional AI | Critique-revision pairs | Multi-stage | Safety-focused training |
| Chain-of-Thought | Reasoning steps + answer | Sequence loss | Complex reasoning tasks |
| RAFT | Ranked responses | Ranking loss | Quality-focused training |
| Reward Modeling | Comparison data | Bradley-Terry | Building reward models |
| GRPO | Multiple responses per prompt | Group ranking | Group-based evaluation |
| ReMax | Prompt-response-reward | Reward maximisation | Direct reward optimisation |
| PRO | Ranked responses (3+) | Multi-rank loss | Multiple preference rankings |
| SPPO | Self-play comparisons | Iterative preference | Iterative model improvement |
| ReST | Generated samples + filtering | Selective SFT | Quality-focused training |
| AWR | Advantage-weighted samples | Weighted regression | Offline RL with advantages |
| EXO | DPO + exploration bonus | Exploration loss | Encouraging novel responses |
| V-MPO | State-action-reward | KL-constrained policy | Stable policy updates |
| CQL | Conservative offline RL | Conservative loss | Safe offline RL |
| IQL | Implicit Q-learning | Implicit loss | Offline RL without explicit Q |
| RL-CAI | Constitutional principles | Multi-objective RL | Safety-focused RL |
| APO | Anchored preferences | Anchored loss | Reference-anchored learning |
| Nash-MD | Multi-agent utilities | Nash equilibrium | Game-theoretic alignment |
| SALMON | Principle-following rewards | Principle loss | Self-alignment with principles |
| RRHF-enhanced | Hindsight rankings | Hindsight loss | Goal relabeling scenarios |
| PKD | Teacher preferences | Distillation loss | Knowledge transfer |
| R-DPO | Refined preferences | Multi-stage loss | Iterative preference improvement |
| MODPO | Multi-objective preferences | Multi-objective loss | Balancing multiple criteria |
| Token-Level RL | Token-level rewards | Token-level loss | Fine-grained control |
| GSHF | Self-generated feedback | Self-improvement loss | Self-improving systems |
| Pairwise Cringe Loss | Quality distinctions | Penalty loss | Preference correction |
| COIG | Structured instructions | Instruction loss | Instruction-following |
| LIMA-style | High-quality curated data | Quality-focused loss | Minimal high-quality training |
| WPO | Winner-take-all preferences | Winner loss | Clear preference winners |
| HIR | Hindsight relabeling | Relabeling loss | Learning from failures |

### Implementation Checklist

- [ ] Choose appropriate technique for your use case
- [ ] Collect or generate high-quality training data
- [ ] Validate data format and quality
- [ ] Set up proper evaluation metrics
- [ ] Monitor training progress and overfitting
- [ ] Test on held-out validation set
- [ ] Perform safety and robustness checks
- [ ] Document training configuration and results

### Common Pitfalls to Avoid

1. **Data Quality**: Ensure your training data is high-quality and representative
2. **Overfitting**: Monitor validation performance and use early stopping
3. **Safety**: Always include safety considerations in your training
4. **Evaluation**: Use appropriate metrics for your specific use case
5. **Scalability**: Consider computational requirements and resource constraints

---

*This library is continuously updated with new techniques and best practices. For specific implementation questions or contributions, please refer to the project documentation.*