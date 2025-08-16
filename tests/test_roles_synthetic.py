"""
Synthetic tests for roles.py without external dependencies.
"""

from src.roles import economist_prompt, lawyer_prompt, sociologist_prompt, synthesizer_prompt


class TestEconomistPrompt:
    """Test economist role prompt."""

    def test_economist_prompt_returns_string(self):
        """Test that economist_prompt returns a string."""
        prompt = economist_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_economist_prompt_content(self):
        """Test economist prompt contains expected keywords."""
        prompt = economist_prompt()

        # Check for role definition
        assert "Role: Economist" in prompt

        # Check for economic concepts
        assert "market size" in prompt
        assert "TAM/SAM/SOM" in prompt
        assert "unit economics" in prompt
        assert "pricing power" in prompt
        assert "supply/demand" in prompt
        assert "funding options" in prompt
        assert "ROI" in prompt
        assert "risks" in prompt

        # Check for formatting requirements
        assert "specific numbers" in prompt
        assert "calculations" in prompt
        assert "$1.2M" in prompt  # Example format
        assert "15% ROI" in prompt  # Example format
        assert "3-year payback" in prompt  # Example format

        # Check for analysis requirements
        assert "financial projections" in prompt
        assert "break-even analysis" in prompt
        assert "concise" in prompt
        assert "quantify" in prompt

    def test_economist_prompt_consistency(self):
        """Test that economist prompt is consistent across calls."""
        prompt1 = economist_prompt()
        prompt2 = economist_prompt()
        assert prompt1 == prompt2


class TestLawyerPrompt:
    """Test lawyer role prompt."""

    def test_lawyer_prompt_returns_string(self):
        """Test that lawyer_prompt returns a string."""
        prompt = lawyer_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_lawyer_prompt_content(self):
        """Test lawyer prompt contains expected keywords."""
        prompt = lawyer_prompt()

        # Check for role definition
        assert "Role: Business-Law Expert" in prompt

        # Check for legal concepts
        assert "regulatory obligations" in prompt
        assert "licensing" in prompt
        assert "privacy/data-protection" in prompt
        assert "consumer" in prompt
        assert "employment law" in prompt
        assert "IP" in prompt
        assert "copyright" in prompt
        assert "patents" in prompt
        assert "trademarks" in prompt
        assert "contractual risks" in prompt
        assert "liabilities" in prompt

        # Check for requirements
        assert "specific" in prompt
        assert "legal requirements" in prompt
        assert "cite relevant regulations" in prompt
        assert "actionable compliance steps" in prompt
        assert "jurisdiction-sensitive" in prompt
        assert "legal structures" in prompt

    def test_lawyer_prompt_consistency(self):
        """Test that lawyer prompt is consistent across calls."""
        prompt1 = lawyer_prompt()
        prompt2 = lawyer_prompt()
        assert prompt1 == prompt2


class TestSociologistPrompt:
    """Test sociologist role prompt."""

    def test_sociologist_prompt_returns_string(self):
        """Test that sociologist_prompt returns a string."""
        prompt = sociologist_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_sociologist_prompt_content(self):
        """Test sociologist prompt contains expected keywords."""
        prompt = sociologist_prompt()

        # Check for role definition
        assert "Role: Sociologist" in prompt

        # Check for sociological concepts
        assert "cultural fit" in prompt
        assert "adoption behavior" in prompt
        assert "incentives" in prompt
        assert "fairness/equity" in prompt
        assert "externalities" in prompt
        assert "ethical concerns" in prompt

        # Check for analysis requirements
        assert "user segments" in prompt
        assert "pain points" in prompt
        assert "network effects" in prompt
        assert "behavioral economics" in prompt
        assert "social proof" in prompt
        assert "resistance points" in prompt
        assert "adoption accelerators" in prompt
        assert "different user segments" in prompt
        assert "contexts" in prompt

    def test_sociologist_prompt_consistency(self):
        """Test that sociologist prompt is consistent across calls."""
        prompt1 = sociologist_prompt()
        prompt2 = sociologist_prompt()
        assert prompt1 == prompt2


class TestSynthesizerPrompt:
    """Test synthesizer role prompt."""

    def test_synthesizer_prompt_returns_string(self):
        """Test that synthesizer_prompt returns a string."""
        prompt = synthesizer_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_synthesizer_prompt_content(self):
        """Test synthesizer prompt contains expected keywords."""
        prompt = synthesizer_prompt()

        # Check for role definition
        assert "Role: Business Consultant" in prompt

        # Check for instructions
        assert "FULL conversation" in prompt
        assert "ONE comprehensive report" in prompt
        assert "OUTPUT FORMAT" in prompt
        assert "valid JSON object" in prompt

        # Check for JSON structure
        assert '"executive_summary"' in prompt
        assert '"economic_viability"' in prompt
        assert '"legal_risks"' in prompt
        assert '"social_impact"' in prompt
        assert '"next_steps"' in prompt

        # Check for field requirements
        assert "<=200 words" in prompt
        assert "specific numbers and projections" in prompt
        assert "compliance checklist" in prompt
        assert "specific regulations" in prompt
        assert "adoption analysis" in prompt
        assert "user segments" in prompt

        # Check for formatting requirements
        assert "precise and structured" in prompt
        assert "specific metrics" in prompt
        assert "timelines" in prompt
        assert "priorities" in prompt
        assert "No markdown formatting" in prompt
        assert "only valid JSON" in prompt

    def test_synthesizer_prompt_json_structure(self):
        """Test that synthesizer prompt describes valid JSON structure."""
        prompt = synthesizer_prompt()

        # Extract the JSON example from the prompt
        start_idx = prompt.find("{")
        end_idx = prompt.find("}", start_idx) + 1
        json_example = prompt[start_idx:end_idx]

        # The example should be parseable (though with placeholder values)
        assert "{" in json_example
        assert "}" in json_example
        assert "executive_summary" in json_example
        assert "economic_viability" in json_example
        assert "legal_risks" in json_example
        assert "social_impact" in json_example
        assert "next_steps" in json_example

    def test_synthesizer_prompt_consistency(self):
        """Test that synthesizer prompt is consistent across calls."""
        prompt1 = synthesizer_prompt()
        prompt2 = synthesizer_prompt()
        assert prompt1 == prompt2


class TestAllPrompts:
    """Test all prompts together."""

    def test_all_prompts_unique(self):
        """Test that each role has a unique prompt."""
        prompts = [economist_prompt(), lawyer_prompt(), sociologist_prompt(), synthesizer_prompt()]

        # All prompts should be unique
        assert len(prompts) == len(set(prompts))

    def test_all_prompts_have_role(self):
        """Test that all prompts define a role."""
        prompts = {
            "economist": economist_prompt(),
            "lawyer": lawyer_prompt(),
            "sociologist": sociologist_prompt(),
            "synthesizer": synthesizer_prompt(),
        }

        for name, prompt in prompts.items():
            assert "Role:" in prompt

    def test_all_prompts_have_important_section(self):
        """Test that specialist prompts have IMPORTANT sections."""
        specialist_prompts = [economist_prompt(), lawyer_prompt(), sociologist_prompt()]

        for prompt in specialist_prompts:
            assert "IMPORTANT:" in prompt

    def test_prompt_lengths_reasonable(self):
        """Test that prompts are reasonable lengths."""
        prompts = {
            "economist": economist_prompt(),
            "lawyer": lawyer_prompt(),
            "sociologist": sociologist_prompt(),
            "synthesizer": synthesizer_prompt(),
        }

        for name, prompt in prompts.items():
            # Prompts should be substantial but not too long
            assert 100 < len(prompt) < 1000, f"{name} prompt length is {len(prompt)}"
