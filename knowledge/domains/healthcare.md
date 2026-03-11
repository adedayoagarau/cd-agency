---
title: "Domain: Healthcare — Content Design Patterns"
domain: domains
tags: [healthcare, health, medical, patient, accessibility, compliance, hipaa]
industries: [telehealth, patient-portals, health-tracking, mental-health, pharmacy]
---

### Domain Context

Healthcare content design directly impacts people's wellbeing. Misunderstood medication instructions, confusing appointment flows, or anxiety-inducing test results can cause real harm. Content must be precise, empathetic, and accessible to users who may be stressed, in pain, or cognitively impaired.

### Key Challenges

1. **Health literacy is low.** Only 12% of US adults have proficient health literacy (NAAL study). Content must work for everyone.
2. **Users are often anxious.** Reading test results, scheduling surgery, managing chronic conditions — emotional states are heightened.
3. **Compliance is complex.** HIPAA, FDA regulations, and medical accuracy requirements constrain content.
4. **Consequences are high.** A misunderstood dosage instruction or ignored warning can be life-threatening.

### Content Patterns by Feature

**Appointment booking:**
- "Book an appointment with Dr. Sarah Chen — Family Medicine"
- Confirmation: "Your appointment is confirmed. Tuesday, March 15 at 2:30 PM with Dr. Chen at Main Street Clinic."
- Preparation instructions: "Before your visit: Bring your insurance card and a list of current medications."
- Reminder: "Appointment tomorrow at 2:30 PM. Need to reschedule? Call (555) 123-4567 or tap Reschedule."

**Test results:**
- Lead with context, not data: "Your cholesterol levels are in the normal range."
- Then provide specifics: "Total cholesterol: 185 mg/dL (normal: under 200)"
- Always provide next steps: "No action needed. Your next check is recommended in 12 months."
- For concerning results: "Your results are ready. Please contact your doctor's office to discuss next steps." — don't deliver bad news through an app without context.

**Medication information:**
- Dosage: "Take 1 tablet (500mg) by mouth, twice daily, with food"
- Timing: "Morning and evening, approximately 12 hours apart"
- Warnings: "Do not take with alcohol. May cause drowsiness."
- Missed dose: "If you miss a dose, take it as soon as you remember. If it's almost time for your next dose, skip the missed dose."

**Symptom tracking:**
- Simple scales: "How is your pain today? 0 (no pain) to 10 (worst pain)"
- Clear categories, not medical jargon: "Mood" not "Affect assessment"
- Trends: "Your average pain score has decreased from 6 to 4 over the past month"

### Empathy in Healthcare Content

**Tone calibration by context:**
| Context | Tone | Example |
|---------|------|---------|
| Routine appointment | Warm, efficient | "You're all set for Tuesday." |
| Test results (normal) | Reassuring, clear | "Good news — everything looks normal." |
| Test results (abnormal) | Calm, supportive, action-oriented | "Some results need attention. Your care team will contact you within 24 hours." |
| Mental health | Gentle, non-judgmental | "It's okay to not be okay. Here are resources that can help." |
| Emergency guidance | Direct, urgent, specific | "Call 911 immediately. Do not drive yourself." |
| Billing | Transparent, patient | "Your visit cost $150. Insurance covered $120. You owe $30." |

### Health Literacy Guidelines

- **Target 6th-grade reading level** for patient-facing content
- **Avoid medical jargon** or define it immediately: "Hypertension (high blood pressure)"
- **Use numbers carefully:** "Take 2 tablets" not "Take a double dose"
- **Teach-back method in content:** Summarize key info and ask users to confirm understanding
- **Visual aids:** Icons for medication timing, body diagrams for symptoms
- **Action-first structure:** "Take this medication with food" before "This medication may cause stomach upset if taken on an empty stomach"

### Compliance and Privacy

- **HIPAA:** Never show protected health information in notifications or previews. "You have a new message from your care team" not "Your HIV test results are ready."
- **Consent flows:** Explain what data is collected and why, in plain language: "We collect your health data to provide personalized care recommendations. We never sell your data."
- **FDA requirements for drug information:** Follow structured product labeling (SPL) format for accuracy, but layer plain-language summaries on top.

### Accessibility in Healthcare

Healthcare content accessibility is often legally required AND morally critical:
- **Vision impairment:** Ensure prescription labels are available in large print and audio
- **Cognitive impairment:** Use simple language, numbered steps, visual aids
- **Motor impairment:** Ensure all form interactions work without fine motor control
- **Hearing impairment:** Provide text alternatives for all audio (telehealth calls, instructional videos)
- **Language barriers:** Prioritize translation for top patient-facing content

### Case Studies

**MyChart (Epic):** The dominant patient portal. Lesson: clinical data needs a "translation layer" — raw lab values with normal ranges AND plain-language interpretation.

**Headspace:** Mental health content that avoids clinical language. "Take a deep breath" not "Practice diaphragmatic breathing." Lesson: approachability drives engagement in health apps.

**One Medical:** Telehealth with human-centered content. Appointment booking in 3 taps, clear visit summaries in plain language. Lesson: healthcare UX can be as simple as consumer apps without sacrificing accuracy.

**Zocdoc:** Doctor search with patient reviews. Content design challenge: presenting reviews responsibly. Lesson: user-generated health content needs careful framing and moderation.
