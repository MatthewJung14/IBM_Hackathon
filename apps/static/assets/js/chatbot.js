// static/assets/js/chatbot.js

// Initialize interact.js for draggable functionality
interact('.msger')
  .draggable({
    // Enable inertial throwing
    inertia: true,
    // Keep the element within the window bounds
    modifiers: [
      interact.modifiers.restrictRect({
        restriction: 'window',
        endOnly: true
      })
    ],
    // Enable autoScroll
    autoScroll: true,

    listeners: {
      // Call this function on every dragmove event
      move: dragMoveListener,
    }
  });

function dragMoveListener(event) {
  var target = event.target;
  // Keep the dragged position in the data-x/data-y attributes
  var x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
  var y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;

  // Translate the element
  target.style.transform = 'translate(' + x + 'px, ' + y + 'px)';

  // Update the position attributes
  target.setAttribute('data-x', x);
  target.setAttribute('data-y', y);
}

// Make dragMoveListener available globally
window.dragMoveListener = dragMoveListener;

// Chatbot functionality with Integration to Flask API
document.addEventListener("DOMContentLoaded", () => {
  const msgerForm = document.querySelector(".msger-inputarea");
  const msgerInput = document.querySelector(".msger-input");
  const msgerChat = document.querySelector(".msger-chat");

  const BOT_NAME = "Assistant";
  const PERSON_NAME = "You";

  // Retrieve user data from the hidden div
  const userDataDiv = document.getElementById('user-data');
  const userId = userDataDiv.getAttribute('data-user-id');
  const profilePicture = userDataDiv.getAttribute('data-profile-picture');
  const givenName = userDataDiv.getAttribute('data-given-name');
  const familyName = userDataDiv.getAttribute('data-family-name');
  const userEmail = userDataDiv.getAttribute('data-user-email');

  // Define Bot and User Images
  const BOT_IMG = "/static/assets/images/bot.png"; // Replace with your bot image path
  const PERSON_IMG = profilePicture || "/static/assets/images/user.png"; // User's profile picture or default

  msgerForm.addEventListener("submit", event => {
    event.preventDefault();
    const msgText = msgerInput.value.trim();
    if (!msgText) return;

    appendMessage(PERSON_NAME, PERSON_IMG, "right", msgText);
    msgerInput.value = "";
    hideTypewriter(); // Hide typewriter message when user sends a message
    sendMessageToAPI(msgText);
  });

  function appendMessage(name, img, side, text) {
    const msgClass = side === "left" ? "left-msg" : "right-msg";
    const msgHTML = `
      <div class="msg ${msgClass}">
        <div class="msg-img" style="background-image: url(${img});"></div>
        <div class="msg-bubble">
          <div class="msg-info">
            <div class="msg-info-name">${name}</div>
            <div class="msg-info-time">${formatDate(new Date())}</div>
          </div>
          <div class="msg-text">${text}</div>
        </div>
      </div>
    `;
    msgerChat.insertAdjacentHTML("beforeend", msgHTML);
    msgerChat.scrollTop = msgerChat.scrollHeight;
  }

  function sendMessageToAPI(message) {
    // Show a loading indicator
    const loadingMessage = "Assistant is typing...";
    appendMessage(BOT_NAME, BOT_IMG, "left", loadingMessage);

    fetch('/chat/message', { // Adjust the endpoint as needed
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: userId,
        message: message,
        // Optionally, include coordinates if available
        // x: latitude,
        // y: longitude
      })
    })
    .then(response => response.json())
    .then(data => {
      // Remove the loading indicator
      removeLastMessage();

      // Handle different response structures
      if (data.results && Array.isArray(data.results)) {
        data.results.forEach(result => {
          appendMessage(BOT_NAME, BOT_IMG, "left", result.text);
        });
      } else if (data.message) {
        appendMessage(BOT_NAME, BOT_IMG, "left", data.message);
      } else {
        appendMessage(BOT_NAME, BOT_IMG, "left", "I'm not sure how to respond to that.");
      }
    })
    .catch(error => {
      console.error('Error:', error);
      // Remove the loading indicator
      removeLastMessage();
      appendMessage(BOT_NAME, BOT_IMG, "left", "Sorry, something went wrong. Please try again later.");
    });
  }

  function removeLastMessage() {
    const messages = msgerChat.querySelectorAll('.msg');
    if (messages.length > 0) {
      msgerChat.removeChild(messages[messages.length - 1]);
    }
  }

  function formatDate(date) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  // Typewriter Effect for Welcome Message
  const welcomeMessage = "What can I help you with?";
  const typewriterElement = document.createElement('div');
  typewriterElement.classList.add('typewriter');
  msgerChat.appendChild(typewriterElement);

  function typeWriter(text, element, delay = 100) {
    let i = 0;
    function type() {
      if (i < text.length) {
        element.textContent += text.charAt(i);
        i++;
        setTimeout(type, delay);
      }
    }
    type();
  }

  // Initialize the typewriter effect after a short delay
  setTimeout(() => {
    typeWriter(welcomeMessage, typewriterElement);
  }, 500);

  function hideTypewriter() {
    if (typewriterElement) {
      typewriterElement.style.display = 'none';
    }
  }

  // Hide typewriter when user starts typing
  msgerInput.addEventListener('focus', () => {
    hideTypewriter();
  });

  msgerInput.addEventListener('input', () => {
    hideTypewriter();
  });

  // Handle File Upload
  const fileUploadBtn = document.getElementById('file-upload-btn');
  const fileInput = document.getElementById('file-input');

  fileUploadBtn.addEventListener('click', () => {
    fileInput.click();
  });

  fileInput.addEventListener('change', () => {
    const file = fileInput.files[0];
    if (file) {
      appendMessage(PERSON_NAME, PERSON_IMG, "right", `📎 ${file.name}`);
      // Optionally, upload the file to the server
      uploadFile(file);
    }
  });

  function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId);

    fetch('/upload', { // Define this endpoint in Flask
      method: 'POST',
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      if (data.message) {
        appendMessage(BOT_NAME, BOT_IMG, "left", data.message);
      } else {
        appendMessage(BOT_NAME, BOT_IMG, "left", "File uploaded successfully.");
      }
    })
    .catch(error => {
      console.error('Error uploading file:', error);
      appendMessage(BOT_NAME, BOT_IMG, "left", "Sorry, failed to upload the file.");
    });
  }
});
