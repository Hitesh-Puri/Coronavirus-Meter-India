import requests
import json
import pyttsx3
import speech_recognition as sr
import re
import threading
import time

API_KEY = "YOUR API FROM PARSE_HUB"
PROJECT_TOKEN = "YOUR PROJECT_TOKEN FROM PARSE_HUB"
RUN_TOKEN = "YOUR RUN_TOKEN FROM PARSE_HUB"


class Data:
    def __init__(self, api_key, project_token):
        self.api_key = api_key
        self.project_token = project_token
        self.params = {
            "api_key": self.api_key
        }
        self.data = self.get_data()

    def get_data(self):
        response = requests.get(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/last_ready_run/data', params=self.params)
        data = json.loads(response.text)
        return data

    def get_total_cases(self):
        data = self.data['total']

        for content in data:
            if content['name'] == "Confirmed":
                return content['value']

    def get_total_deaths(self):
        data = self.data['total']

        for content in data:
            if content['name'] == "Deceased":
                return content['value']

        return "0"

    def get_state_data(self, state):
        data = self.data["state"]

        for content in data:
            if content['name'].lower() == state.lower():
                return content

        return "0"

    def get_list_of_states(self):
        states = []
        for state in self.data['state']:
            states.append(state['name'].lower())

        return  states

#print(data.get_list_of_countries())
#print(data.get_country_data("India")['total_cases'])
    def update_data(self):
        response = requests.post(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/run', params=self.params)

        def poll():
            time.sleep(0.1)
            old_data = self.data
            while True:
                new_data = self.get_data()
                if new_data != old_data:
                    self.data = new_data
                    print("Data updated")
                    break
                time.sleep(5)

        t = threading.Thread(target=poll)
        t.start()


def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

#speak("hello")
def get_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        said = ""

        try:
            said = r.recognize_google(audio)
        except Exception as e:
            print("Exception:", str(e))

    return said.lower()

#print(get_audio())
def main():
    print("Started Program")
    data = Data(API_KEY, PROJECT_TOKEN)
    END_PHASE = "over and out"
    state_list = data.get_list_of_states()

    TOTAL_PATTERNS = {
        re.compile("[\w\s]+ total [\w\s]+ cases"):data.get_total_cases,
        re.compile("[\w\s]+ total cases"): data.get_total_cases,
        re.compile("[\w\s]+ total [\w\s]+ deaths"): data.get_total_deaths,
        re.compile("[\w\s]+ total deaths"): data.get_total_deaths
    }        

    STATE_PATTERNS = {
					re.compile("[\w\s]+ cases [\w\s]+"): lambda state: data.get_state_data(state)['total_cases'],
                    re.compile("[\w\s]+ deaths [\w\s]+"): lambda state: data.get_state_data(state)['total_deaths'],
					}

    UPDATE_COMMAND = "update"

    while True:
        print("Listening...")
        text = get_audio()
        print(text)
        result = None

        for pattern, func in STATE_PATTERNS.items():
            if pattern.match(text):
                words = set(text.split(" "))
                for state in state_list:
                    if state in words:
                        result = func(state)
                        break

        for pattern, func in TOTAL_PATTERNS.items():
            if pattern.match(text):
                result = func()
                break

        if text == UPDATE_COMMAND:
            result = "Data is being updated. this may take some time!"
            data.update_data()

        if result:
            speak(result)

        if text.find(END_PHASE) != -1:   # stop loop
            print("Exit")
            break

main()