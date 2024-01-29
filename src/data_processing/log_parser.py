import pandas as pd
import re

class LogParser:
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path

    def read_and_parse_logs(self):
        logs = [self.parse_log_entry(line) for line in self._read_log_file() if self.parse_log_entry(line)]
        logs = pd.DataFrame(logs)
        logs['DateTime'] = pd.to_datetime(logs['DateTime'], format='%Y-%m-%d %H:%M:%S,%f')  # Update the format as per your data
        return pd.DataFrame(logs)

    def read_and_parse_feedback_logs(self):
        parsed_entries = [self.parse_feedback_log_entry(line.strip()) for line in self._read_log_file() if line.strip()]
        return pd.DataFrame([entry for entry in parsed_entries if entry is not None])

    def read_and_parse_history_logs(self):
        return pd.DataFrame(
            [self.parse_log_entry_history(line) for line in self._read_log_file() if self.is_valid_log_entry(self.parse_log_entry_history(line))]
        )

    def _read_log_file(self):
        with open(self.log_file_path, 'r') as file:
            return file.readlines()
        
        

    def parse_feedback_log_entry(self,log_entry):
        try:
            # General Pattern for Both Types of Feedback
            match = re.match(
                r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - INFO - (Thumb Feedback|Manual Feedback) - Feedback: (.*?)(, Collection: (.*?), Query: (.*?), Answer: (.*?), Sources: (\[.*?\]))? - Temps: (.+)',
                log_entry
            )

            if match:
                timestamp, feedback_type, feedback, _, collection, query, answer, sources, response_time = match.groups()

                # Prepare the dictionary
                entry_dict = {
                    "timestamp": pd.to_datetime(timestamp, format='%Y-%m-%d %H:%M:%S,%f'),
                    "feedback_type": feedback_type,
                    "feedback": feedback,
                    "response_time": response_time
                }

                # Add additional fields for Thumb Feedback
                if feedback_type == 'Thumb Feedback':
                    entry_dict.update({
                        "collection": collection,
                        "query": query,
                        "answer": answer,
                        "sources": sources
                    })

                return entry_dict

        except Exception as e:
            print(f"Error parsing feedback log entry: {e}")
        return None

    def parse_log_entry_history(self, log_entry):
        try:
            # Use regular expressions to extract the timestamp, level, and main message
            match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (.*)', log_entry)
            if not match:
                return None
            
            timestamp, level, message = match.groups()

            # Extract collection name
            collection_match = re.search(r'Collection: (.*?)(?=, Query:)', message)
            collection = collection_match.group(1).strip() if collection_match else None

            # Extract query
            query_match = re.search(r'Query: (.*?)(?=, Answer:)', message)
            query = query_match.group(1).strip() if query_match else None

            # Extract answer
            answer_match = re.search(r'Answer: (.*?)(?=,  Sources:)', message)
            answer = answer_match.group(1).strip() if answer_match else None

            # Extract sources
            # Find the entire 'Sources' to 'Temps' section
            sources_section_match = re.search(r'Sources: (.*) - Time:', log_entry, re.DOTALL)
            sources_section = sources_section_match.group(1).strip() if sources_section_match else None
            
            # Clean up the 'Sources' section to extract the list
            sources = None
            if sources_section:
                # Assume the sources are enclosed in brackets '[]'
                sources_match = re.search(r'\[(.*)\]', sources_section, re.DOTALL)
                if sources_match:
                    # Extract the content inside the brackets and split by ', ' to get a list of sources
                    sources = sources_match.group(1).split("', '")
            
            # Extract time
            time_match = re.search(r'Temps: (.*)', log_entry)
            time = time_match.group(1).strip() if time_match else None

            # Construct and return the result dictionary
            return {
                "timestamp": timestamp,
                "level": level,
                "collection": collection,
                "query": query,
                "answer": answer,
                "sources": sources,  # Return the cleaned list of sources
                "Time": time
            }
        except Exception as e:
            # Print error message for debugging
            print("Error parsing log:", e)
            # Return None if parsing fails
            return None
        
        
    def parse_log_entry(self,entry):
        # Original log format pattern
        original_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (\w+) - Collection: ([\w\s_]+) , Query: .* - Time: ([0-9.]+)'
        match = re.search(original_pattern, entry)

        if match:
            return {
                'DateTime': match.group(1),
                'LogLevel': match.group(2),
                'Activity': match.group(3),
                'Collection': match.group(4).strip(),
                'Time': float(match.group(5))
            }
        
        # Fail log without a collection
        fail_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (\w+) - .+ - Time: ([0-9.]+)'
        match = re.search(fail_pattern, entry)

        if match:
            return {
                'DateTime': match.group(1),
                'LogLevel': match.group(2),
                'Activity': match.group(3),
                'Collection': 'N/A',
                'Time': float(match.group(4))
            }

        feedback_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (\w+ Feedback) - (Feedback: )?(.*) - Time: ([0-9.]+)'
        match = re.search(feedback_pattern, entry)
        if match:
            return {
                'DateTime': match.group(1),
                'LogLevel': match.group(2),
                'Activity': match.group(3),
                'Collection': 'N/A',  # Or you might want to add feedback text here instead
                'Time': float(match.group(6))  # Use group 6 for the time value
            }   
        return None  # If no pattern matches, return None

    @staticmethod
    def is_valid_log_entry(log_entry):
        if log_entry is None:
            return False
        return log_entry.get('query', None) not in [None, ''] and log_entry.get('answer', None) not in [None, '']
