# import necessary libraries for web scraping
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote_plus
import re
from collections import defaultdict
from typing import Any, Dict

# define constants for the target website and headers to mimic a browser
SITE_ROOT = "https://esgnews.com/"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# function to scrape news articles related to a specific company tag from the target website
def get_articles(company_tag: str):
    """Scrapes news articles related to a specific company tag from the ESG News website.
    Inputs:
        company_tag: A string representing the company name or tag to search for (e.g. "Nike")
    Outputs:
        A list of dictionaries, each containing the title and URL of a relevant news article.
    """

    # construct the search URL by appending the company tag as a query parameter
    search_url = f"{SITE_ROOT}?s={quote_plus(company_tag)}"
    # make a GET request to the search URL and parse the response with BeautifulSoup
    with requests.Session() as session:
        session.headers.update(HEADERS)
        resp = session.get(search_url, timeout=30)
        resp.raise_for_status()
    # parse the HTML content of the response to extract relevant articles
    soup = BeautifulSoup(resp.text, "html.parser")

    articles = []
    seen = set()
    company_tag = company_tag.lower().strip()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        title = " ".join(a.get_text(" ", strip=True).split())

        if not href or not title:
            continue

        full_url = urljoin(SITE_ROOT, href)

        if not full_url.startswith(SITE_ROOT):
            continue
        if "/tag/" in full_url:
            continue
        if "?s=" in full_url:
            continue
        if len(title) < 20:
            continue

        title_l = title.lower()
        url_l = full_url.lower()

        if company_tag in title_l or company_tag in url_l:
            key = (title, full_url)
            if key not in seen:
                seen.add(key)
                articles.append({
                    "title": title,
                    "url": full_url,
                })

    return articles


# helper function to extract the main text content from a news article given its URL
def extract_article_data(url: str) -> dict:
    """Extracts the main text content and metadata from a news article given its URL.
    Inputs:
        url: The URL of the news article to extract data from
    Outputs:
        A dictionary containing the article's title, published date (if available), main text content, and the original URL.
    """

    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.decompose()

    title = ""
    if soup.title:
        title = soup.title.get_text(" ", strip=True)

    published_date = None
    time_tag = soup.find("time")
    if time_tag:
        published_date = time_tag.get("datetime") or time_tag.get_text(" ", strip=True)

    selectors = [
        "article",
        "div.td-post-content",
        "div.entry-content",
        "div.post-content",
        "main",
    ]

    body_text = ""

    for selector in selectors:
        container = soup.select_one(selector)
        if container:
            paragraphs = [
                p.get_text(" ", strip=True)
                for p in container.find_all(["p", "h2", "h3", "li"])
            ]
            paragraphs = [p for p in paragraphs if p]
            if paragraphs:
                body_text = "\n".join(paragraphs)
                break

    if not body_text:
        body_text = "\n".join(
            t.strip() for t in soup.stripped_strings if t.strip()
        )

    return {
        "title": title,
        "published_date": published_date,
        "text": f"{title}\n\n{body_text}" if title else body_text,
        "url": url,
    }


# helper function to build the expected json
def build_article_result(url: str, analysis: dict) -> dict:
    """Builds a structured dictionary containing the analysis results for a given article.
    Inputs:
        url: The URL of the article that was analyzed
        analysis: A dictionary containing the results of the article analysis, including relevance, strength, main ESG pillar, matched keywords, and any messages.
    Outputs:        
    A structured dictionary that can be easily consumed by the frontend to display the analysis results for the article.
    """

    return {
        "is_relevant": analysis.get("is_relevant"),
        "strength": analysis.get("strength"),
        "main_pillar": analysis.get("main_pillar"),
        "matched_keywords": analysis.get("matched_keywords", []),
        "message": analysis.get("message"),
        "url": url,
    }




# ESG-related keywords for each pillar to help determine the relevance and strength of news articles in relation to ESG topics
ESG_KEYWORDS = {
    "Environmental": [
        "emissions", "carbon", "co2", "climate", "net zero", "net-zero",
        "renewable", "renewables", "pollution", "waste", "recycling",
        "water", "biodiversity", "deforestation", "greenhouse gas",
        "scope 1", "scope 2", "scope 3", "sustainability"
    ],
    "Social": [
        "labor", "labour", "worker safety", "human rights", "supply chain",
        "diversity", "equity", "inclusion", "community", "employee welfare",
        "working conditions", "child labor", "child labour"
    ],
    "Governance": [
        "governance", "compliance", "ethics", "corruption", "bribery",
        "board", "shareholder", "transparency", "audit", "risk management",
        "executive compensation", "data privacy"
    ]
}


def split_sentences(text: str):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]


def strengthly_word(strength: str) -> str:
    return {
        "moderate": "moderately",
        "strong": "strongly"
    }.get(strength, strength)


# function to analyse content
def analyse_article(article_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyzes the content of a news article to determine its relevance to ESG topics, the strength of that relevance, the main ESG pillar it relates to, and which specific keywords were matched.
    Inputs:                                     
        Expects article_data in the shape:
        {
            "title": ...,
            "published_date": ...,
            "text": ...,
            "url": ...
        }
    Outputs:
        A dictionary containing:
        - is_relevant: A boolean indicating whether the article is relevant to ESG topics
        - strength: A string indicating the strength of the relevance ("none", "weak", "moderate", "strong")
        - main_pillar: The ESG pillar that the article is most strongly related to ("Environmental", "Social", "Governance"), or None if not relevant
        - matched_keywords: A list of ESG-related keywords that were found in the article
        - message: A human-readable message summarizing the analysis results
        - url: The original URL of the article that was analyzed
    """
    article_text = article_data["text"]
    url = article_data["url"]

    text = article_text.lower()
    pillar_matches = defaultdict(list)

    for pillar, keywords in ESG_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                pillar_matches[pillar].append(kw)

    counts = {pillar: len(set(matches)) for pillar, matches in pillar_matches.items()}
    total_matches = sum(counts.values())

    if total_matches == 0:
        return {
            "is_relevant": False,
            "strength": "none",
            "main_pillar": None,
            "matched_keywords": [],
            "message": "This article does not appear to be materially related to ESG.",
            "url": url
        }

    main_pillar = max(counts, key=counts.get)
    matched_keywords = sorted(set(pillar_matches[main_pillar]))

    if total_matches == 1:
        strength = "weak"
    elif total_matches <= 4:
        strength = "moderate"
    else:
        strength = "strong"

    if strength == "weak":
        message = (
            f"This article may be relevant to {main_pillar} topics, "
            f"with a limited number of related references such as {', '.join(matched_keywords[:3])}."
        )
    else:
        message = (
            f"This article appears {strengthly_word(strength)} related to {main_pillar} issues, "
            f"especially {', '.join(matched_keywords[:4])}."
        )

    return {
        "is_relevant": True,
        "strength": strength,
        "main_pillar": main_pillar,
        "matched_keywords": matched_keywords,
        "message": message,
        "url": url,
        "title": article_data.get("title"),
        #"published_date": article_data.get("published_date")
    }


# main function to get and analyze articles for a given company tag
def display_articles(company_tag: str) -> list[dict]:
    """Fetches, analyzes, and structures news articles related to a specific company tag.
    Inputs:
        company_tag: A string representing the company name or tag to search for (e.g. "Nike")
    Outputs:
        A list of structured dictionaries, each containing the analysis results for a relevant news article.
    """

    results = []
    articles = get_articles(company_tag)

    for article in articles:
        url = article.get("url")
        if not url:
            continue

        try:
            article_data = extract_article_data(url)
            analysis = analyse_article(article_data)

            if analysis.get("is_relevant"):
                results.append(analysis)

        except Exception as e:
            print(f"Error processing article {url}: {e}")

    strength_order = {"strong": 3, "moderate": 2, "weak": 1}
    results.sort(key=lambda x: strength_order.get(x.get("strength"), 0), reverse=True)

    return results[:5]