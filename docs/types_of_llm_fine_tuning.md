# Types of LLM Fine-Tuning

This document provides an overview of the various methods used to fine-tune Large Language Models (LLMs), categorised into supervised learning and reinforcement learning approaches.

---

## Supervised Fine-Tuning Methods

### Supervised Fine-Tuning (SFT)

**Description:** The standard approach to fine-tuning where the model is trained on labelled examples using supervised learning.

**Key Characteristics:**
- Updates all model parameters during training
- Requires high-quality labelled datasets
- Computationally expensive for large models
- Effective for adapting models to specific tasks or domains

### Instruction Tuning

**Description:** A specialised form of fine-tuning that trains models on instruction-response pairs to improve their ability to follow natural language instructions.

**Key Characteristics:**
- Uses datasets formatted as instruction-output pairs
- Teaches the model to understand and execute diverse instructions
- Improves zero-shot and few-shot performance on new tasks
- Essential for creating general-purpose assistant models

### Parameter-Efficient Fine-Tuning (PEFT)

**Description:** A family of techniques that fine-tune only a small subset of parameters, making the process more efficient and accessible.

**Methods:**

- **LoRA (Low-Rank Adaptation)**
  - Trains small rank decomposition matrices instead of full weight matrices
  - Significantly reduces trainable parameters (often by 10,000x)
  - Maintains performance comparable to full fine-tuning
  - Enables efficient model switching by swapping adapter weights

- **QLoRA (Quantised LoRA)**
  - Combines LoRA with model quantisation (typically 4-bit)
  - Further reduces memory requirements
  - Enables fine-tuning of large models on consumer hardware
  - Minimal performance degradation compared to full-precision LoRA

- **Prefix Tuning**
  - Trains soft prompts that are prepended to model inputs
  - Keeps the original model frozen
  - Learns task-specific continuous vectors
  - Efficient for multi-task scenarios

- **P-Tuning**
  - Optimises continuous prompt embeddings
  - Can be applied to various positions in the input
  - More flexible than discrete prompt engineering
  - Effective for smaller models

- **Adapter Layers**
  - Inserts small trainable modules between frozen transformer layers
  - Typically consists of down-projection and up-projection layers
  - Allows task-specific adaptation with minimal parameters
  - Easy to add, remove, or swap for different tasks

- **IA³ (Infused Adapter by Inhibiting and Amplifying Inner Activations)**
  - Learns vectors that scale activations in the model
  - Even more parameter-efficient than LoRA
  - Modifies key, value, and feed-forward activations
  - Minimal overhead during inference

### Continued Pre-training

**Description:** Extends the pre-training phase on domain-specific or task-specific data before fine-tuning.

**Key Characteristics:**
- Adapts the model's general knowledge to a specific domain
- Uses large amounts of unlabelled domain data
- Bridges the gap between general pre-training and task-specific fine-tuning
- Particularly useful for specialised domains (medical, legal, scientific, etc.)

---

## Reinforcement Learning Methods

### RLHF (Reinforcement Learning from Human Feedback)

**Description:** The foundational approach that uses reinforcement learning to align model outputs with human preferences.

**Key Characteristics:**
- Trains a reward model on human preference data
- Uses PPO to optimise the language model against the reward model
- Requires significant human annotation effort
- Highly effective for improving helpfulness, harmlessness, and honesty

### PPO (Proximal Policy Optimization)

**Description:** A policy gradient reinforcement learning algorithm commonly used in RLHF.

**Key Characteristics:**
- Uses clipped objectives to prevent large policy updates
- More stable than vanilla policy gradient methods
- Balances exploration and exploitation
- Industry standard for RLHF implementations

### DPO (Direct Preference Optimization)

**Description:** A simplified alternative to RLHF that directly optimises on preference data without training a separate reward model.

**Key Characteristics:**
- Bypasses the reward modelling step
- Optimises directly on pairwise preference data
- More stable and easier to implement than RLHF
- Requires less computational resources
- Increasingly popular for alignment tasks

### RLAIF (Reinforcement Learning from AI Feedback)

**Description:** Replaces human feedback with AI-generated feedback, typically from a stronger model.

**Key Characteristics:**
- Uses AI systems to generate preference labels
- More scalable than human feedback
- Can leverage stronger models to improve weaker ones
- Reduces annotation costs significantly
- Quality depends on the capability of the feedback-generating model

### KTO (Kahneman-Tversky Optimization)

**Description:** A preference optimisation method inspired by prospect theory that uses binary feedback instead of pairwise comparisons.

**Key Characteristics:**
- Requires only binary labels (good/bad) rather than preference pairs
- More efficient data collection
- Based on psychological principles of human decision-making
- Suitable when pairwise comparisons are difficult to obtain

### IPO (Identity Preference Optimization)

**Description:** A regularised variant of DPO that addresses some of its theoretical limitations.

**Key Characteristics:**
- Adds regularisation to the DPO objective
- More theoretically grounded than standard DPO
- Prevents overfitting to preference data
- Maintains better calibration of model outputs

### ORPO (Odds Ratio Preference Optimization)

**Description:** An efficient method that combines supervised fine-tuning and preference learning in a single training step.

**Key Characteristics:**
- Eliminates the need for separate SFT and preference optimisation stages
- Uses odds ratio-based loss function
- More computationally efficient than multi-stage approaches
- Achieves competitive performance with fewer training steps

### SimPO (Simple Preference Optimization)

**Description:** A simplified version of DPO that removes the need for a reference model during training.

**Key Characteristics:**
- Eliminates reference model requirement
- Reduces memory footprint during training
- Faster training iterations
- Maintains performance comparable to DPO
- Easier to implement and debug

### Reward Modeling

**Description:** The process of training a model to predict human preferences, typically used as a component in RLHF.

**Key Characteristics:**
- Trained on human preference comparisons
- Outputs scalar reward scores for model outputs
- Acts as a proxy for human judgement
- Critical component in traditional RLHF pipelines
- Can be used for filtering and ranking model outputs

### Constitutional AI

**Description:** An approach that uses AI self-critique and revision based on a set of principles (a "constitution") to improve model behaviour.

**Key Characteristics:**
- Model critiques its own outputs against defined principles
- Iteratively revises responses to better align with values
- Reduces reliance on human feedback
- Promotes transparency through explicit principles
- Combines self-improvement with preference learning
- Developed by Anthropic for alignment research

---

## Choosing a Fine-Tuning Method

The choice of fine-tuning method depends on several factors:

- **Available resources:** PEFT methods are ideal for limited compute/memory
- **Data availability:** DPO and variants require preference data; SFT needs labelled examples
- **Task requirements:** Instruction tuning for general assistants; domain-specific continued pre-training for specialised applications
- **Alignment needs:** RL methods for aligning with human values and preferences
- **Implementation complexity:** SimPO and DPO are simpler than full RLHF pipelines