import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException


BMKG_URL = "https://bmkg.go.id"
HEADERS = {
    "User-Agent": "Quakindo/0.1.3 (Earthquake Data Fetcher)"
}


def fetch_earthquake_data():
    """
    Fetches the latest earthquake data from the official BMKG website.
    Returns dict or raises Exception.
    """
    try:
        response = requests.get(BMKG_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except RequestException as e:
        raise RuntimeError(f"Failed to connect to BMKG: {e}")

    soup = BeautifulSoup(response.text, "html.parser")

    # Default values
    data = {
        "date": "N/A",
        "time": "N/A",
        "magnitude": "N/A",
        "depth": "N/A",
        "coordinates": "N/A",
        "epicenter": "N/A"
    }

    # Date & time
    dt = soup.select_one("p.mt-2.text-sm.leading-[22px].font-medium.text-gray-primary")
    if dt:
        parts = dt.get_text(strip=True).split(", ")
        if len(parts) == 2:
            data["date"], data["time"] = parts

    # Epicenter
    epi = soup.select_one("p.mt-4.text-xl.font-bold.text-black-primary")
    if epi:
        data["epicenter"] = epi.get_text(strip=True)

    # Magnitude, depth, coordinates
    vals = soup.select("span.text-base.font-bold.text-black-primary")
    if len(vals) >= 3:
        data["magnitude"] = vals[0].get_text(strip=True)
        data["depth"] = vals[1].get_text(strip=True)
        data["coordinates"] = vals[2].get_text(strip=True)

    return data


def display_data(data):
    """Prints the earthquake data in a human-readable format."""
    if not data:
        print("⚠️  No earthquake data available.")
        return

    print("🌍 Latest Earthquake Update (BMKG)")
    for k, v in data.items():
        print(f"{k.capitalize()}: {v}")

__all__ = ["fetch_earthquake_data", "display_data"]
