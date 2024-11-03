## Watsome Relief

Watsome Relief is a neighbor coordination website designed to assist individuals in need during natural disasters, particularly hurricanes. If there is no power or cell service, users can send SMS messages to request help or inquire about available resources nearby without the need to log in as emergency SMS can be sent through satellites with modern smartphones. Our platform infers user needs, coordinates responses, and keeps users updated on nearby supplies and neighbors in need, making it easier for communities to support one another.

## Features
- **Chabot with IBM Watsonx.ai**: Allows users to communicate the resources that they need to the chatbot. Users receive responses regarding nearby supplies, and their requests are stored in the Requests Manager. The chatbot is connected to SMS and can process requests without having internet. 
- **Resource Map**: Visually displays the locations where resources are needed and where the resources can be found. 
- **Requests Manager**: All of the resources that a user requests is shown here. The status of whether the user received or is awaiting their supplies is shown here.

## How to Start the Project

> 👉 **Step 1** - Download the code from the GH repository (using `GIT`) 

```bash
$ git clone https://github.com/app-generator/flask-material-dashboard.git
$ cd flask-material-dashboard
```

<br /> 

> 👉 **Step 2** - Start the APP in `Docker`

```bash
$ docker-compose up --build 
```

Visit `http://localhost:5085` in your browser. The app should be up & running.

<br /> 
