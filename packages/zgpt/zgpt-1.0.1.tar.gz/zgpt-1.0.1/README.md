
# zgpt 

A versatile and easy-to-use command-line AI assistant powered by the **Google Gemini API**.

##  Features

- **Simple Interface**: Get answers directly in your terminal.
- **Easy Setup**: Configure your API key with a single command.
- **Secure**: Your API key is stored locally in your user configuration directory.

##  Installation

You can now install `zgpt` directly from PyPI: _(Recommended)_

```
pip install zgpt
```

----------------OR---------------

if you want to work on the project locally, clone the repository and install in editable mode:

First, clone the repository and navigate into the directory:
```
git clone https://github.com/sachinz25/zgpt.git
cd zgpt
```

Then, install the package in editable mode. This is great for development and ensures the `zgpt` command is available system-wide.

```
pip install -e .
```

##  Setup 🔑

Before you can use `zgpt`, you need to set your Gemini API key. Run the `--init` command:

```
zgpt --init
```

You will be prompted to enter your API key. Once saved, you're ready to go!
on following page you can get Gemini api keys

**Note: [click here to get gemini api keys](https://aistudio.google.com/app/apikey)**
```
click on "ceate API key"
click "Gemini api" 
```
it will generate your api keys 

You can remove the key at any time:

```
zgpt --revoke
```

##  Usage

To ask a question, simply type `zgpt` followed by your prompt:

```
zgpt "explain what a decorator is in python with a simple example"

zgpt "give me a 5-line summary of the movie Inception"
```

## 🛠 Example

```
$ zgpt "hello there"

🤔 Thinking...
🤖

Hello there! How can I help you today?
```
