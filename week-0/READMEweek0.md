# CLI Gemini Chatbot (LangChain)

A tiny, friendly command-line chatbot that uses **LangChain** to call **Google Gemini**.

> **What it does (in plain words):**
> 1. Reads your **GEMINI_API_KEY** from a `.env` file.
> 2. Builds a **Gemini chat model** using `langchain_google_genai.ChatGoogleGenerativeAI`.
> 3. Sends whatever you type as a **HumanMessage**.
> 4. Prints the model’s reply to your terminal.
>
> That’s it—small, focused, and easy to extend.

---

## Quickstart

### 1) Requirements
- Python 3.10+ recommended
- A Google Generative AI API key (put this in your `.env` file)

### 2) Install
```bash
# (Optional) create and activate a virtual environment
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -U pip
pip install python-dotenv langchain-core langchain-google-genai
```

> If you run into issues, also try:
>
> ```bash
> pip install langchain  # some setups prefer this umbrella package
> ```

### 3) Configure your `.env`
Create a file named `.env` in the project root (same folder as `app.py`) and add:

```
GEMINI_API_KEY=your_real_api_key_here
```

You can copy from `.env.example` and fill in your key.

### 4) Run
```bash
python app.py
```
Type a question or instruction, press **Enter**, and you’ll see Gemini’s response.
Type `exit` to quit.

---

## How it works (machine-brain mental model)

Here’s the exact sequence the code follows when you run `python app.py`:

1. **Load configuration**  
   `load_dotenv()` reads the `.env` file and populates `os.environ`.  
   The goal: make sure `os.environ["GEMINI_API_KEY"]` exists.

2. **Build the model (once)**  
   `build_model()` creates `ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=...)`.  
   We cache it with `@lru_cache` so we don’t rebuild the client for every turn.

3. **Read user input (loop)**  
   The CLI prints a prompt (`Enter query:`) and waits for your text.

4. **Wrap input as a chat message**  
   LangChain chat models expect a list of messages. We create `HumanMessage(content=your_text)`.

5. **Call the model**  
   `model.invoke([HumanMessage(...)])` sends the message to Gemini’s API and waits for a reply.

6. **Show the reply**  
   The object returned by LangChain has a `.content` string. We print it as the chatbot’s answer.

7. **Repeat**  
   The loop continues until you type `exit` (or press Ctrl+C / Ctrl+D).

**Error paths (defensive thinking):**  
- If `.env` is missing or the key isn’t set → we raise a clear message.  
- If the API rejects the request (quota, invalid key, network) → we catch the exception and print a readable `[error]` line.

---

## File structure

```
.
├── app.py            # The CLI program
├── .env.example      # Template for your secrets
└── README.md         # You’re reading this
```

---

## Common issues & quick fixes

- **`ModuleNotFoundError: ...`**  
  You’re missing a dependency. Re-run the `pip install ...` commands in **Install**.

- **`GEMINI_API_KEY is missing`**  
  Create the `.env` file and paste your key. Make sure there are no quotes around it.

- **`Permission` or `SSL` errors**  
  Try updating `pip` (`pip install -U pip`) or using a fresh virtual environment.

- **Model name errors**  
  If `gemini-2.5-flash` isn’t available in your region/account, try a different available Gemini model.

---

## Extend it

- **Add a system prompt** (persona/instructions): use `langchain_core.messages.SystemMessage` before `HumanMessage`.
- **Stream tokens**: try `model.stream([...])` to print partial tokens as they arrive.
- **Multi-turn context**: keep a list of prior messages and append to it before each `invoke()`.

---

## GitHub: how to push this repo

1. Create a new empty repo on GitHub (e.g. `gemini-cli-langchain`). Copy its URL.
2. In your terminal (inside this project folder):

```bash
git init
git branch -M main
echo ".env" >> .gitignore
echo ".venv/" >> .gitignore
echo "__pycache__/" >> .gitignore
echo ".DS_Store" >> .gitignore
git add .
git commit -m "Add CLI Gemini chatbot (LangChain)"
git remote add origin https://github.com/YOUR_USERNAME/gemini-cli-langchain.git
git push -u origin main
```

> Replace the remote URL with your actual repo URL.  
> If you see an authentication prompt, sign in with your GitHub token/password.

---

## License

MIT (or your preferred license).
