import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException


def fetch_earthquake_data():
    """
    Fetches the latest earthquake data from the official BMKG website.
    Returns the parsed data as a dictionary.
    """
    # Initialize variables with default values
    date = "N/A"
    time = "N/A"
    epicenter = "N/A"
    magnitude = "N/A"
    depth = "N/A"
    coordinates = "N/A"

    try:
        content = requests.get("https://bmkg.go.id")
    except RequestException:
        return None

    if content.status_code == 200:
        data = dict()
        soup = BeautifulSoup(content.text, "html.parser")
        title = soup.find("title")
        print(title.text)

        # --- 1. Fetch Date, Time, and Epicenter ---
        # NOTE: The code below is still highly vulnerable to AttributeError if the element is not found.
        result_elem = soup.find("p", {"class": "mt-2 text-sm leading-[22px] font-medium text-gray-primary"})

        # Apply strict error handling here before split/text access for production code!
        if result_elem:
            result_split = result_elem.text.split(", ")
            date = result_split[0]
            time = result_split[1]

        epicenter_elem = soup.find("p", {"class": "mt-4 text-xl lg:text-2xl font-bold text-black-primary"})

        if epicenter_elem:
            epicenter = epicenter_elem.text

        # --- 2. Fetch Magnitude, Depth, Coordinates (Index-based method) ---
        all_span_values = soup.find_all("span", {"class": "text-base lg:text-lg font-bold text-black-primary"})

        if len(all_span_values) > 2:  # Check if all three values exist
            magnitude = all_span_values[0].text.strip()
            depth = all_span_values[1].text.strip()
            coordinates = all_span_values[2].text.strip()
        else:
            if len(all_span_values) > 0:
                magnitude = all_span_values[0].text.strip()
            if len(all_span_values) > 1:
                depth = all_span_values[1].text.strip()

            # coordinates remains "N/A"

        data["date"] = date
        data["time"] = time
        data["magnitude"] = magnitude
        data["depth"] = depth
        data["coordinates"] = coordinates
        data["epicenter"] = epicenter
        return data
    else:
        return None


def display_data(data):
    """
    Prints the earthquake data in a human-readable format.
    """
    if data is None:
        print("Could not retrieve the latest earthquake data.")
        return None
    print("Latest Earthquake Update (BMKG)")
    print(f"Date: {data['date']}")
    print(f"Time: {data['time']}")
    print(f"Magnitude: {data['magnitude']}")
    print(f"Depth: {data['depth']}")
    print(f"Coordinates: {data['coordinates']}")
    print(f"Epicenter: {data['epicenter']}")
    return None