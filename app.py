from dotenv import load_dotenv
from flask import Flask, render_template, request, send_file
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import requests
import os
import google.generativeai as genai

import io
# Load environment variables
load_dotenv()

app = Flask(__name__)

# Load API Keys
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")
latest_summary = ""

@app.route("/", methods=["GET", "POST"])
def home():

    articles = []
    summary = ""
    error = ""

    if request.method == "POST":

        keyword = request.form["keyword"]
        from_date = request.form["from_date"]
        to_date = request.form["to_date"]

        url = (
            "https://newsapi.org/v2/everything?"
            f"q={keyword}"
            f"&from={from_date}"
            f"&to={to_date}"
            "&sortBy=publishedAt"
            "&language=en"
            "&pageSize=10"
            f"&apiKey={NEWS_API_KEY}"
        )

        response = requests.get(url)
        data = response.json()

        print(data)

        if data.get("status") == "ok":

            articles = data.get("articles", [])

            if articles:

                news_text = ""

                for article in articles[:5]:

                    title = article.get("title", "")
                    description = article.get("description", "")

                    news_text += f"""
Title: {title}

Description:
{description}

"""

                prompt = f"""
You are an AI News Assistant.

Summarize the following news articles.

Return the response in this format:

Overall Summary:
(2-3 paragraphs)

Key Highlights:
• Point 1
• Point 2
• Point 3

Important Trends:
• Trend 1
• Trend 2

News Articles:

{news_text}
"""

                try:
                    gemini_response = model.generate_content(prompt)
                    summary = gemini_response.text

                    global latest_summary
                    latest_summary = summary

                except Exception as e:
                    summary = f"Gemini Error: {e}"

            else:
                error = "No articles found."

        else:
            error = data.get("message", "Something went wrong.")

    return render_template(
        "index.html",
        articles=articles,
        summary=summary,
        error=error
    )
@app.route("/download")
def download():

    global latest_summary

    if latest_summary == "":
        return "No summary available to download."

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph("AI News Digest Summary", styles["Title"])
    )

    story.append(
        Paragraph(latest_summary.replace("\n", "<br/>"),
                  styles["BodyText"])
    )

    doc.build(story)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="AI_News_Summary.pdf",
        mimetype="application/pdf"
    )
if __name__ == "__main__":
    app.run(debug=True)