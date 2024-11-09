import requests
import json
import re

# Configurations
LITELLM_BASE_URL = "http://0.0.0.0:4000"  # URL of the LiteLLM server
MODEL_NAME = "ollama/llama3.2:latest"
JSONL_FILE = "test.jsonl"  # Path to the JSONL file containing questions
RESULT_FILE = "result.txt"  # Output file for numerical answers

class Agent:
    def __init__(self, name, role, model_name=MODEL_NAME):
        self.name = name
        self.role = role
        self.model_name = model_name

    def prompt(self, message, max_tokens=300):
        """Sends a message to the agent and returns the response."""
        data = {
            "model": self.model_name,
            "prompt": f"{self.role} {self.name}: {message}",
            "max_tokens": max_tokens
        }
        response = requests.post(f"{LITELLM_BASE_URL}/v1/completions", json=data)
        
        response_json = response.json()
        print("Full response from LiteLLM:", response_json)
        
        if "choices" in response_json:
            return response_json["choices"][0]["text"].strip()
        else:
            raise ValueError("The response does not contain the expected 'choices' key.")
            
class OrganizerAgent(Agent):
    def __init__(self, model_name=MODEL_NAME):
        super().__init__("Organizer", "Central Organizer", model_name)
        self.agents = []

    def determine_difficulty(self, question):
        """Determines the difficulty of a question based on its length."""
        question_length = len(question)
        if question_length < 50:
            return "easy"
        elif 50 <= question_length < 100:
            return "medium"
        else:
            return "hard"

    def decide_number_of_agents(self, difficulty):
        """Decides the number of agents based on the difficulty of the question."""
        if difficulty == "easy":
            num_agents = 2
        elif difficulty == "medium":
            num_agents = 3
        else:  # hard
            num_agents = 5
        print(f"Organizer has decided that {num_agents} agents are required for a '{difficulty}' question.")
        return num_agents

    def create_agents(self, num_agents):
        """Creates agents with specific roles for the discussion."""
        roles = [f"Agent {i+1}" for i in range(num_agents)]
        self.agents = [Agent(name=f"Agent_{i+1}", role=roles[i]) for i in range(num_agents)]

    def initialize_discussion(self, question):
        """Initializes the discussion by prompting each agent with the question and their role."""
        for agent in self.agents:
            agent.prompt(f"You are {agent.role}. Here is the question to discuss: '{question}'")

    def conduct_discussion(self, question):
        """Conducts the discussion by gathering responses from all agents."""
        responses = []
        for agent in self.agents:
            response = agent.prompt(question)
            responses.append((agent.name, response))
            print(f"{agent.name} ({agent.role}): {response}")
        return responses

    def summarize_discussion(self, responses, max_tokens=300):
        """Summarizes the discussion responses with pagination."""
        summary_prompt = "Summarize the following discussion:\n"
        for name, response in responses:
            summary_prompt += f"{name}: {response}\n"

        full_summary = ""
        while True:
            data = {
                "model": self.model_name,
                "prompt": f"{self.role} {self.name}: {summary_prompt}",
                "max_tokens": max_tokens
            }
            response = requests.post(f"{LITELLM_BASE_URL}/v1/completions", json=data)
            response_json = response.json()
            
            if "choices" in response_json:
                part = response_json["choices"][0]["text"].strip()
                full_summary += part
                
                if response_json["choices"][0].get("finish_reason") == "stop":
                    break
                else:
                    summary_prompt = part
            else:
                raise ValueError("The response does not contain the expected 'choices' key.")
        
        return full_summary

    def extract_numerical_answer(self, summary):
        """Extracts the first numerical answer from the summary, if available."""
        match = re.search(r'\b\d+(\.\d+)?\b', summary)  # Matches integers or decimals
        if match:
            return match.group(0)
        else:
            return "No numerical answer found"

    def write_numerical_answer_to_file(self, answer):
        """Writes the extracted numerical answer to the result file."""
        with open(RESULT_FILE, 'a') as file:
            file.write(f"{answer}\n")

# Main Function
def main():
    organizer = OrganizerAgent()
    
    # Clear or create the result file before writing new answers
    open(RESULT_FILE, 'w').close()

    # Open the JSONL file and read questions
    with open(JSONL_FILE, 'r') as file:
        for line in file:
            question_data = json.loads(line)
            question = question_data.get("question")
            
            if question:
                print(f"\nProcessing question: {question}")
                
                # Determine the difficulty of the question
                difficulty = organizer.determine_difficulty(question)
                
                # Organizer decides the number of agents required based on difficulty
                num_agents = organizer.decide_number_of_agents(difficulty)
                organizer.create_agents(num_agents)
                
                # Initialize discussion
                organizer.initialize_discussion(question)
                
                # Conduct the discussion
                responses = organizer.conduct_discussion(question)
                
                # Organizer summarizes the discussion
                final_summary = organizer.summarize_discussion(responses)
                print("\nFinal Summary from Organizer:\n", final_summary)
                
                # Extract numerical answer and write it to the result file
                numerical_answer = organizer.extract_numerical_answer(final_summary)
                organizer.write_numerical_answer_to_file(numerical_answer)
                print(f"Numerical answer written to {RESULT_FILE}: {numerical_answer}")

if __name__ == "__main__":
    main()
