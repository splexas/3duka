import requests
import json
import sys
from getpass import getpass

class Eduka:
    def __init__(self) -> None:
        self.endpoint = "https://klase.eduka.lt"

    def login(self, username: str, password: str) -> str:
        '''
        Returns the session key used for accessing Eduka data
        '''

        req = requests.post(
            self.endpoint + "/api/anonymously/login",
            json = {
                "username": username,
                "password": password
            }
        )
        
        if (req.status_code != 200):
            return None
        
        return req.cookies["PHPSESSID"]


    def read_task_data(self, session_key: str, quiz_id: int) -> dict:
        '''
        Returns a dictionary where all the neccesary information of tasks are stored
        '''

        req = requests.get(
            self.endpoint + f"/api/student/quiz-templates/data/{quiz_id}/sprendimas",
            cookies = {"PHPSESSID": session_key}
        )

        return req.json()

    def decode_task_data(self, task_data: dict) -> dict:
        '''
        Decodes the task dictionary so properly usable and readable
        '''

        tasks_data = json.loads(task_data["tasksData"])
        working_state = json.loads(task_data["workingState"])
        scores = json.loads(working_state["score"])

        # cannot change values in a dict that is already in iteration as it changes size
        temp_scores = {}
        for key, value in scores.items():
            temp_scores[key] = json.loads(value)

        
        extracted = {"base": {}, "tasks": {}}
        extracted["base"] = tasks_data
        extracted["tasks"] = temp_scores

        return extracted


if __name__ == "__main__":
    eduka = Eduka()
    
    print("How do you wish to login?\n1: by session ID\n2: by credentials")
    login_method = int(input("Login method: "))

    ses_key = None

    if (login_method == 1):
        ses_key = input("Session key: ")

    elif (login_method == 2):
        username = input("Username: ")
        password = getpass("Password: ") # hides the input
        
        ses_key = eduka.login(username, password)
        if (ses_key == None):
            print("You have provided invalid login credentials.")
            exit(1)
        
        print(f"\nUpdate this session ID (PHPSESSID) in your browser: {ses_key}\nExecute `javascript:document.cookie=\"PHPSESSID=your_session_id\";` in klase.eduka.lt/auth\n")

    else:
        print("You have provided an invalid login method.")
        exit(1)

    quiz_id = int(input("Quiz ID: "))

    while True:
        task_data = eduka.read_task_data(session_key=ses_key, quiz_id=quiz_id)
        decoded = eduka.decode_task_data(task_data)

        max_points = {}
        for task_id in decoded["base"]["ids"]:
            max_points[task_id] = decoded["base"]["points"][decoded["base"]["ids"].index(task_id)]

        for task_id in decoded["base"]["ids"]:
            current_score = int(decoded["tasks"][task_id]["score"])
            max_score = int(decoded["tasks"][task_id]["maxScore"])
            max_points_per_task = max_points[task_id]

            result = (current_score * max_points_per_task) / max_score
            if result < 0: result = 0.0 # the endpoint can provide a negative value

            sys.stdout.write("\033[2K") # clear entire line
            print(f"Task ID: {task_id}: {result}/{max_points_per_task}")
        
        sys.stdout.write(f"\033[{len(decoded['base']['ids'])}A") # move the cursor upward `len(decoded['base']['ids']` times
