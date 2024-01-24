#!/usr/bin/env python3
import sys
    
sys.path.append('src/model')

from src.model.paragraph import Paragraph 

#from langchain_experimental.agents.agent_toolkits import create_csv_agent
import pandas as pd
csv_file_path = "/Users/quent1/Documents/Hexamind/ILLUMIO/Illumio3011/Chatbot_llama2_questions/src/Readers/test.csv"


class ReaderExcel:
    def __init__(self, path):
        self.path = path
        self.paragraphs = self.get_paragraphs()

    def get_paragraphs(self, max_paragraph_length=1000, rows_per_page=50):
        df = pd.read_excel(self.path)

        paragraphs = []
        paragraph_lines = []
        current_page_id = 1
        paragraph_id = 1

        for index, row in df.iterrows():
            # Concatenate text from multiple columns with column names
            row_text = ' | '.join([f"{col}: {row[col]}" for col in df.columns if pd.notnull(row[col])])

            # Accumulate paragraph lines
            paragraph_lines.append(row_text)

            # Check if the maximum paragraph length is reached or if it's the last row
            if sum(len(line) for line in paragraph_lines) >= max_paragraph_length or index == len(df) - 1:
                # Join lines to form a paragraph
                current_paragraph = ' '.join(paragraph_lines)


                # Create and append the Paragraph object
                paragraphs.append(Paragraph(current_paragraph, 'Normal', paragraph_id, current_page_id))
                paragraph_id += 1
                paragraph_lines = []  # Reset for the next paragraph

            # Increment page_id after every 'rows_per_page' rows
            if (index + 1) % rows_per_page == 0:
                current_page_id += 1

        return paragraphs
    
    
if __name__ == "__main__":
    # Example file path; replace with the path to your actual Excel file
    example_file_path = csv_file_path

    # Create an instance of ReaderExcel
    reader = ReaderExcel(example_file_path)

    # Print out the paragraphs
    for paragraph in reader.paragraphs:
        print(f"ID: {paragraph.id_}, Page: {paragraph.page_id}, Text: {paragraph.text}\n")