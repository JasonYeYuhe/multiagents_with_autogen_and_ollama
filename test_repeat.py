import requests
import json
import random

# Configurations
LITELLM_BASE_URL = "http://0.0.0.0:4000"  # URL of the LiteLLM server
MODEL_NAME = "ollama/llama3.2:latest"

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
        """Determines the difficulty of a question based on keywords indicating complexity."""
        difficulty_keywords = {
            "very easy": ["basic", "simple", "introduction", "overview"],
            "easy": ["example", "calculate", "definition", "explain", "describe"],
            "medium": ["analyze", "apply", "method", "theory", "relationship"],
            "hard": ["prove", "theorem", "mechanism", "advanced", "hypothesis"],
            "very hard": ["quantum", "relativity", "genomics", "multivariable", "neural network"]
        }
        
        # Default to "medium" if no specific keywords match
        detected_difficulty = "medium"
        
        # Check for keywords indicating difficulty level
        for level, keywords in difficulty_keywords.items():
            if any(keyword in question.lower() for keyword in keywords):
                detected_difficulty = level
                break
        
        print(f"Organizer has determined that the difficulty of the question is '{detected_difficulty}'.")
        return detected_difficulty

    def identify_areas_of_study(self, question):
        """Identifies the areas of study based on keywords in the question."""
        areas = []
        keywords = {
            "Mathematician": ["calculate", "equation", "math", "geometry", "algebra"],
            "Physicist": ["physics", "force", "energy", "gravity", "relativity"],
            "Biologist": ["biology", "genetics", "evolution", "cell"],
            "Historian": ["history", "ancient", "war", "revolution"],
            "Chemist": ["chemistry", "chemical", "reaction", "molecule"],
            "Economist": ["economics", "trade", "market", "finance", "GDP"],
            "Computer Scientist": ["algorithm", "data", "machine learning", "computer", "AI"],
            "Literary Analyst": ["literature", "novel", "poetry", "author", "narrative"],
            "Philosopher": ["philosophy", "ethics", "morality", "existentialism", "thought"],
            "Psychologist": ["psychology", "behavior", "cognition", "mind", "personality"],
            "Linguist": ["linguistics", "language", "syntax", "semantics", "grammar"],
            "Sociologist": ["sociology", "society", "culture", "social behavior", "class"],
            "Medical Doctor": ["medicine", "disease", "treatment", "diagnosis", "patient"],
            "Lawyer": ["law", "legal", "court", "justice", "rights"],
            "Environmental Scientist": ["environment", "climate", "pollution", "conservation", "ecosystem"],
            "Engineer": ["engineering", "design", "mechanics", "structure", "construction"]
        }

        # Check each area for keywords
        for area, keywords_list in keywords.items():
            if any(keyword in question.lower() for keyword in keywords_list):
                areas.append(area)
        
        # Default to Generalist if no specific area is detected
        if not areas:
            areas.append("Generalist")
        
        print(f"Organizer has identified the following areas of study: {', '.join(areas)}")
        return areas

    def decide_number_of_agents(self, difficulty, areas_of_study):
        """Decides the number of agents based on difficulty and areas of study."""
        base_agents = len(areas_of_study)

        # Adjust the number of agents based on difficulty
        if difficulty == "very easy":
            additional_agents = 0
        elif difficulty == "easy":
            additional_agents = random.randint(0, 1)
        elif difficulty == "medium":
            additional_agents = random.randint(1, 2)
        elif difficulty == "hard":
            additional_agents = random.randint(2, 3)
        else:  # very hard
            additional_agents = random.randint(3, 5)
        
        num_agents = base_agents + additional_agents
        print(f"Organizer has decided that {num_agents} agents are required for a '{difficulty}' question covering {', '.join(areas_of_study)}.")
        return num_agents

    def create_agents(self, num_agents, areas_of_study):
        """Creates agents with specific roles for the discussion based on identified areas of study."""
        # Use the identified areas for initial roles, then fill with "Generalist" if needed
        roles = areas_of_study + ["Generalist"] * (num_agents - len(areas_of_study))
        self.agents = [Agent(name=f"Agent_{i+1}", role=roles[i]) for i in range(num_agents)]

    def initialize_discussion(self, question):
        """Initializes the discussion by prompting each agent with the question and their role."""
        for agent in self.agents:
            agent.prompt(f"You are a {agent.role}. Here is the question to discuss: '{question}'")

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

    def is_satisfied_with_answer(self, summary):
        """Checks if the organizer is satisfied with the summarized answer."""
        satisfaction = random.choice([True, False])
        if satisfaction:
            print("Organizer is satisfied with the answer.")
        else:
            print("Organizer is not satisfied with the answer. Agents will discuss again.")
        return satisfaction

# Main Function
def main():
    question = input("Enter your question: ")
    organizer = OrganizerAgent()
    
    while True:
        # Determine the difficulty of the question
        difficulty = organizer.determine_difficulty(question)
        
        # Identify the areas of study for the question
        areas_of_study = organizer.identify_areas_of_study(question)
        
        # Organizer decides the number of agents required based on difficulty and areas of study
        num_agents = organizer.decide_number_of_agents(difficulty, areas_of_study)
        organizer.create_agents(num_agents, areas_of_study)
        
        # Repeat discussion until the organizer is satisfied
        satisfied = False
        while not satisfied:
            # Initialize discussion
            organizer.initialize_discussion(question)
            
            # Conduct the discussion
            responses = organizer.conduct_discussion(question)
            
            # Organizer summarizes the discussion
            final_summary = organizer.summarize_discussion(responses)
            print("\nFinal Summary from Organizer:\n", final_summary)
            
            # Check if the organizer is satisfied with the summary
            satisfied = organizer.is_satisfied_with_answer(final_summary)

        # Ask for a follow-up question or exit
        follow_up = input("Do you have a follow-up question? (Enter 'yes' to continue or 'no' to exit): ").strip().lower()
        if follow_up == 'yes':
            question = input("Enter your follow-up question: ")
        else:
            print("Ending the discussion.")
            break

if __name__ == "__main__":
    main()
