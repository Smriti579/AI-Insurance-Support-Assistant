import faiss
import gradio as gr
import numpy as np
from groq import Groq
from sentence_transformers import SentenceTransformer
import os

# -----------------------------
# Groq Client
# -----------------------------
client = Groq(api_key=os.environ["GROQ_API_KEY"])

# -----------------------------
# Knowledge Base
# -----------------------------
knowledge_base = [
"Customers can check policy status using their policy number on the insurance portal.",
"Insurance claims require identity proof and the original policy document.",
"Hospital bills and discharge summary must be submitted for medical insurance claims.",
"Premium payments can be made online through net banking, debit card, or credit card.",
"A grace period of 30 days is allowed for premium payment after the due date.",
"If premium is not paid within the grace period, the policy may lapse.",
"Policies can be cancelled within 15 days of purchase for a full refund.",
"Insurance claims are typically processed within 7–10 working days after verification.",
"Customers receive SMS and email notifications once the claim is processed.",
"Nominee details can be updated through the customer portal.",
"Customers can update their address and phone number through the account dashboard.",
"Lost policy documents can be reissued by submitting an application request.",
"Policy renewal reminders are sent to customers before the premium due date.",
"Claim status can be checked using the claim reference number.",
"For cashless claims, the hospital coordinates directly with the insurer.",
"Customers can contact support through phone, email, or online portal."
]

# -----------------------------
# Embeddings + Vector DB
# -----------------------------
embedder = SentenceTransformer("all-MiniLM-L6-v2")

knowledge_embeddings = embedder.encode(knowledge_base)

dimension = knowledge_embeddings.shape[1]

index = faiss.IndexFlatL2(dimension)
index.add(np.array(knowledge_embeddings))


# -----------------------------
# Retriever
# -----------------------------
def retrieve_context(query):

    query_embedding = embedder.encode([query])

    distances, indices = index.search(query_embedding, k=3)

    results = [knowledge_base[i] for i in indices[0]]

    return "\n".join(results)


# -----------------------------
# Agent Tools
# -----------------------------
def policy_status_tool():
    return "Policy is active and in good standing."

def claim_document_tool():
    return """
Required documents:
• ID proof
• Policy document
• Hospital bills
• Claim form
"""

def premium_payment_tool():
    return """
Premium payments can be made online using:
• Net banking
• Debit card
• Credit card

A 30-day grace period is allowed.
"""


# -----------------------------
# Agent Decision
# -----------------------------
def agent_decide_tool(query):

    query = query.lower()

    if "policy status" in query:
        return "policy_status"

    elif "claim" in query:
        return "claim_documents"

    elif "premium" in query or "payment" in query:
        return "premium_payment"

    else:
        return "retriever"


# -----------------------------
# Chat Function
# -----------------------------
def chatbot(message, history):

    tool = agent_decide_tool(message)

    if tool == "policy_status":
        info = policy_status_tool()

    elif tool == "claim_documents":
        info = claim_document_tool()

    elif tool == "premium_payment":
        info = premium_payment_tool()

    else:
        info = retrieve_context(message)

    prompt = f"""
You are a helpful insurance assistant.

Use this information to answer the customer.

Information:
{info}

Customer Question:
{message}
"""

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    answer = completion.choices[0].message.content

    response = f"""
🧠 **Agent reasoning:** {tool}

🔧 **Tool used:** {tool}

💬 **Response:**
{answer}
"""

    return response


# -----------------------------
# UI Layout
# -----------------------------
with gr.Blocks(theme=gr.themes.Soft()) as demo:

    gr.Markdown("# 🤖 AI Insurance Support Assistant")

    gr.Markdown(
    """
AI Agent prototype for **insurance customer support automation**

This assistant can:
• Answer policy questions  
• Provide claim information  
• Help with premium payments  
• Retrieve insurance knowledge
"""
)

    chatbot_ui = gr.ChatInterface(
        chatbot,
        examples=[
            "How can I check my policy status?",
            "What documents are needed for claims?",
            "What happens if I miss premium payment?",
            "How do I update nominee details?"
        ]
    )

demo.launch()