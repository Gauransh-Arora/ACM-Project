import requests
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
AIR_QUALITY_URL = "http://api.openweathermap.org/data/2.5/air_pollution"
GEO_API_KEY = os.getenv("GEO_API_KEY")
GEO_BASE_URL = "http://api.ipstack.com/check"
REPORTS_DIR = "weather_reports"

class WeatherNotifier:
    def __init__(self, api_key):
        self.api_key = api_key

    def fetch_weather(self, city):
        try:
            params = {
                'q': city,
                'appid': self.api_key,
                'units': 'metric'
            }
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Unable to fetch weather data: {e}")
            return None

    def parse_weather(self, data):
        if data:
            city = data.get("name", "Unknown")
            temp = data["main"].get("temp", "N/A")
            desc = data["weather"][0].get("description", "N/A").capitalize()
            lat = data["coord"]["lat"]
            lon = data["coord"]["lon"]
            return city, temp, desc, lat, lon
        return "No data available."

    def fetch_air_quality(self, lat, lon):
        try:
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key
            }
            response = requests.get(AIR_QUALITY_URL, params=params)
            response.raise_for_status()
            data = response.json()

            aqi = data['list'][0]['main']['aqi']
            aqi_desc = {
                1: "Good",
                2: "Fair",
                3: "Moderate",
                4: "Poor",
                5: "Very Poor"
            }
            return aqi_desc.get(aqi, "Unknown"), aqi
        except requests.exceptions.RequestException as e:
            return "Error fetching air quality", None

    def activity_notifications(self, temp, desc):
        notifications = []
        if desc.lower().find("rain") != -1:
            notifications.append("Caution: Roads may be slippery.")
        if temp < 5:
            notifications.append("Warning: Sudden temperature drop detected, wear warm clothing.")
        return notifications

class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.notifier = WeatherNotifier(API_KEY)

        self.root.title("Weather Notifier")
        self.root.geometry("800x800")
        self.root.configure(bg="#ADD8E6")

        self.city_label = tk.Label(root, text="Enter city name:", font=("Arial", 12), bg="#ADD8E6")
        self.city_label.pack(pady=10)

        self.city_entry = ttk.Entry(root, font=("Arial", 12))
        self.city_entry.pack(pady=5)

        self.search_button = ttk.Button(root, text="Search", command=self.search_weather)
        self.search_button.pack(pady=10)

        self.result_frame = tk.Frame(root, bg="#ADD8E6")
        self.result_frame.pack(pady=20)

        self.result_label = tk.Label(self.result_frame, text="", font=("Arial", 12), justify="left", bg="#ADD8E6")
        self.result_label.pack()

        self.notification_label = tk.Label(self.result_frame, text="", font=("Arial", 10), fg="red", justify="left", bg="#ADD8E6")
        self.notification_label.pack()

        self.report_button = ttk.Button(root, text="Report Weather", command=self.report_weather)
        self.report_button.pack(pady=10)

        self.reports_button = ttk.Button(root, text="View Reports", command=self.view_reports)
        self.reports_button.pack(pady=10)

        self.fetch_current_location_weather()

    def search_weather(self):
        city = self.city_entry.get()
        if city:
            data = self.notifier.fetch_weather(city)
            if data:
                city_name, temp, desc, lat, lon = self.notifier.parse_weather(data)
                air_quality_desc, air_quality_index = self.notifier.fetch_air_quality(lat, lon)

                reports = self.get_city_reports(city)
                report_info = "\n\nUser-submitted reports:\n" + "\n".join(reports) if reports else "\n\nNo user-submitted reports."

                weather_info = f"City: {city_name}\nTemperature: {temp}°C\nCondition: {desc}\nAir Quality: {air_quality_desc} (Index: {air_quality_index}){report_info}"
                self.result_label.config(text=weather_info)

                notifications = self.notifier.activity_notifications(temp, desc)
                self.notification_label.config(text="\n".join(notifications) if notifications else "")
        else:
            messagebox.showinfo("Input Required", "Please enter a city name.")

    def fetch_current_location_weather(self):
        try:
            params = {
                'access_key': GEO_API_KEY
            }
            response = requests.get(GEO_BASE_URL, params=params)
            response.raise_for_status()
            location_data = response.json()
            city = location_data.get("city", "")
            if city:
                data = self.notifier.fetch_weather(city)
                if data:
                    city_name, temp, desc, lat, lon = self.notifier.parse_weather(data)
                    air_quality_desc, air_quality_index = self.notifier.fetch_air_quality(lat, lon)

                    reports = self.get_city_reports(city)
                    report_info = "\n\nUser-submitted reports:\n" + "\n".join(reports) if reports else "\n\nNo user-submitted reports."

                    weather_info = f"Current Location:\nCity: {city_name}\nTemperature: {temp}°C\nCondition: {desc}\nAir Quality: {air_quality_desc} (Index: {air_quality_index}){report_info}"
                    self.result_label.config(text=weather_info)

                    notifications = self.notifier.activity_notifications(temp, desc)
                    self.notification_label.config(text="\n".join(notifications) if notifications else "")
            else:
                self.result_label.config(text="Could not fetch location.")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Unable to fetch location: {e}")

    def report_weather(self):
        def submit_report():
            description = desc_entry.get()
            city = city_entry.get()

            if not os.path.exists(REPORTS_DIR):
                os.makedirs(REPORTS_DIR)

            report_file = os.path.join(REPORTS_DIR, f"{city.replace(' ', '_')}_report.txt")
            with open(report_file, "a") as file:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                file.write(f"Time: {timestamp}\nDescription: {description}\n\n")

            messagebox.showinfo("Success", "Weather report submitted successfully!")
            report_window.destroy()

        report_window = tk.Toplevel(self.root)
        report_window.title("Report Weather")
        report_window.geometry("400x300")

        tk.Label(report_window, text="City:").pack(pady=5)
        city_entry = ttk.Entry(report_window)
        city_entry.pack(pady=5)

        tk.Label(report_window, text="Weather Description:").pack(pady=5)
        desc_entry = ttk.Entry(report_window)
        desc_entry.pack(pady=5)

        ttk.Button(report_window, text="Submit", command=submit_report).pack(pady=10)

    def view_reports(self):
        if not os.path.exists(REPORTS_DIR):
            messagebox.showinfo("No Reports", "No weather reports available yet.")
            return

        reports_window = tk.Toplevel(self.root)
        reports_window.title("View Reports")
        reports_window.geometry("400x300")

        report_text = tk.Text(reports_window, wrap=tk.WORD)
        report_text.pack(expand=True, fill=tk.BOTH)

        for file_name in os.listdir(REPORTS_DIR):
            file_path = os.path.join(REPORTS_DIR, file_name)
            with open(file_path, "r") as file:
                report_text.insert(tk.END, file.read() + "\n---\n")

    def get_city_reports(self, city):
        city_file = os.path.join(REPORTS_DIR, f"{city.replace(' ', '_')}_report.txt")
        if os.path.exists(city_file):
            with open(city_file, "r") as file:
                return file.readlines()
        return []

if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()
