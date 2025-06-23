# Future Roadmap

This document outlines planned features, what worked well, blockers encountered, and recommendations for future development.

---

## 1. Planned Features
- **Reminders & Follow-ups:** Let users set reminders or follow-up tasks on emails
- **Calendar Sync:** Integrate with Google Calendar for smart scheduling
- **Smart Reply/Compose:** Suggest AI-generated replies or compose drafts
- **Bulk Actions:** Archive, delete, or categorize multiple emails at once
- **Advanced Analytics:** Show stats on email categories, response times, etc.
- **User Settings:** Customizable categories, notification preferences
- **Mobile App:** React Native or PWA for mobile access
- **WebSocket Updates:** Real-time inbox updates without polling

---

## 2. What Worked Well
- **Gmail OAuth Integration:** Reliable, secure, and user-friendly
- **AI Summarization:** Gemini API produced concise, useful summaries
- **MongoDB Storage:** Flexible schema, easy to extend
- **Clerk Authentication:** Simple, secure, and easy to integrate
- **Pub/Sub Webhooks:** Real-time email ingestion worked well in both dev and prod

---

## 3. Blockers & Pain Points
- **Gmail Restricted Scope Policy:**
  - Using sensitive/restricted scopes (modify/send) requires Google verification
  - Verification process is slow and requires privacy policy, demo video, and justification
  - For most dev/testing, use only non-sensitive scopes if possible
- **AI API Limits:**
  - Gemini API has rate limits and occasional downtime
  - Consider adding retry/backoff logic or a fallback to OpenAI
- **Windows Build Issues:**
  - pydantic-core and other Rust/C++ dependencies require extra setup (Rust, C++ Build Tools)
- **Frontend OAuth State:**
  - State validation is critical; bugs here can break the flow

---

## 4. Recommendations for Restarting
- **Review All Docs:** Start with `README.md` and `architecture.md` for a refresher
- **Check Google Cloud Console:** Ensure APIs, OAuth, and Pub/Sub are still enabled
- **Update Dependencies:** Run `pip install -r requirements.txt` and `npm install` to update
- **Test OAuth Flow:** Use ngrok for local webhook testing
- **Start with Non-sensitive Scopes:** Add sensitive scopes only if needed
- **Add More Tests:** Especially for OAuth, webhook, and AI fallback logic
- **Consider WebSocket Upgrade:** For real-time updates
- **Document Any New Features:** Update the docs folder as you go

---

## 5. Lessons Learned
- OAuth and webhook flows are complex—document every step
- Google API policies can change; always check current requirements
- AI summarization is powerful but not perfect—always have a fallback
- Good logging and error handling save hours of debugging

---

## 6. Next Steps
- Prioritize features based on user feedback
- Consider open-sourcing or inviting collaborators
- Monitor Google API and AI provider changes
- Keep documentation up to date for future you (or new devs) 