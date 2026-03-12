# All 16 Agents

> Stability: Stable

CD Agency ships with 16 specialized content design agents.

## Agent Catalog

### Beginner

| Agent | Slug | Description |
| --- | --- | --- |
| Content Designer Generalist | `content-designer-generalist` | All-around expert in UX writing, microcopy, and content strategy |
| Empty State & Placeholder Specialist | `empty-state-placeholder-specialist` | Designs engaging empty states, loading messages, and helpful placeholders |

### Intermediate

| Agent | Slug | Description |
| --- | --- | --- |
| Accessibility Content Auditor | `accessibility-content-auditor` | Ensures content meets WCAG standards for diverse user needs |
| CTA Optimization Specialist | `cta-optimization-specialist` | Crafts high-converting calls-to-action |
| Error Message Architect | `error-message-architect` | Designs human-centered error messages with resolution guidance |
| Microcopy Review Agent | `microcopy-review-agent` | Finesses microcopy for clarity, conciseness, and conversion |
| Mobile UX Writer | `mobile-ux-writer` | Creates microcopy optimized for mobile interfaces |
| Notification Content Designer | `notification-content-designer` | Crafts action-oriented notifications across channels |
| Onboarding Flow Designer | `onboarding-flow-designer` | Guides users to their first success moment |
| Search Experience Writer | `search-experience-writer` | Optimizes search interfaces — from input hints to no-results messages |
| Tone Evaluation Agent | `tone-evaluation-agent` | Assesses and refines emotional register and content feel |

### Advanced

| Agent | Slug | Description |
| --- | --- | --- |
| Conversational AI Designer | `conversational-ai-designer` | Dialogue for chatbots, voice assistants, and conversational interfaces |
| Information Architect | `information-architect` | Extracts entities, maps relationships, and recommends structural patterns for content systems |
| Localization Content Strategist | `localization-content-strategist` | Adapts content for global audiences with cultural relevance |
| Privacy & Legal Content Simplifier | `privacy-legal-content-simplifier` | Translates legal jargon into user-friendly language |
| Technical Documentation Writer | `technical-documentation-writer` | Clear, accurate technical content for developers |

---

## Agent Details

### Content Designer Generalist

- **Slug:** `content-designer-generalist`
- **Aliases:** `generalist`, `general`
- **Difficulty:** beginner
- **Tags:** `ux-writing`, `microcopy`, `content-strategy`, `brand-voice`, `general`
- **Required Input:** `content_or_context` — The content to review or the context for new content
- **Optional Inputs:** `brand_guidelines`, `target_audience`, `channel`, `constraints`

### Error Message Architect

- **Slug:** `error-message-architect`
- **Aliases:** `error`, `errors`
- **Difficulty:** intermediate
- **Tags:** `errors`, `error-messages`, `recovery`, `troubleshooting`, `validation`
- **Required Input:** `error_scenario` — The error condition
- **Optional Inputs:** `technical_details`, `severity`, `target_audience`, `brand_guidelines`
- **Outputs:** `user_message`, `resolution_steps`, `developer_note`, `prevention_tip`

### CTA Optimization Specialist

- **Slug:** `cta-optimization-specialist`
- **Aliases:** `cta`
- **Difficulty:** intermediate
- **Tags:** `cta`, `conversion`, `buttons`, `persuasion`, `a-b-testing`, `landing-pages`
- **Required Input:** `cta_context` — What the CTA should accomplish
- **Optional Inputs:** `current_cta`, `target_action`, `audience`, `brand_guidelines`

### Accessibility Content Auditor

- **Slug:** `accessibility-content-auditor`
- **Aliases:** `a11y`, `accessibility`, `wcag`
- **Difficulty:** intermediate
- **Tags:** `accessibility`, `a11y`, `wcag`, `inclusive-language`, `plain-language`, `screen-reader`

### Microcopy Review Agent

- **Slug:** `microcopy-review-agent`
- **Aliases:** `microcopy`
- **Difficulty:** intermediate
- **Tags:** `microcopy`, `buttons`, `tooltips`, `forms`, `labels`, `review`, `refinement`

### Tone Evaluation Agent

- **Slug:** `tone-evaluation-agent`
- **Aliases:** `tone`, `voice`
- **Difficulty:** intermediate
- **Tags:** `tone`, `voice`, `brand`, `emotion`, `style`, `consistency`

### Mobile UX Writer

- **Slug:** `mobile-ux-writer`
- **Aliases:** `mobile`
- **Difficulty:** intermediate
- **Tags:** `mobile`, `app`, `push-notifications`, `ios`, `android`, `responsive`, `touch`

### Notification Content Designer

- **Slug:** `notification-content-designer`
- **Aliases:** `notifications`, `notify`, `push`
- **Difficulty:** intermediate
- **Tags:** `notifications`, `push`, `email`, `in-app`, `alerts`, `engagement`

### Onboarding Flow Designer

- **Slug:** `onboarding-flow-designer`
- **Aliases:** `onboarding`
- **Difficulty:** intermediate
- **Tags:** `onboarding`, `activation`, `retention`, `welcome`, `first-run`, `progressive-disclosure`

### Search Experience Writer

- **Slug:** `search-experience-writer`
- **Aliases:** `search`
- **Difficulty:** intermediate
- **Tags:** `search`, `filters`, `no-results`, `autocomplete`, `discoverability`, `facets`

### Empty State & Placeholder Specialist

- **Slug:** `empty-state-placeholder-specialist`
- **Aliases:** `empty`, `placeholder`
- **Difficulty:** beginner
- **Tags:** `empty-state`, `placeholder`, `loading`, `first-run`, `zero-state`, `onboarding`

### Conversational AI Designer

- **Slug:** `conversational-ai-designer`
- **Aliases:** `chatbot`, `conversation`
- **Difficulty:** advanced
- **Tags:** `chatbot`, `voice-ui`, `dialogue`, `conversation`, `ivr`, `persona`

### Localization Content Strategist

- **Slug:** `localization-content-strategist`
- **Aliases:** `l10n`, `localization`, `i18n`
- **Difficulty:** advanced
- **Tags:** `localization`, `l10n`, `i18n`, `translation`, `globalization`, `cultural-adaptation`

### Privacy & Legal Content Simplifier

- **Slug:** `privacy-legal-content-simplifier`
- **Aliases:** `privacy`, `legal`
- **Difficulty:** advanced
- **Tags:** `privacy`, `legal`, `gdpr`, `consent`, `terms-of-service`, `plain-language`, `compliance`

### Information Architect

- **Slug:** `information-architect`
- **Aliases:** `ia`, `architecture`
- **Difficulty:** advanced
- **Tags:** `information-architecture`, `content-structure`, `entities`, `taxonomy`, `relationships`, `content-systems`
- **Required Input:** `content_or_context` — The content to analyze (a page, flow, feature description, or set of UI strings)
- **Optional Inputs:** `scope`, `existing_taxonomy`, `target_audience`, `platform`
- **Outputs:** `entities`, `relationships`, `content_model`, `naming_recommendations`, `structural_patterns`, `consistency_flags`

### Technical Documentation Writer

- **Slug:** `technical-documentation-writer`
- **Aliases:** `docs`, `tech-docs`
- **Difficulty:** advanced
- **Tags:** `documentation`, `api-docs`, `sdk`, `developer`, `technical-writing`, `code-examples`
