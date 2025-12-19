# 👋 Demo Frontend

A simple app that renders a frontend experience with no Temporal worker(s) involved.

## Features

- The OOTB FastAPI integration is already equipped to render frontend apps anchored off **frontend/templates/index.html**, with static files served off **frontend/static**. This app leverages that default configuration.

- While the app uses the BaseApplication abstraction, it provides a no-frills APIServer instance to avoid having to define Workflows and Activities.

## Features

- Create a frontend app as per your requirements using any modern JavaScript framework (React, Vue, Angular, etc.). Source code for a sample React app, **data-sla-monitor-default**, has been provided as a reference.

- Build your app and drop the compiled code into **frontend/static** within the project.

- Install the App Framework essentials.

```bash
uv sync --all-extras --all-groups
```

- Run the app.

```bash
uv run main.py
```

- The app should render on **localhost:8000**.
