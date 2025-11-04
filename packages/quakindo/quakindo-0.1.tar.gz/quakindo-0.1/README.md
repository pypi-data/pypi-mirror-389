# 🌍 Quakindo: Latest Earthquake Update

Quakindo (Quake-Indonesia) is a concise, open-source Python library
designed to fetch and process the latest earthquake data in Indonesia.
This package sources its data directly from BMKG (Badan Meteorologi,
Klimatologi, dan Geofisika), making it a valuable tool for geophysical
monitoring projects, early warning applications, or data integration.

## ✨ Features

The library provides crucial details in a clean, structured Python
dictionary format:

-   ⚡ **Direct Data Extraction:** Fetches the very latest earthquake
    update directly from the official BMKG website.
-   📚 **Structured Data Output:** Returns earthquake data ready for
    integration into databases, APIs, or dashboard displays.
-   🎯 **Comprehensive Details:** Includes:
    -   Date and Time (WIB)
    -   Magnitude
    -   Depth
    -   Coordinates (Parsed into clean numerical Latitude/Longitude
        values)
    -   Epicenter Location
    -   Felt Intensity (MMI Scale)

## 🛠️ Installation

You can install quakindo directly using pip:

``` bash
pip install quakindo
```

## 💻 Quick Usage

Here is a simple example demonstrating how to use the quakindo package
in your Python code:

``` python
from quakindo import fetch_earthquake_data, display_data

# 1. Fetch the latest data
equake_data = fetch_earthquake_data()

# 2. Display the data
if equake_data:
    print("--- QUAKINDO EARTHQUAKE REPORT ---")
    display_data(equake_data)
else:
    print("Failed to retrieve earthquake data.")
```

## 📝 Example Output

(Note: Coordinates will be parsed into negative values for LS/BB and
positive for LU/BT.)

    Latest Earthquake Update (BMKG)
    Date: 03 Nov 2025
    Time: 12:45:00 WIB
    Magnitude: 4,8
    Depth: 15 Km
    Coordinates: LS=-1.57, BT=127.87
    Epicenter: 122 km TimurLaut TERNATE-MALUT

## 📄 License

This project is licensed under the **GNU General Public License v3
(GPLv3)**. See the LICENSE file in the root directory for full details.
