"""Download Wikipedia article intros (text + thumbnail) into data/articles.json."""
import json
import time
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

API = "https://en.wikipedia.org/w/api.php"
UA = "minisearch/0.2 (learning project; https://github.com/Charanya3408/minisearch)"
OUT = Path("data/articles.json")

SEEDS = [
    "Photosynthesis", "Black hole", "DNA", "Evolution", "Periodic table", "Quantum mechanics",
    "Plate tectonics", "Vaccine", "Antibiotic", "Mitochondrion", "CRISPR", "Genome", "Protein",
    "Enzyme", "Neuron", "Immune system", "Climate change", "Solar System", "Mars", "Jupiter",
    "Moon", "Galaxy", "Big Bang", "Gravity", "Electricity", "Magnet", "Atom", "Water", "Volcano",
    "Earthquake", "Algorithm", "Computer", "Internet", "Search engine", "Machine learning",
    "Neural network", "Python (programming language)", "Database", "Cryptography",
    "Operating system", "Binary search algorithm", "Hash table", "Heap (data structure)",
    "Compiler", "Blockchain", "Robotics", "Artificial intelligence", "World Wide Web",
    "Smartphone", "Semiconductor", "Indian independence movement", "Mughal Empire",
    "Chola dynasty", "Tamil Nadu", "Thanjavur", "Brihadisvara Temple", "Chennai", "Kerala",
    "Himalayas", "Ganges", "Great Wall of China", "Roman Empire", "Industrial Revolution",
    "World War II", "Ancient Egypt", "Great Pyramid of Giza", "Amazon rainforest", "Sahara",
    "Mount Everest", "Monsoon", "Taj Mahal", "Delhi", "Mumbai", "Bengaluru", "Silk Road",
    "Cricket", "Association football", "Olympic Games", "Chess", "Yoga", "Ayurveda",
    "Indian cuisine", "Dosa", "Biryani", "Tea", "Coffee", "Chocolate", "Sourdough",
    "Cinema of India", "Bharatanatyam", "Carnatic music", "Diwali", "Pongal",
    "Rabindranath Tagore", "A. P. J. Abdul Kalam", "Mahatma Gandhi", "Albert Einstein",
    "Marie Curie", "Isaac Newton", "Leonardo da Vinci", "Ada Lovelace", "Alan Turing",
    "Srinivasa Ramanujan", "C. V. Raman", "Elephant", "Tiger", "Indian peafowl", "Honey bee",
    "Coral reef", "Blue whale", "Octopus",
]


def fetch_json(url: str) -> dict:
    with urlopen(Request(url, headers={"User-Agent": UA}), timeout=30) as response:
        return json.load(response)


def batch_url(titles: list[str]) -> str:
    params = {
        "action": "query", "format": "json", "prop": "extracts|pageimages",
        "exintro": 1, "explaintext": 1, "exlimit": "max",
        "piprop": "thumbnail", "pithumbsize": 480, "redirects": 1,
        "titles": "|".join(titles),
    }
    return API + "?" + urlencode(params)


def parse_pages(payload: dict) -> list[dict]:
    docs = []
    for page in payload.get("query", {}).get("pages", {}).values():
        text = (page.get("extract") or "").strip()
        if "missing" in page or len(text) < 80:
            continue
        title = page["title"]
        docs.append({
            "id": str(page["pageid"]),
            "title": title,
            "text": text,
            "thumb": page.get("thumbnail", {}).get("source", ""),
            "url": "https://en.wikipedia.org/wiki/" + quote(title.replace(" ", "_")),
        })
    return docs


def crawl(titles=SEEDS, fetch=fetch_json, pause: float = 0.4, size: int = 20) -> list[dict]:
    seen, docs = set(), []
    for i in range(0, len(titles), size):
        for doc in parse_pages(fetch(batch_url(titles[i:i + size]))):
            if doc["id"] not in seen:
                seen.add(doc["id"])
                docs.append(doc)
        print(f"fetched {min(i + size, len(titles))}/{len(titles)} titles, {len(docs)} articles")
        time.sleep(pause)
    return docs


def main() -> None:
    docs = crawl()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(docs), encoding="utf-8")
    print(f"Saved {len(docs)} articles to {OUT}")


if __name__ == "__main__":
    main()
