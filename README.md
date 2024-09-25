
# AI_Quiz_Generator

Originally part of an internship group endeavor, this is a continously updated project with the objective of using AI to create multiple choice questions from documents or web pages. Currently the code works with PDFs documents. In exploring the capabilities of AI, the code in this project was majority generated by GPT. 


## Authors

- [@knn8894](https://github.com/knn8894)
- 3 other unnamed contributers


## 🚀 About Me
I'm an aspiring cyber security professional. This is a place for displaying small projects I have been apart of.

## Screenshots

![App Screenshot](https://raw.githubusercontent.com/knn8894/AI_Quiz_Generator/9d7d7dee671f6521cd515f3adb5aab127aee38ac/workflow2.png)

![App Screenshot](https://github.com/knn8894/AI_Quiz_Generator/blob/main/workflow.png?raw=true)
## Run Locally

Clone the project

```bash
  git clone https://github.com/knn8894/AI_Quiz_Generator.git
```

Go to the project directory

```bash
  cd {project-directory-name}
```

Install dependencies
*(If error occurs, install other dependencies listed in error)*

```bash
  pip install google-generativeai
  pip install PyPDF2
  pip install Flask
  pip install Flask-SQLAlchemy
  pip install Flask-Login
```

Run the app.py code

```bash
  python app.py
```

#### Navigate to 'http://127.0.0.1:5000/' to view the application locally in a browser.
## API Reference

#### If not using an environment variable, don't forget to set the 'api_key' variable to your Gemini api key.


| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `api_key` | `string` | **Required**. Your API key |
