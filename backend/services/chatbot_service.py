import os
import groq
from backend.config import Config

class ChatbotService:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            api_key = os.environ.get("GROQ_API_KEY")
            if api_key:
                cls._client = groq.Groq(api_key=api_key)
        return cls._client

    @classmethod
    def generate_response(cls, portal_type: str, current_tab: str, chat_history: list, user_message: str, user_name: str = None, db_context: str = "") -> str:
        client = cls.get_client()
        if not client:
            return "AI Chatbot Assistant is offline. Please configure your GROQ_API_KEY in the .env file."

        # 1. Select prompt based on portal type
        if portal_type == "organization":
            system_prompt = (
                "You are 'WorkForceX Recruiter Assistant', a professional, helpful, and friendly AI staffing specialist. "
                "You help recruiters/HR managers configure staffing projects, understand AI candidate match scores, send invites, and manage hires.\n\n"
                "Real-Time Database Context:\n"
                f"{db_context}\n\n"
                "Current Page/Module Context:\n"
                f"- Active Recruiter Portal Tab: {current_tab or 'Overview'}\n"
                f"- User (Recruiter Name): {user_name or 'Recruiter'}\n\n"
                "Instructions:\n"
                "1. Keep responses clear, concise, and focused on recruitment tasks. Absolutely limit responses to 4 to 5 lines of content maximum.\n"
                "2. Provide step-by-step guidance on how to navigate the current tab or manage candidate lists using the real-time database context provided.\n"
                "3. Do not hallucinate or guess details. If you are unsure of the answer or if the database lacks details, tell the recruiter to contact support at support@workforcex.com."
            )
        else:
            system_prompt = (
                "You are 'WorkForceX Career Coach', a friendly, encouraging, and supportive career assistant. "
                "You help candidates optimize their resumes, pass assessment MCQ tests, accept project invitations, and complete profiles.\n\n"
                "Real-Time Database Context:\n"
                f"{db_context}\n\n"
                "Current Page/Module Context:\n"
                f"- Active Professional Workspace Tab: {current_tab or 'My Profile'}\n"
                f"- User (Candidate Name): {user_name or 'Professional'}\n\n"
                "Instructions:\n"
                "1. Keep responses highly encouraging, professional, and career-oriented. Absolutely limit responses to 4 to 5 lines of content maximum.\n"
                "2. Help the candidate learn how to pass assessments (passing score is 70%, max 3 attempts) or edit their profile info using the real-time database context provided.\n"
                "3. Avoid recruiter-specific jargon. If unsure, suggest emailing candidate support at support@workforcex.com."
            )

        # 2. Build Groq chat messages payload
        messages = [{"role": "system", "content": system_prompt}]

        # Inject conversation history (max 8 messages to stay lightweight and within context)
        for msg in chat_history[-8:]:
            messages.append({
                "role": "user" if msg.get("role") == "user" else "assistant",
                "content": msg.get("content", "")
            })

        # Append new user message
        messages.append({"role": "user", "content": user_message})

        try:
            chat_completion = client.chat.completions.create(
                messages=messages,
                model="llama-3.1-8b-instant",
                temperature=0.2,  # Low temperature for highly deterministic/factual responses
                max_tokens=500
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            return "I'm having trouble connecting to the AI brain right now. Please try again or contact support at support@workforcex.com."
