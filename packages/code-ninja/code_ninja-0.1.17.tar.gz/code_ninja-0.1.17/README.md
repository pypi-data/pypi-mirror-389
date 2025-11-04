# ErrorHandler-AI

Python error handler library with UV and Rich, provides AI-powered suggestions for fixing errors in user code. Uses OpenAI for error cause analysis and solution output. Styled suggestions are shown in the terminal using Rich.

---

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Decorator Usage](#decorator-usage)


---

## Overview

ErrorHandler-AI provides a decorator that lets you catch and explain Python errors in your functions automatically. If an error occurs, the library uses OpenAI to analyze the cause and suggest a fix and Correct code. Output is neatly formatted in your terminal using Rich panels for easy readability.

**Main features:**

- Catches Python errors in user code (decorator-based)
- AI-powered error cause and fix suggestions
- Rich terminal output with styled panels
- Customizable with environment variables

---

## Installation

Install via pip:

```
pip install code-ninja==0.1.14
```

Set your OpenAI API key and other environment variables in a `.env` file:
```
API_KEY=your-api-key
BASE_URL=your-openai-base-url # optional
INSTRUCTION=Explain the error in more detail with examples. # optional
```


---

## Quickstart

Add the decorator to your function:

```
from errorhandler_ai import catch

@catch
def divide(x, y):
return x / y

divide(10, 0) # Triggers error handler
```



When an error is raised, you'll see:

- Error type and info (bold red panel)
- AI-analyzed cause (red panel)
- AI fix suggestion (green panel)

---

## Decorator Usage

Use the `@catch` decorator to wrap any function you want to monitor for errors:

