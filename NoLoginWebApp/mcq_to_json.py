import google.generativeai as genai  # Gemini API
import csv  # Handle CSV file creation and saving
from PyPDF2 import PdfReader  # Reads and parses the PDF file
import os

# Configure the Gemini API
genai.configure(api_key=os.environ["API_KEY"])

# Configure the Gemini API
#genai.configure(api_key="ENTER_API_KEY")    #---Enter API Key Here---#

model = genai.GenerativeModel('gemini-1.5-flash')

def extract_text_from_pdf(pdf_path, page_start=0, page_end=None):
    """Extract text from a PDF file."""
    with open(pdf_path, 'rb') as f:
        pdf = PdfReader(f)
        text = ""
        if page_end is None:
            page_end = len(pdf.pages)
        for page_num in range(page_start, page_end):
            page = pdf.pages[page_num]
            text += page.extract_text()
    return text

def generate_questions(extracted_text):
    """Generate questions using the Gemini API."""
    response = model.generate_content(f'''Create 5 questions with 3 incorrect and 1 correct multiple choice answers
                based on the information found in the text. List the answer choices (a,b,c,d), then list
                the correct answer. Don't leave any spaces between new lines. The first line should be the question,
                the second through fifth lines should be answer choices, and the sixth line should show the correct
                answer and the reason why it is correct, in the format of "The correct answer is" followed by the correct letter and
                the reason why it is correct, all on one line:\n{extracted_text}''')
    print(response.text)
    return response.text

def save_questions_to_csv(question_text, csv_path='questions.csv'):
    """Save the generated questions to a CSV file."""
    def parse_question_block(block):
        """Parse a block of text into question and answers including explanation."""
        lines = block.strip().split('\n')
        
        if len(lines) < 6:
            raise ValueError(f"Invalid question block: {block}")

        question = lines[0].strip()
        choices = [line.strip() for line in lines[1:5]]
        answer_line = lines[5].strip()
        
        # Extract correct answer and explanation
        if "The correct answer is " in answer_line:
            correct_answer_part = answer_line.split("The correct answer is ")[1].strip()
            correct_answer_letter = correct_answer_part.split(" ")[0].strip()
            
            # Extract the explanation
            explanation = " ".join(correct_answer_part.split(" ")[1:]).strip() if " " in correct_answer_part else ""
            
            # Get the correct answer choice text
            correct_answer_text = next((choice for choice in choices if choice.startswith(correct_answer_letter)), "")
            
            # Ensure the explanation is included correctly
            correct_answer = f"{correct_answer_text} - {explanation}"
        else:
            raise ValueError(f"Answer line format is incorrect: {answer_line}")

        return [question] + choices + [correct_answer, "Placeholder"]  # Include explanation in correct answer



    blocks = question_text.strip().split("\n\n")
    questions_data = []
    for block in blocks:
        if block.strip():
            try:
                questions_data.append(parse_question_block(block))
            except ValueError as e:
                print(f"Error parsing block: {e}")
    
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            ["Question", "Answer A", "Answer B", "Answer C", "Answer D", "Correct Answer", "Arbitrary Value"])
        writer.writerows(questions_data)


# Optional: main function to run everything in one go
def run_quiz_generator(pdf_path, csv_path='questions.csv'):
    extracted_text = extract_text_from_pdf(pdf_path)
    questions_text = generate_questions(extracted_text)
    save_questions_to_csv(questions_text, csv_path)

    
'''
# Example usage:
if __name__ == "__main__":
    # Specify the path to your test PDF
    test_pdf_path = 'path/to/file'
    # Specify the path where the CSV file will be saved
    test_csv_path = 'path/to/folder/questions.csv'     #Enter path of where 'questions.csv' will be saved

    # Run the quiz generator
    run_quiz_generator(test_pdf_path, test_csv_path)
'''    
