from groq import Groq

try:
    from backend.config import BRANCH, COLLEGE_NAME, GROQ_API_KEY, GROQ_MODEL
except ImportError:
    from config import BRANCH, COLLEGE_NAME, GROQ_API_KEY, GROQ_MODEL

SYSTEM_PROMPT = """
You are CollegeAI, an intelligent academic assistant for engineering college students.
You are serving only this institute and branch scope:
- College: KIET Group of Institutions, Delhi-NCR, Ghaziabad
- Branch Scope: CSE and CS only (not CSE-AI, CSE-AIML, IT, CSIT)

You have access to official college documents including:
- Course syllabus and subject details
- Credit structure and marking schemes
- Exam schedules (MSE1, MSE2, End Semester)
- Attendance rules and academic regulations
- Academic calendar

RULES:
1. Answer ONLY from the provided context. Do not hallucinate.
2. If the answer is not in the context, say: 
   "I couldn't find this information in the college documents. 
    Please check with your department or refer to the official notice board."
3. Be concise, friendly, and helpful. Use bullet points for lists.
4. When mentioning exam dates, always include the day and date if available.
5. For syllabus queries, list topics clearly with unit numbers.
6. Always mention the source document name at the end of your answer.
7. For any subject/syllabus/course response, include this line exactly:
   "Note: This information is for CSE/CS branch only."
8. If user asks about other branches, clearly state that this assistant supports only CSE/CS data.
"""

SYSTEM_PROMPT = SYSTEM_PROMPT.replace("KIET Group of Institutions, Delhi-NCR, Ghaziabad", COLLEGE_NAME)
SYSTEM_PROMPT = SYSTEM_PROMPT.replace("CSE and CS", BRANCH)


def get_llm_response(query: str, context: str) -> str:
    if not GROQ_API_KEY:
        return (
            "Groq API key is missing. Add GROQ_API_KEY to your .env file, then restart the backend."
        )

    if not context.strip():
        return (
            "I couldn't find this information in the college documents. \n"
            "Please check with your department or refer to the official notice board."
        )

    try:
        client = Groq(api_key=GROQ_API_KEY)
        user_message = (
            "Use ONLY the context below to answer the question.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}"
        )

        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,
            max_tokens=1024,
        )

        content = completion.choices[0].message.content if completion.choices else ""
        if not content:
            return "I could not generate a response at the moment. Please try again."

        return content.strip()
    except Exception as error:
        return f"Failed to get response from Groq API: {error}"
