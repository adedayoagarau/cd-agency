"""Brand voice consistency checker using LLM scoring."""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class VoiceProfile:
    """A brand voice configuration."""

    name: str
    tone_descriptors: list[str]
    do_list: list[str]
    dont_list: list[str]
    sample_content: list[str] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, filepath: str | Path) -> "VoiceProfile":
        """Load a voice profile from a YAML file."""
        path = Path(filepath)
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(
            name=data.get("name", path.stem),
            tone_descriptors=data.get("tone_descriptors", []),
            do_list=data.get("do", []),
            dont_list=data.get("dont", []),
            sample_content=data.get("sample_content", []),
        )

    @classmethod
    def from_dict(cls, data: dict) -> "VoiceProfile":
        """Create a voice profile from a dictionary."""
        return cls(
            name=data.get("name", "custom"),
            tone_descriptors=data.get("tone_descriptors", []),
            do_list=data.get("do", []),
            dont_list=data.get("dont", []),
            sample_content=data.get("sample_content", []),
        )

    def to_prompt(self) -> str:
        """Convert voice profile to a prompt description."""
        parts = [f"Brand voice: {self.name}"]
        if self.tone_descriptors:
            parts.append(f"Tone: {', '.join(self.tone_descriptors)}")
        if self.do_list:
            parts.append("Do: " + "; ".join(self.do_list))
        if self.dont_list:
            parts.append("Don't: " + "; ".join(self.dont_list))
        if self.sample_content:
            parts.append("Example content that matches this voice:")
            for sample in self.sample_content[:3]:
                parts.append(f"  - \"{sample}\"")
        return "\n".join(parts)


@dataclass
class VoiceDeviation:
    """A specific phrase that deviates from brand voice."""

    phrase: str
    reason: str
    suggestion: str


@dataclass
class VoiceResult:
    """Result of voice consistency check."""

    score: float  # 1-10
    summary: str
    deviations: list[VoiceDeviation] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        if self.score >= 9:
            return "Excellent"
        elif self.score >= 7:
            return "Good"
        elif self.score >= 5:
            return "Needs Work"
        elif self.score >= 3:
            return "Poor"
        else:
            return "Off-Brand"

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "label": self.label,
            "summary": self.summary,
            "deviations": [
                {"phrase": d.phrase, "reason": d.reason, "suggestion": d.suggestion}
                for d in self.deviations
            ],
            "strengths": self.strengths,
        }


class VoiceChecker:
    """Checks content against a brand voice profile using LLM."""

    def __init__(self, client=None, model: str = "claude-sonnet-4-20250514"):
        """Initialize with an Anthropic client.

        Args:
            client: An anthropic.Anthropic client instance. If None, creates one.
            model: Model to use for voice checking.
        """
        self._client = client
        self._model = model

    @property
    def client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic()
        return self._client

    def check(self, text: str, profile: VoiceProfile) -> VoiceResult:
        """Check text against a voice profile using LLM.

        Args:
            text: The content to check.
            profile: The brand voice profile to check against.

        Returns:
            VoiceResult with score, deviations, and suggestions.
        """
        system_prompt = (
            "You are a brand voice consistency evaluator. "
            "Score content against a brand voice guide on a 1-10 scale. "
            "Return your analysis as JSON with this exact structure:\n"
            '{"score": <number 1-10>, "summary": "<1-2 sentence summary>", '
            '"deviations": [{"phrase": "<exact phrase>", "reason": "<why it deviates>", '
            '"suggestion": "<replacement>"}], '
            '"strengths": ["<what matches the voice well>"]}'
        )

        user_message = (
            f"## Brand Voice Guide\n{profile.to_prompt()}\n\n"
            f"## Content to Evaluate\n{text}\n\n"
            "Score this content against the brand voice guide. "
            "Identify specific phrases that deviate and suggest replacements. "
            "Return JSON only, no other text."
        )

        response = self.client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        return self._parse_response(response.content[0].text)

    def _parse_response(self, response_text: str) -> VoiceResult:
        """Parse LLM response into VoiceResult."""
        # Try to extract JSON from the response
        text = response_text.strip()

        # Handle markdown code blocks
        if "```" in text:
            match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
            if match:
                text = match.group(1).strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return VoiceResult(
                score=5.0,
                summary="Could not parse voice check response",
                deviations=[],
                strengths=[],
            )

        deviations = [
            VoiceDeviation(
                phrase=d.get("phrase", ""),
                reason=d.get("reason", ""),
                suggestion=d.get("suggestion", ""),
            )
            for d in data.get("deviations", [])
        ]

        return VoiceResult(
            score=float(data.get("score", 5)),
            summary=data.get("summary", ""),
            deviations=deviations,
            strengths=data.get("strengths", []),
        )

    def check_without_llm(self, text: str, profile: VoiceProfile) -> VoiceResult:
        """Basic voice check using rule-based heuristics (no LLM needed).

        Checks do/don't lists against the text. Less accurate but free and fast.
        """
        text_lower = text.lower()
        deviations = []
        strengths = []
        score = 10.0

        # Check "don't" violations
        for dont in profile.dont_list:
            # Extract key phrases from the don't rule
            dont_lower = dont.lower()
            # Simple substring check for key terms
            key_words = [w for w in dont_lower.split() if len(w) > 3]
            for word in key_words:
                if word in text_lower and word not in {"that", "this", "with", "from", "your", "they", "have", "been", "will", "when"}:
                    deviations.append(VoiceDeviation(
                        phrase=word,
                        reason=f"Violates voice rule: Don't {dont}",
                        suggestion=f"Rewrite to avoid: {dont}",
                    ))
                    score -= 1.0
                    break

        # Check "do" matches
        for do_rule in profile.do_list:
            do_lower = do_rule.lower()
            key_words = [w for w in do_lower.split() if len(w) > 3]
            for word in key_words:
                if word in text_lower:
                    strengths.append(f"Matches voice rule: {do_rule}")
                    break

        score = max(1.0, min(10.0, score))
        passed = len(deviations)
        total = len(profile.dont_list) + len(profile.do_list)

        summary = f"Checked against {total} voice rules. Found {len(deviations)} deviation(s) and {len(strengths)} strength(s)."

        return VoiceResult(
            score=round(score, 1),
            summary=summary,
            deviations=deviations,
            strengths=strengths,
        )
