import oci
import logging
import tiktoken
import os
import csv
from datetime import datetime

# ------------------ Setup CSV Logging ------------------
csv_path = os.path.join(os.getcwd(), "oci_model_usage.csv")

# Create CSV file with header if not exists
if not os.path.exists(csv_path):
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow([
            "Timestamp",
            "Model OCID",
            "Model Name",
            "Family",
            "Input",
            "Output",
            "Prompt Tokens",
            "Completion Tokens",
            "Total Cost in inr",
            "Total Cost in cents"
        ])

print(f"[OCI Tracker] Usage will be saved to: {os.path.abspath(csv_path)}")
# ------------------ Tokenizer ------------------
tokenizer = tiktoken.get_encoding("cl100k_base")

# ------------------ Your Model Pricing ------------------
MODEL_PRICING = {
    "cohere.command-r-plus-08-2024": {"price": 0.27503, "family": "cohere"},
    "cohere.command-r-08-2024": {"price": 0.01587, "family": "cohere"},
    "cohere.command-a-03-2025": {"price": 0.27503, "family": "cohere"},
    "meta.llama-4-scout-17b-16e-instruct": {"price": 0.03178630, "family": "meta"},
    "meta.llama-4-maverick-17b-128e-instruct-fp8": {"price": 0.03178630, "family": "meta"},
    "xai.grok-3": {"input_price": 0.264, "output_price": 1.32, "family": "grok"},
    "xai.grok-3-fast": {"input_price": 0.44, "output_price": 2.20, "family": "grok"},
    "xai.grok-3-mini": {"input_price": 0.03, "output_price": 0.04, "family": "grok"},
    "xai.grok-3-mini-fast": {"input_price": 0.05, "output_price": 0.35, "family": "grok"},
}

# ------------------ Map OCID -> model name ------------------
OCID_TO_MODEL = {
    "ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceyaodm6rdyxmdzlddweh4amobzoo4fatlao2pwnekexmosq": "cohere.command-r-plus-08-2024",
    "ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceyanrlpnq5ybfu5hnzarg7jomak3q6kyhkzjsl4qj24fyoq": "cohere.command-r-08-2024",
    "ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceyapnibwg42qjhwaxrlqfpreueirtwghiwvv2whsnwmnlva": "cohere.command-a-03-2025",
    "ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceyarojgfh6msa452vziycwfymle5gxdvpwwxzara53topmq": "meta.llama-4-scout-17b-16e-instruct",
    "ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceyayjawvuonfkw2ua4bob4rlnnlhs522pafbglivtwlfzta": "meta.llama-4-maverick-17b-128e-instruct-fp8",
    "ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceya6dvgvvj3ovy4lerdl6fvx525x3yweacnrgn4ryfwwcoq": "xai.grok-3",
    "ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceyat326ygnn5hesfplopdmkyrklzcehzxhk5262655bthjq": "xai.grok-3-fast",
    "ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceyavwbgai5nlntsd5hngaileroifuoec5qxttmydhq7mykq": "xai.grok-3-mini",
    "ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceyaoukpjdotfk5fmhkps63szixxhfiyfamurrzkqea7sjva": "xai.grok-3-mini-fast",
}

# ------------------ Save Original ------------------
_original_chat = oci.generative_ai_inference.GenerativeAiInferenceClient.chat
_original_embed_text = oci.generative_ai_inference.GenerativeAiInferenceClient.embed_text

# ------------------ Monkey Patch ------------------
def patched_chat(self, chat_detail, *args, **kwargs):
    response =""
    try:
        # Model info
        model_id = getattr(chat_detail.serving_mode, "model_id", None)
        model_name = OCID_TO_MODEL.get(model_id, "unknown")
        pricing = MODEL_PRICING.get(model_name, {})

        # Extract user input
        user_input = None
        if hasattr(chat_detail.chat_request, "message"):
            user_input = chat_detail.chat_request.message
        elif hasattr(chat_detail.chat_request, "messages"):
            msgs = chat_detail.chat_request.messages
            if msgs and msgs[0].content and len(msgs[0].content) > 0:
                user_input = msgs[0].content[0].text

        # ------------------ Call real OCI API ------------------
        response = _original_chat(self, chat_detail, *args, **kwargs)

        # Extract model output
        output_text = None
        chat_hist = response.data.chat_response
        if hasattr(chat_hist, "text"):
            output_text = chat_hist.text
        elif hasattr(chat_hist, "choices") and chat_hist.choices:
            output_text = chat_hist.choices[0].message.content[0].text

        # Token counts
        input_tokens = len(tokenizer.encode(user_input or ""))
        output_tokens = len(tokenizer.encode(output_text or ""))

        # Cost calculation
        total_cost = 0.0
        if pricing.get("family") in ["cohere", "meta"]:
            total_cost = (input_tokens + output_tokens) * pricing["price"] / 2000
        elif pricing.get("family") == "grok":
            total_cost = (input_tokens / 1000) * pricing["input_price"] + \
                         (output_tokens / 1000) * pricing["output_price"]
            
        USD_TO_INR = 84.0
        total_cost_usd = total_cost / USD_TO_INR
        total_cost_cents = total_cost_usd * 100

        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ------------------ Append to CSV ------------------
        with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f,quoting=csv.QUOTE_ALL)
            writer.writerow([
                timestamp,
                model_id,
                model_name,
                pricing.get("family"),
                user_input or "",  
                output_text or "",
                input_tokens,
                output_tokens,
                round(total_cost, 6),
                round(total_cost_cents,6)
            ])

    except Exception as e:
        with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "ERROR", str(e)])

    return response


# --- Patched embed_text (fixed column order) ---
def patched_embed_text(self, embed_details, *args, **kwargs):
    try:
        # Extract model info
        model_id = getattr(embed_details.serving_mode, "model_id", None)
        model_name = OCID_TO_MODEL.get(model_id, "unknown")
        pricing_family = "universal"

        # Input texts
        input_texts = getattr(embed_details, "inputs", [])
        num_inputs = len(input_texts)

        # Total characters (for cost estimation)
        total_chars = sum(len(text) for text in input_texts)

        # ✅ Universal cost calculation (based on your ₹881.50 per 10 crore chars rule)
        cost_in_inr = total_chars * 0.000008815
        cost_in_usd = cost_in_inr / 84.0
        cost_in_cents = cost_in_usd * 100

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ------------------ Append to CSV ------------------
        with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerow([
                timestamp,
                model_id,
                model_name,
                pricing_family,
                f"{num_inputs} texts",   # Input summary
                "N/A",                   # Output
                total_chars,             # Treat characters as prompt tokens
                0,                       # No completion tokens
                round(cost_in_inr, 6),
                round(cost_in_cents, 6)
            ])

        print(f"[OCI Tracker] Logged embed for {model_name}: {num_inputs} texts, {total_chars} chars, ₹{round(cost_in_inr,3)}")

    except Exception as e:
        with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "EMBED_ERROR", str(e)])

    # Always return original embedding response
    return _original_embed_text(self, embed_details, *args, **kwargs)


# ------------------ Apply monkey patch ------------------
oci.generative_ai_inference.GenerativeAiInferenceClient.chat = patched_chat
oci.generative_ai_inference.GenerativeAiInferenceClient.embed_text = patched_embed_text