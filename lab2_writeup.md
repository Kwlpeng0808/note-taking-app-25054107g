# Lab2 Writing up

A Report that contain the major steps for completing the tasks and some challenges in the tasks.

## 🚀 Main steps
The major steps for completing the tasks:

### Step1: Refactoring, New features implementing and Testing

#### Added tags and datetime functionality, allowing users to fill in tags and scheduled date/time when creating notes.
![alt text](screenshots/tags%20and%20time1.png)
![alt text](screenshots/tags%20and%20time2.png)
![alt text](screenshots/tags%20and%20time3.png)

#### Implemented a note translation feature that supports 5 major languages, enabling users to switch freely as needed.
![alt text](screenshots/translation1.png)
![alt text](screenshots/translation3.png)
![alt text](screenshots/translation4.png)
![alt text](screenshots/translation5.png)

#### Implemented an AI-powered note generation feature, which parses user-input ideas into note titles, content, corresponding tags, and dates.
![alt text](screenshots/ai%20generation1.png)
![alt text](screenshots/ai%20generation2.png)
![alt text](screenshots/ai%20generation3.png)

#### Refined the user interface and input controls to enhance the user experience.
![alt text](screenshots/improvement1.png)
![alt text](screenshots/improvement2.png)

#### Conducted testing and resolved bugs.
Solving "MaxClientsInSessionMode: max clients reached" when the remote pooler limits clients.
![alt text](screenshots/bugfix1.png)

UI Styling Improvements
![alt text](screenshots/bugfix2.png)

### Step2: Setting up of supabase

#### Determined the Supabase connection method.
![alt text](screenshots/Supabase3.png)

#### Set database connection parameters in environment variables.
![alt text](screenshots/Supabase2.png)

#### Updated the code to initialize and configure the database connection.
![alt text](screenshots/Supabase1.png)

### Step3: Vercel deployment and handling the API keys, environment variables

#### Vercel Entry Point and Routing Configuration
Vercel uses index.py as the build/entry point. This file exports the Flask application to Vercel.
The build and routing rules for Vercel are defined in vercel.json, where all requests are routed to api/index.py.
![alt text](screenshots/Vercel1.png)

#### Flask App / WSGI Callable
The Flask application is defined in src.main.app. The index.py file exposes it to Vercel via the statement from src.main import app.
![alt text](screenshots/Vercel2.png)

#### Static Frontend Hosting
The Flask app is configured with static_folder set to src/static. Routes in main.py return index.html if no matching static file is found. Consequently, the frontend static pages are served by Vercel alongside the API.
![alt text](screenshots/Vercel3.png)

#### Database and Runtime Environment Variables
main.py contains logic to detect the Vercel environment and the SUPABASE_DATABASE_URL:
If running on Vercel, it mandates SUPABASE_DATABASE_URL and uses it for SQLALCHEMY_DATABASE_URI.
To ensure secure database usage in the serverless environment, SQLALCHEMY_ENGINE_OPTIONS (e.g., connection pool size, overflow, timeout, pre-ping) are also controlled via environment variables within main.py.
![alt text](screenshots/Vercel4.png)

#### Dependency Installation
During the build process, Vercel automatically installs packages listed in requirements.txt (e.g., psycopg2-binary, Flask, openai).
![alt text](screenshots/Vercel5.png)

#### LLM Features and Token Management
LLM interactions are encapsulated in llm.py, which reads the GITHUB_TOKEN.
If the token is not configured, both the frontend and backend will return a service unavailable error.
![alt text](screenshots/Vercel6.png)

#### API Route Registration and Frontend Interaction
All API blueprints are registered under the /api prefix during application startup. The route implementations are located in note.py and user.py (see src.routes.note and src.routes.user).
![alt text](screenshots/Vercel7-1.png)
![alt text](screenshots/Vercel7-2.png)

#### Final Deployment Steps on Vercel
Connect the GitHub repository to Vercel. (Note: The repository must be set to public for free deployment on Vercel).
![alt text](screenshots/Vercel8-1.png)

Configure the required environment variables in the Vercel project settings. Sensitive keys (e.g., personal API keys) must be marked as secret to prevent exposure.
![alt text](screenshots/Vercel8-2.png)

Initiate the deployment. Monitor the build and runtime logs in the Vercel dashboard to ensure the process completes without errors.
![alt text](screenshots/Vercel8-3.png)

## 🌟 Challenges and Insights

### LLM model response problems
When utilizing a large language model (LLM) to power the translation and AI-based note generation features, the LLM server sometimes takes a considerable amount of time to return a response. This leads to a suboptimal user experience. However, this is fundamentally an issue with the external service (e.g., poor network conditions) and is beyond the control of my project's code.

Consequently, I considered how to optimize the feature logic to mitigate this poor experience:

First, I implemented a three-retry mechanism: In [src/llm.py::translate_text], I added 3 retries with exponential backoff. This appropriately increases the number of system retry attempts, improving the chances of a successful request. Additionally, logging was incorporated to promptly print tracebacks when exceptions occur, facilitating future maintenance and debugging. Finally, even if the operation ultimately fails, it returns None to prevent blocking the note creation process.

Furthermore, I modified the translation request to be handled as an asynchronous background task (translation_worker). This avoids blocking user requests and allows for more robust handling of retries and persisting failed records. However, due to Vercel's serverless nature, this translation_worker does not start on Vercel (enabling it on Vercel would require deploying an external worker or using a cloud task/queue service, which is planned for future optimization).

The frontend status display was also optimized to show the translation status, helping users understand the current state and reducing confusion.







